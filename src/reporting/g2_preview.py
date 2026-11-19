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
ROLL = 250                      # 케인스 렌즈의 경험 분위 창(참고 렌즈 전용)
# 참고 범위 B4a′(2026-11-19 패널 재검토 후 승인 적용): 중심 = 현재가(무드리프트), 폭 = EWMA 일변동성 × √h × 정규 분위.
# 지평별 감쇠: 1·5일 0.94, 20·60일 0.97 — 60일 80% coverage 76.8%·pinball 최저·폭 일변동 안정(근거:
# docs/research_desk/2026-11/g2_b4_panel_review_2026_11_19.md). 컨포멀 배수는 60일 독립 표본이 적어 범위에 곱하지 않음.
EWMA_LAMBDA = {1: 0.94, 5: 0.94, 20: 0.97, 60: 0.97}
Z = {0.10: -1.2816, 0.25: -0.6745, 0.50: 0.0, 0.75: 0.6745, 0.90: 1.2816}
EVAL_START = "2012-01-01"        # 범위 적중 이력 산출 시작(walk-forward, 결과가 실현된 구간만)
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


def _ewma_sigma(lp: np.ndarray, lam: float) -> np.ndarray:
    """t일 종가까지의 일간 로그수익률로 만든 EWMA 일변동성(t 이후 정보 없음)."""
    r = np.diff(lp)
    s2 = np.empty(len(lp))
    s2[0] = 0.015 ** 2                    # 미래 수익률 없이 고정 사전값(연율 약 24%) — 평가 시작 전 소멸
    for t in range(1, len(lp)):
        s2[t] = lam * s2[t - 1] + (1 - lam) * r[t - 1] ** 2
    return np.sqrt(s2)


def bands(close: pd.Series, with_stats: bool = True) -> dict:
    """참고 범위 B4a′ + 지평별 과거 적중 이력(같은 방식을 매일 적용했을 때 실제가 범위 안·위·아래에 든 비율)."""
    last = float(close.iloc[-1])
    lp = np.log(close.to_numpy())
    out = {}
    for h, label in HORIZONS.items():
        sig = _ewma_sigma(lp, EWMA_LAMBDA[h])
        sd = float(sig[-1]) * math.sqrt(h)
        item = {"label": label, "n": int(len(lp)), "lambda": EWMA_LAMBDA[h],
                "q": {f"p{int(q * 100)}": round(last * math.exp(Z[q] * sd), 2) for q in QUANTS}}
        if with_stats:
            start = int(np.searchsorted(close.index.values, np.datetime64(EVAL_START)))
            t = np.arange(start, len(lp) - h)
            zs = (lp[t + h] - lp[t]) / (sig[t] * math.sqrt(h))
            item["stats"] = {"n": int(len(t)), "since": EVAL_START,
                             "cov80": round(float(np.mean(np.abs(zs) <= Z[0.90])) * 100, 1),
                             "cov50": round(float(np.mean(np.abs(zs) <= Z[0.75])) * 100, 1),
                             "above90": round(float(np.mean(zs > Z[0.90])) * 100, 1),
                             "below10": round(float(np.mean(zs < Z[0.10])) * 100, 1)}
        out[str(h)] = item
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


# ── 관점(렌즈) 참고값 — G2 범위 숫자는 바꾸지 않는다. 휴리스틱이며 백테스트 전(화면에 그대로 표기) ──────────
PARITY_WINDOW = 756            # 약 3년 — 상대가격(스프레드) 분포 창
BUSHEL_OIL_LB, BUSHEL_MEAL_ST = 0.11, 0.022   # 대두 1부셸 → 유지 11lb(USc/lb×0.11=$/bu), 대두박 0.022 short ton
LB_PER_GAL = 7.5                                 # 대두유 1갤런 ≈ 7.5lb (BOHO 환산)
SOY_EXPORT_CR4 = 45                              # 대두 수출 상위 4사 점유율 %(Wilson AEPP 2025, 선박 실거래)


def _mkt(code: str) -> pd.Series:
    if code.startswith("TE_"):
        df = pd.read_parquet(RAW / "te_commodities_historical.parquet", columns=["price_date", "indicator_code", "value"])
    else:
        f = sorted(glob.glob(str(RAW / "economic_indicators_*.parquet")))
        if not f:
            return pd.Series(dtype=float)
        df = pd.read_parquet(f[-1], columns=["price_date", "indicator_code", "value"])
    s = df[df["indicator_code"] == code].drop_duplicates("price_date", keep="last").set_index("price_date")["value"]
    return s.sort_index().astype(float)


