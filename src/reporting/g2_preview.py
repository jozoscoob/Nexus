"""G2 Preview 화면 생성기 — 대두유 CBOT 정산가의 지평별 참고 범위·과거 성적표·해상 경로·인과 지도를 한 장의 HTML로.

데이터 원천(전부 로컬 파이프라인 산출물):
  - data/raw/cbot_session_close.parquet          목표 계열 CBOT_BO_CLOSE(정산가, USc/lb)
  - data/processed/g2_band_backtest_latest.json  기준선 워크포워드·lockbox 성적표(band_backtest)
  - data/raw/te_commodities_historical.parquet   관련 시장 시세(팜유·대두·유채·해바라기유·원유·BDI)
  - data/raw/economic_indicators_*.parquet       환율(BRL·KRW)
  - data/processed/route_scenarios_latest.json   해상 경로 시나리오(src/logistics/route_scenarios.py)
  - src/semantic/ontology.yaml                   인과 엣지(인과 지도)
범위 산출 = 기준선 B2(최근 250개 h-거래일 로그수익률의 경험 분위를 최신 정산가에 적용). Champion(Quantile LightGBM+CQR)
전 단계이므로 화면 문구는 '참고 범위·과거 표본 성적표'로 고정한다 — 상승확률·임계 초과확률은 표시하지 않는다(A-191).
출력: reports/g2_preview/g2_preview_latest.html (가격 데이터를 포함하므로 저장소에 커밋하지 않음 — .gitignore).
"""
from __future__ import annotations

import glob
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
TEMPLATE = Path(__file__).with_name("templates") / "g2_preview.html"
OUT = ROOT / "reports" / "g2_preview" / "g2_preview_latest.html"
HORIZONS = {1: "1일", 5: "1주", 20: "1개월", 60: "3개월"}
QUANTS = [0.10, 0.25, 0.50, 0.75, 0.90]
ROLL = 250                      # band_backtest B2와 동일한 경험 분위 창
HISTORY_DAYS = 1300             # 화면 차트 표시 이력(약 5년)
USC_LB_TO_USD_MT = 22.0462      # 1 USc/lb = 22.0462 USD/MT (정확 환산)
TICKERS = [("TE_PALM_OIL", "팜유 (Bursa)"), ("TE_SOYBEANS", "대두 (CBOT)"),
           ("TE_RAPESEED", "유채 (Euronext)"), ("TE_SUNFLOWER_OIL", "해바라기유"),
           ("TE_BRENT_CRUDE_OIL", "브렌트유"), ("TE_BDI", "BDI 운임"),
           ("DEXBZUS", "헤알/달러"), ("DEXKOUS", "원/달러")]


def _close() -> pd.Series:
    d = pd.read_parquet(RAW / "cbot_session_close.parquet", columns=["price_date", "indicator_code", "value"])
    s = d[d["indicator_code"] == "CBOT_BO_CLOSE"].set_index("price_date")["value"].sort_index()
    if s.empty:
        raise SystemExit("[오류] CBOT_BO_CLOSE 없음 — validate_session_close.py(마트 작업)를 먼저 실행하세요")
    return s.astype(float)


def bands(close: pd.Series) -> dict:
    last = float(close.iloc[-1])
    lp = np.log(close.to_numpy())
    out = {}
    for h, label in HORIZONS.items():
        r = lp[h:] - lp[:-h]
        win = r[-ROLL:]
        qs = np.quantile(win, QUANTS)
        out[str(h)] = {"label": label, "n": int(len(win)),
                       "q": {f"p{int(q * 100)}": round(last * math.exp(v), 2) for q, v in zip(QUANTS, qs)}}
    return out


def report_card() -> dict:
    p = PROC / "g2_band_backtest_latest.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    card = {"window": d.get("window"), "lockbox": d.get("lockbox"), "horizons": {}}
    for h, models in d.get("horizons", {}).items():
        rows = []
        for name, m in models.items():
            wf, lb = m.get("walk_forward", {}), m.get("lockbox", {})
            rows.append({"model": name, "cov80": wf.get("coverage_80"), "cov50": wf.get("coverage_50"),
                         "width80": wf.get("width_80_pct"), "mae": wf.get("mae_p50_pct"),
                         "lock_cov80": lb.get("coverage_80"), "lock_width80": lb.get("width_80_pct"),
                         "n": wf.get("n")})
        card["horizons"][h] = rows
    return card


