"""Nexus Terminal — 파이프라인 산출물을 한 화면의 대화형 대시보드로(최종 산출물).

모아 오는 것(모두 이미 생성된 산출물 — 새 계산은 범위 기간구조 표면뿐):
  정산가·참고 범위(B4a′)·시세 띠        src/reporting/g2_preview (_close · bands · tickers)
  일봉(캔들)                             yfinance ZL=F 최근 6개월 — 실패 시 정산가 선으로 대체(오프라인 안전)
  해상 경로 상태                         data/processed/route_scenarios_latest.json
  모델 평가 보드                         reports/g2_preview/band_method_compare.json + 기준선 백테스트 + B4a′ 이력
  G1 핵심 변인·경보                     reports/pipeline/g1_variable_importance_*_ko.md · g1_alert_ledger.csv
  파이프라인 콘솔                        docker/logs/<job>_*.json (scripts/pipeline_run_report와 같은 규칙)
  Codex 교차검증 요약                    reports/ops/codex_verify_<단계>_*.md 의 심각도 집계
  온톨로지 3D 그래프                     src/semantic/entities.yaml · ontology.yaml
  일별 비정형 신호                       data/processed/unstructured_daily_signals.csv
출력: reports/terminal/nexus_terminal.html (gitignore — 가격 수치 포함)
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from scripts.pipeline_run_report import LABELS, STAGES, latest
from src.reporting import g2_preview as g2

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "reporting" / "templates" / "terminal.html"
OUT = ROOT / "reports" / "terminal" / "nexus_terminal.html"
SURFACE_HORIZONS = [1, 2, 3, 5, 10, 15, 20, 30, 40, 60]
SURFACE_DAYS = 260
SURFACE_STEP = 5
CANDLE_DAYS = 130


def candles() -> dict:
    """최근 일봉 — 네트워크 실패해도 화면은 정산가 선으로 그려짐."""
    try:
        import yfinance as yf
        h = yf.Ticker("ZL=F").history(period="6mo", auto_adjust=False)
        h = h.dropna(subset=["Open", "High", "Low", "Close"]).iloc[-CANDLE_DAYS:]
        if len(h) < 20:
            raise ValueError("표본 부족")
        return {"source": "yfinance ZL=F 일봉(참고 — 정산가와 다를 수 있음)",
                "rows": [[d.strftime("%Y-%m-%d"), round(float(r.Open), 2), round(float(r.Close), 2),
                          round(float(r.Low), 2), round(float(r.High), 2), int(r.Volume or 0)]
                         for d, r in h.iterrows()]}
    except Exception as e:  # 오프라인·차단 — 정산가 선만
        print(f"[정보] 일봉 수집 생략({type(e).__name__}) — 정산가 선으로 표시")
        return {"source": None, "rows": []}


def range_surface(close: pd.Series) -> dict:
    """범위 기간구조 표면: x=날짜, y=지평(거래일), z=B4a′ 80% 범위 폭(%)."""
    lp = np.log(close.to_numpy())
    sig = {lam: g2._ewma_sigma(lp, lam) for lam in (0.94, 0.97)}
    idx = list(range(len(lp) - SURFACE_DAYS, len(lp), SURFACE_STEP))
    z90 = g2.Z[0.90]
    data = []
    for xi, t in enumerate(idx):
        for yi, h in enumerate(SURFACE_HORIZONS):
            s = sig[0.94 if h <= 5 else 0.97][t] * math.sqrt(h)
            data.append([xi, yi, round((math.exp(z90 * s) - math.exp(-z90 * s)) * 100, 2)])
    return {"dates": [close.index[t].strftime("%Y-%m-%d") for t in idx], "horizons": SURFACE_HORIZONS, "data": data}


def model_board(bands: dict) -> dict:
    rows = []
    cmp_p = ROOT / "reports" / "g2_preview" / "band_method_compare.json"
    names = {"B2_250": "B2 경험 분위 250일(이전)", "B2_120": "B2 경험 분위 120일", "EWMA_N": "EWMA 정규(0.94)",
             "FHS_750": "FHS 750일", "EWMA_CONF": "EWMA+컨포멀(B4 원안)"}
    if cmp_p.exists():
        d = json.loads(cmp_p.read_text(encoding="utf-8"))
        for h, models in d.get("horizons", {}).items():
            for k, m in models.items():
                rows.append({"h": int(h), "model": names.get(k, k), "cov80": m.get("cov80_pct"),
                             "width": m.get("width_pct"), "pinball": m.get("pinball_x1e3"), "now": (m.get("now") or [None] * 3)[2]})
    for h, b in bands.items():
        s = b.get("stats") or {}
        rows.append({"h": int(h), "model": "B4a′ EWMA 지평별 λ(적용)", "cov80": s.get("cov80"), "cov50": s.get("cov50"),
                     "above": s.get("above90"), "below": s.get("below10"), "applied": True})
    base_p = ROOT / "data" / "processed" / "g2_band_backtest_latest.json"
    if base_p.exists():
        d = json.loads(base_p.read_text(encoding="utf-8"))
        for h, models in d.get("horizons", {}).items():
            for k, m in models.items():
                wf = m.get("walk_forward") or {}
                if "coverage_80" in wf:
                    rows.append({"h": int(h), "model": f"기준선 {k}", "cov80": round(wf["coverage_80"] * 100, 1),
                                 "cov50": round(wf["coverage_50"] * 100, 1), "mae": wf.get("mae_p50_pct"), "baseline": True})
    return {"rows": rows}


def g1_panel() -> dict:
    out = {"top": [], "alerts": []}
    md = sorted(glob.glob(str(ROOT / "reports" / "pipeline" / "g1_variable_importance_*_ko.md")), key=os.path.getmtime)
    if md:
        for line in Path(md[-1]).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*([A-Za-z0-9_]+)\s*\|\s*(-?\d+\.\d+)\s*\|", line)
            if m and len(out["top"]) < 10:
                out["top"].append({"var": m.group(1), "r": float(m.group(2))})
        out["as_of"] = datetime.fromtimestamp(os.path.getmtime(md[-1])).strftime("%Y-%m-%d %H:%M")
    led = ROOT / "reports" / "pipeline" / "g1_alert_ledger.csv"
    if led.exists():
        rows = list(csv.DictReader(led.open(encoding="utf-8")))
        if rows:
            last = max(r["date"] for r in rows)
            out["alerts"] = [{"var": r["variable"], "value": r["value"], "threshold": r["threshold"], "status": r["status"],
                              "date": r["date"]} for r in rows if r["date"] == last][:8]
    return out


def console() -> dict:
    now = datetime.now()
    stages = []
    for title, desc, jobs in STAGES:
        items = []
        for j in jobs:
            d = latest(j)
            if d is None:
                items.append({"job": LABELS[j], "state": "none"})
                continue
            fresh = (now - d["_mtime"]).total_seconds() < 86400
            items.append({"job": LABELS[j], "state": "fail" if d.get("failed") and fresh else ("ok" if fresh else "stale"),
                          "secs": round(sum(s.get("seconds", 0) for s in d.get("steps", []))),
                          "at": d["_mtime"].strftime("%m-%d %H:%M")})
        stages.append({"title": title, "desc": desc, "items": items})
    codex = {}
    for st in ("collect", "process", "analyze"):
        files = sorted(glob.glob(str(ROOT / "reports" / "ops" / f"codex_verify_{st}_*.md")))
        if files:
            t = Path(files[-1]).read_text(encoding="utf-8")
            codex[st] = {k: len(re.findall(rf"\|\s*{k}\s*\|", t)) for k in ("치명", "높음", "참고")}
            codex[st]["date"] = Path(files[-1]).stem.split("_")[-1]
    return {"stages": stages, "codex": codex}


def ontology_graph() -> dict:
    ent = yaml.safe_load((ROOT / "src/semantic/entities.yaml").read_text(encoding="utf-8"))
    ont = yaml.safe_load((ROOT / "src/semantic/ontology.yaml").read_text(encoding="utf-8"))
    nodes, links, seen = [], [], set()

    def add(nid, label, group, val=1):
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "label": label, "group": group, "val": val})

    terms = {t["term_id"]: t for k, v in ent.items() if isinstance(v, list) for t in v if isinstance(t, dict) and "term_id" in t}
    for e in ont.get("causal_edges", []):
        chain = [e["cause"]["node"], *[m["node"] for m in e.get("mechanisms", [])], e["outcome"]["node"]]
        for i, n in enumerate(chain):
            add(n, n, "원인" if i == 0 else ("결과" if i == len(chain) - 1 else "경로"), 4 if i == len(chain) - 1 else 2)
        for a, b in zip(chain, chain[1:]):
            links.append({"source": a, "target": b, "edge": e["edge_id"], "dir": e.get("direction")})
        for tid in e["cause"].get("entity_terms", []):
            if tid in terms:
                t = terms[tid]
                add(tid, t.get("canonical_ko") or t.get("canonical"), t.get("class") or "용어", 1)
                links.append({"source": tid, "target": chain[0], "edge": "용어", "dir": None})
    for tid, t in terms.items():   # 사슬에 안 걸린 용어도 분류 허브에 연결해 전체 구조를 보이게
        if tid in seen:
            continue
        cls = t.get("class") or "기타"
        add(f"CLS:{cls}", cls, "분류", 3)
        add(tid, t.get("canonical_ko") or t.get("canonical"), cls, 0.6)
        links.append({"source": tid, "target": f"CLS:{cls}", "edge": "분류", "dir": None})
    return {"nodes": nodes, "links": links, "n_terms": len(terms), "n_edges": len(ont.get("causal_edges", []))}


def signals() -> list[dict]:
    p = ROOT / "data" / "processed" / "unstructured_daily_signals.csv"
    if not p.exists():
        return []
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    if not rows:
        return []
    days = sorted({r["date"] for r in rows})[-3:]
    return [{"date": r["date"], "cat": r.get("category", ""), "ind": r.get("indicator", ""), "value": r.get("value", ""),
             "note": (r.get("note") or "")[:140]} for r in rows if r["date"] in days][-40:]


def main() -> None:
    close = g2._close()
    bands = g2.bands(close)
    routes = json.loads((ROOT / "data/processed/route_scenarios_latest.json").read_text(encoding="utf-8")) \
        if (ROOT / "data/processed/route_scenarios_latest.json").exists() else {}
    data = {
        "meta": {"as_of": close.index[-1].strftime("%Y-%m-%d"), "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "unit": "USc/lb", "to_usd_mt": g2.USC_LB_TO_USD_MT},
        "price": [[d.strftime("%Y-%m-%d"), round(float(v), 2)] for d, v in close.iloc[-500:].items()],
        "candles": candles(), "bands": bands, "tickers": g2.tickers(),
        "routes": {k: {"state": v.get("state"), "label": v.get("label") or k} for k, v in routes.get("status", {}).items()},
        "surface": range_surface(close), "models": model_board(bands), "g1": g1_panel(), "console": console(),
        "graph": ontology_graph(), "signals": signals(),
    }
    tpl = TEMPLATE.read_text(encoding="utf-8")
    if "/*__NEXUS_DATA__*/null" not in tpl:
        raise RuntimeError("[오류] 터미널 템플릿 자리표시자 없음")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(tpl.replace("/*__NEXUS_DATA__*/null", payload), encoding="utf-8")
    print(f"[완료] Nexus Terminal → {OUT.relative_to(ROOT)} · 기준일 {data['meta']['as_of']} · 캔들 {len(data['candles']['rows'])}개 · "
          f"온톨로지 노드 {len(data['graph']['nodes'])}·연결 {len(data['graph']['links'])}")


if __name__ == "__main__":
    main()