def _front_month(sym: str) -> pd.Series:
    """Databento 원시 일봉에서 아웃라이트 근월(일자별 최대 거래량) 종가 — UTC 일봉이라 진단용."""
    f = sorted(glob.glob(str(RAW / "Databento" / "GLBX.MDP3" / "OHLCV-1d" / sym / f"{sym}_ohlcv-1d_*.csv")))
    if not f:
        return pd.Series(dtype=float)
    d = pd.read_csv(f[-1], usecols=["ts_event", "close", "volume", "symbol"], skipinitialspace=True)
    d["symbol"] = d["symbol"].astype(str).str.strip()
    d = d[d["symbol"].str.fullmatch(rf"{sym}[FGHJKMNQUVXZ]\d")]
    d["date"] = pd.to_datetime(d["ts_event"].str[:10])
    d = d.sort_values("volume").drop_duplicates("date", keep="last")
    return d.set_index("date")["close"].astype(float).sort_index()


def _q3(s: pd.Series) -> list[float]:
    return [float(x) for x in np.quantile(s.dropna().to_numpy(), [0.25, 0.5, 0.75])]


def classical_lens(close: pd.Series) -> dict:
    """고전파 관점 — 대체재·바이오연료·압착 등가(parity)로 본 '기초가치 구간'과 평균 회귀 속도."""
    out = []
    usd_t = close * USC_LB_TO_USD_MT
    palm, myr = _mkt("TE_PALM_OIL"), _mkt("DEXMAUS")
    if len(palm) and len(myr):
        palm_usd = (palm / myr.reindex(palm.index, method="ffill")).dropna()
        j = pd.concat([usd_t, palm_usd], axis=1, keys=["sbo", "palm"], sort=True).dropna().iloc[-PARITY_WINDOW:]
        sp = j["sbo"] - j["palm"]
        q = _q3(sp)
        m = sp.resample("MS").mean().dropna().iloc[-120:]
        x0, x1 = (m - m.mean()).iloc[:-1].to_numpy(), (m - m.mean()).iloc[1:].to_numpy()
        phi = float(np.dot(x0, x1) / np.dot(x0, x0)) if len(x0) > 12 else float("nan")
        hl = round(math.log(0.5) / math.log(phi), 1) if 0 < phi < 1 else None
        out.append({"id": "palm", "name": "팜유 대체 등가", "basis": "대두유−팜유 가격 차이(최근 3년)",
                    "implied": [round((float(j["palm"].iloc[-1]) + v) / USC_LB_TO_USD_MT, 2) for v in q],
                    "now_gap": round(float(sp.iloc[-1]), 0), "gap_unit": "$/MT", "half_life_m": hl})
    ho = _mkt("TE_HEATING_OIL")
    if len(ho):
        gal = close * LB_PER_GAL / 100
        j = pd.concat([gal, ho], axis=1, keys=["sbo", "ho"], sort=True).dropna().iloc[-PARITY_WINDOW:]
        q = _q3(j["sbo"] - j["ho"])
        out.append({"id": "boho", "name": "바이오연료 등가(BOHO)", "basis": "대두유−난방유 갤런당 차이(최근 3년)",
                    "implied": [round((float(j["ho"].iloc[-1]) + v) * 100 / LB_PER_GAL, 2) for v in q],
                    "now_gap": round(float((j["sbo"] - j["ho"]).iloc[-1]), 2), "gap_unit": "$/gal", "half_life_m": None})
    zm = _front_month("ZM")
    if len(zm):
        j = pd.concat([close, zm], axis=1, keys=["zl", "zm"], sort=True).dropna().iloc[-PARITY_WINDOW:]
        share = j["zl"] * BUSHEL_OIL_LB / (j["zl"] * BUSHEL_OIL_LB + j["zm"] * BUSHEL_MEAL_ST)
        q = _q3(share)
        zm_now = float(j["zm"].iloc[-1])
        out.append({"id": "crush", "name": "압착 유지 비중(oil share)", "basis": "크러시 가치 중 유지 몫(최근 3년)",
                    "implied": [round(s * zm_now * BUSHEL_MEAL_ST / (BUSHEL_OIL_LB * (1 - s)), 2) for s in q],
                    "now_gap": round(float(share.iloc[-1]) * 100, 1), "gap_unit": "% 유지 비중", "half_life_m": None,
                    "caveat": "대두박은 UTC 일봉 근월(거래량 기준) — 정산가·롤 달력 불일치로 진단용"})
    zone = [round(float(np.median([p["implied"][i] for p in out])), 2) for i in range(3)] if out else None
    return {"parities": out, "zone": zone}