def _series_last(df: pd.DataFrame, code: str) -> dict | None:
    s = df[df["indicator_code"] == code].drop_duplicates("price_date", keep="last") \
        .set_index("price_date")["value"].sort_index().dropna()
    if len(s) < 2:
        return None
    spark = s.iloc[-60:]
    return {"last": round(float(s.iloc[-1]), 2), "date": s.index[-1].strftime("%Y-%m-%d"),
            "chg": round((float(s.iloc[-1]) / float(s.iloc[-2]) - 1) * 100, 2),
            "spark": [round(float(v), 3) for v in spark]}


def tickers() -> list[dict]:
    frames = []
    te = RAW / "te_commodities_historical.parquet"
    if te.exists():
        frames.append(pd.read_parquet(te, columns=["price_date", "indicator_code", "value", "unit"]))
    eco = sorted(glob.glob(str(RAW / "economic_indicators_*.parquet")))
    if eco:
        frames.append(pd.read_parquet(eco[-1], columns=["price_date", "indicator_code", "value"]))
    if not frames:
        return []
    df = pd.concat(frames, ignore_index=True)
    out = []
    for code, name in TICKERS:
        v = _series_last(df, code)
        if v:
            unit = df.loc[df["indicator_code"] == code, "unit"].dropna()
            out.append({"code": code, "name": name, "unit": unit.iloc[0] if len(unit) else "", **v})
    return out


def causal_graph(disrupted: set[str]) -> dict:
    onto = yaml.safe_load((ROOT / "src" / "semantic" / "ontology.yaml").read_text(encoding="utf-8"))
    hot_words = {"HORMUZ": ["HORMUZ", "STRAIT"], "BAB_EL_MANDEB": ["RED_SEA", "SUEZ", "HOUTHI"],
                 "SUEZ": ["SUEZ"], "PANAMA": ["PANAMA"], "MALACCA": ["MALACCA"]}
    hot_terms = {w for k in disrupted for w in hot_words.get(k, [])}
    nodes: dict[str, dict] = {}
    links = []
    for e in onto.get("causal_edges", []):
        chain = [e["cause"]["node"]] + [m["node"] for m in e.get("mechanisms", [])] + [e["outcome"]["node"]]
        labels = [x.strip() for x in str(e.get("label_ko", "")).split("→")]
        if len(labels) != len(chain):
            labels = chain
        hot = any(t in n for n in chain for t in hot_terms)
        for i, n in enumerate(chain):
            node = nodes.setdefault(n, {"id": n, "label": labels[i][:28], "cat": e.get("category", ""),
                                        "deg": 0, "outcome": n in ("SBO_INTL_PRICE", "KR_IMPORT_CIF"),
                                        "hot": False})
            node["deg"] += 1
            node["hot"] = node["hot"] or hot
        for a, b in zip(chain, chain[1:]):
            links.append({"s": a, "t": b, "edge": e["edge_id"], "status": e.get("status"),
                          "dir": e.get("direction"), "hot": hot})
    edges = [{"id": e["edge_id"], "label": e.get("label_ko", ""), "status": e.get("status"),
              "cat": e.get("category", ""), "dir": e.get("direction")} for e in onto.get("causal_edges", [])]
    return {"nodes": list(nodes.values()), "links": links, "edges": edges}


def build() -> dict:
    close = _close()
    hist = close.iloc[-HISTORY_DAYS:]
    routes_p = PROC / "route_scenarios_latest.json"
    routes = json.loads(routes_p.read_text(encoding="utf-8")) if routes_p.exists() else {}
    disrupted = {k for k, s in routes.get("status", {}).items() if s.get("state") == "disrupted"}
    return {
        "meta": {"as_of": close.index[-1].strftime("%Y-%m-%d"),
                 "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                 "unit": "USc/lb", "to_usd_mt": USC_LB_TO_USD_MT, "roll": ROLL,
                 "method": "기준선 B2 — 최근 250개 h-거래일 수익률의 경험 분위를 최신 정산가에 적용"},
        "price": [[d.strftime("%Y-%m-%d"), round(float(v), 2)] for d, v in hist.items()],
        "bands": bands(close),
        "card": report_card(),
        "tickers": tickers(),
        "routes": routes,
        "graph": causal_graph(disrupted),
    }


def render(data: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    if "/*__G2_DATA__*/null" not in tpl:
        raise RuntimeError("[오류] 템플릿 데이터 자리표시자(/*__G2_DATA__*/null) 없음")
    return tpl.replace("/*__G2_DATA__*/null", payload)


def run() -> Path:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(data), encoding="utf-8")
    b = data["bands"]["60"]["q"]
    print(f"[완료] G2 Preview → {OUT} · 기준일 {data['meta']['as_of']} · 3개월 참고 범위 "
          f"{b['p10']}~{b['p90']} USc/lb · 시세 {len(data['tickers'])}종 · 인과 엣지 {len(data['graph']['edges'])}")
    return OUT


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