def keynesian_lens(close: pd.Series) -> dict:
    """케인스 관점 — 기대·불확실성: 최근 변동성 국면으로 기준선 범위 폭을 늘리거나 줄여 본 참고 범위."""
    r = np.log(close).diff().dropna()
    rv20, rv250 = float(r.iloc[-20:].std() * math.sqrt(252)), float(r.iloc[-250:].std() * math.sqrt(252))
    ratio = round(rv20 / rv250, 2) if rv250 else 1.0
    last, lp = float(close.iloc[-1]), np.log(close.to_numpy())
    scaled = {}
    for h in (20, 60):
        win = (lp[h:] - lp[:-h])[-ROLL:]
        qs = np.quantile(win, QUANTS)
        mid = qs[2]
        scaled[str(h)] = {f"p{int(q * 100)}": round(last * math.exp(mid + (v - mid) * ratio), 2) for q, v in zip(QUANTS, qs)}
    cot = sorted(glob.glob(str(RAW / "cot_positions_*.parquet")))
    pos = None
    if cot:
        c = pd.read_parquet(cot[-1], columns=["price_date", "indicator_code", "value"])
        s = c[c["indicator_code"] == "COT_SBO_MM_NET_PCT_OI"].set_index("price_date")["value"].sort_index().iloc[-260:]
        if len(s):
            pos = {"value": round(float(s.iloc[-1]), 1), "pctile": round(float((s <= s.iloc[-1]).mean() * 100), 0),
                   "date": s.index[-1].strftime("%Y-%m-%d")}
    return {"rv20": round(rv20 * 100, 1), "rv250": round(rv250 * 100, 1), "ratio": ratio, "scaled": scaled,
            "positioning": pos, "cr4": SOY_EXPORT_CR4}


def value_lens(close: pd.Series, classical: dict) -> dict:
    """가치 투자 렌즈(버핏·멍거·린치 원칙을 원자재에 옮긴 점검표) — 숫자는 서술용, 예측 모델 아님."""
    last = float(close.iloc[-1])
    zone = classical.get("zone")
    gap = round((last / zone[1] - 1) * 100, 1) if zone else None
    five = close.iloc[-1260:]
    pctile = round(float((five <= last).mean() * 100), 0)
    lp = np.log(close.to_numpy())
    r60 = lp[60:] - lp[:-60]
    stress = [round(last * math.exp(float(np.quantile(r60, q))), 2) for q in (0.01, 0.99)]
    stu = None
    w = RAW / "wasde_historical.parquet"
    if w.exists():
        d = pd.read_parquet(w, columns=["indicator_code", "value", "available_at", "price_date"])
        s = d[d["indicator_code"] == "WASDE_SBO_STU"]
        s = s[pd.to_datetime(s["available_at"]) <= pd.Timestamp.now()].sort_values("price_date")
        if len(s):
            v = float(s["value"].iloc[-1])
            stu = {"value": round(v, 2), "pctile": round(float((s["value"] <= v).mean() * 100), 0),
                   "date": pd.Timestamp(s["price_date"].iloc[-1]).strftime("%Y-%m")}
    if stu and stu["pctile"] <= 33 and pctile >= 67:
        cycle = "재고는 빠듯하고 가격은 5년 범위 위쪽 — 사이클 후반에 흔한 조합"
    elif stu and stu["pctile"] >= 67 and pctile <= 33:
        cycle = "재고는 넉넉하고 가격은 5년 범위 아래쪽 — 사이클 초반에 흔한 조합"
    else:
        cycle = "재고와 가격 위치가 엇갈림 — 사이클 위치를 단정하기 어려움"
    return {"gap_to_value": gap, "price_pctile_5y": pctile, "stress_60d": stress, "stu": stu, "cycle": cycle}


def build() -> dict:
    close = _close()
    hist = close.iloc[-HISTORY_DAYS:]
    routes_p = PROC / "route_scenarios_latest.json"
    routes = json.loads(routes_p.read_text(encoding="utf-8")) if routes_p.exists() else {}
    disrupted = {k for k, s in routes.get("status", {}).items() if s.get("state") == "disrupted"}
    classical = classical_lens(close)
    krw = _mkt("DEXKOUS")
    return {
        "lenses": {"classical": classical, "keynesian": keynesian_lens(close),
                   "value": value_lens(close, classical)},
        "prev_bands": bands(close.iloc[:-5], with_stats=False),
        "prev_as_of": close.index[-6].strftime("%Y-%m-%d"),
        "fx_krw": {"value": round(float(krw.iloc[-1]), 2), "date": krw.index[-1].strftime("%Y-%m-%d")} if len(krw) else None,
        "meta": {"as_of": close.index[-1].strftime("%Y-%m-%d"),
                 "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                 "unit": "USc/lb", "to_usd_mt": USC_LB_TO_USD_MT, "roll": ROLL,
                 "method": "B4a′ — 중심은 현재 정산가, 폭은 최근 변동성(EWMA) × √기간 × 정규 분위"},
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
