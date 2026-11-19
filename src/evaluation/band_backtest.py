"""G2 밴드 백테스트 — 기준선 분위 밴드의 워크포워드 성적 (2026-09-14 · R-038).

목적: G2 Preview(동결 하 백테스트 전용)의 **기대 정확도 하한**을 실측으로 잡는다.
Champion 스택(SARIMAX + Quantile LightGBM + EGARCH-X → EnCQR)은 미구현이므로, 여기서는
기준선 3종만 산출하고 Champion의 기대 개선은 문헌 근거로 INFERENCE 표기한다(문서 참조).

기준선
  B1 최근값(last value): 분포 폭 0 — 점 예측 기준선(pinball 비교용)
  B2 롤링 경험 분위(직전 250거래일 h일 로그수익률의 P10/P25/P50/P75/P90) — 브리프 참고 범위와 동형
  B3 계절 naive: 1년 전 같은 시점의 h일 수익률을 중앙으로, 폭은 B2와 동일
지표(모델 방법론 §Validation Protocol): pinball(P10/P50/P90)·경험 포함률(50/80%)·평균 폭·
  스트레스 슬라이스별 포함률·락박스(2025-07~12) 별도. 방향 적중률은 산출하지 않는다.
누수 차단: t 시점 분위는 t까지 확정된 수익률(r[t] = t−h→t)만 사용. 실측 = t→t+h.

실행: python -m src.evaluation.band_backtest  → reports/market/g2_band_backtest_{date}.md + JSON
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.evaluation.g1_reliability import HORIZONS, STRESS_SLICES, WINDOW_END, WINDOW_START, load_inputs  # noqa: E402

QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
ROLL = 250
LOCKBOX = ("2025-07-01", "2025-12-31")


def pinball(y: pd.Series, q_pred: pd.Series, q: float) -> float:
    d = y - q_pred
    return float(np.mean(np.maximum(q * d, (q - 1) * d)))


def _baseline_bands(logc: pd.Series, h: int) -> dict[str, pd.DataFrame]:
    """각 기준선의 t 시점 분위 예측(로그수익률 단위) — 인덱스 t, 열 q."""
    r_past = logc - logc.shift(h)                     # t에 확정된 t−h→t 수익률
    roll = {q: r_past.rolling(ROLL, min_periods=120).quantile(q) for q in QUANTILES}
    b2 = pd.DataFrame(roll)
    b1 = pd.DataFrame({q: 0.0 for q in QUANTILES}, index=logc.index)      # 최근값 유지 = 수익률 0
    seasonal_center = r_past.shift(252 - h).fillna(0.0)                   # 1년 전 같은 시점의 h일 수익률
    b3 = b2.sub(b2[0.50], axis=0).add(seasonal_center, axis=0)
    return {"B1 최근값": b1, "B2 롤링 경험 분위(250일)": b2, "B3 계절 naive": b3}


def run_backtest(close: pd.Series) -> dict[str, Any]:
    logc = np.log(close.astype(float).sort_index())
    out: dict[str, Any] = {"quantiles": list(QUANTILES), "roll": ROLL, "window": [WINDOW_START, WINDOW_END],
                           "lockbox": list(LOCKBOX), "horizons": {}}
    for h in HORIZONS:
        realized = logc.shift(-h) - logc
        outcome_date = pd.Series(logc.index, index=logc.index).shift(-h)   # t 예측의 채점일(t+h)
        bands = _baseline_bands(logc, h)
        res_h: dict[str, Any] = {}
        for name, bd in bands.items():
            j = pd.concat([realized.rename("y"), bd], axis=1).dropna()
            j = j[(j.index >= pd.Timestamp(WINDOW_START)) & (j.index <= pd.Timestamp(WINDOW_END))]
            if len(j) < 300:
                res_h[name] = {"status": "표본 부족"}
                continue
            lock = (j.index >= pd.Timestamp(LOCKBOX[0])) & (j.index <= pd.Timestamp(LOCKBOX[1]))
            # 본 평가는 채점일까지 락박스 이전이어야 함 — 경계 h일을 비워 락박스 실측이 섞이지 않게(정화)
            main = j[~lock & (outcome_date.reindex(j.index) < pd.Timestamp(LOCKBOX[0])).to_numpy()]
            def _score(sub: pd.DataFrame) -> dict[str, Any]:
                y = sub["y"]
                return {
                    "n": int(len(sub)),
                    "pinball_p10": round(pinball(y, sub[0.10], 0.10), 5),
                    "pinball_p50": round(pinball(y, sub[0.50], 0.50), 5),
                    "pinball_p90": round(pinball(y, sub[0.90], 0.90), 5),
                    "coverage_50": round(float(((y >= sub[0.25]) & (y <= sub[0.75])).mean()), 3),
                    "coverage_80": round(float(((y >= sub[0.10]) & (y <= sub[0.90])).mean()), 3),
                    "width_80_pct": round(float((sub[0.90] - sub[0.10]).mean() * 100), 2),
                    "mae_p50_pct": round(float((y - sub[0.50]).abs().mean() * 100), 2)}
            entry = {"walk_forward": _score(main), "lockbox": _score(j[lock]) if lock.sum() >= 20 else {"status": "표본 부족"},
                     "by_slice": {}}
            for sname, (s, e) in STRESS_SLICES.items():
                m = (main.index >= pd.Timestamp(s)) & (main.index <= pd.Timestamp(e))
                if m.sum() >= 20:
                    entry["by_slice"][sname] = {"n": int(m.sum()),
                                                "coverage_80": round(float(((main["y"] >= main[0.10]) & (main["y"] <= main[0.90]))[m].mean()), 3)}
            res_h[name] = entry
        out["horizons"][str(h)] = res_h
    return out


def render_markdown(res: dict[str, Any], basis: str) -> str:
    L = [f"# G2 밴드 백테스트 — 기준선 3종 (기대 정확도 하한) — {date.today().isoformat()}", "",
         f"> 입력 기반: **{basis}** · 분석창 {res['window'][0]}~{res['window'][1]} · 락박스 {res['lockbox'][0]}~{res['lockbox'][1]} 별도 · 롤링 창 {res['roll']}거래일",
         "> 산출은 기준선의 과거 표본 성적이며 Champion 스택 성적이 아니다. 방향 판단·오를 가능성 같은 확률 주장은 산출하지 않는다.", ""]
    for h in HORIZONS:
        L.append(f"## 지평 {h}거래일")
        L.append("")
        L.append("| 기준선 | 표본 | pinball P10 | pinball P50 | pinball P90 | 포함률 50% | 포함률 80% | 80% 폭 | 중앙 MAE | 락박스 80% 포함률 |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for name, e in res["horizons"][str(h)].items():
            if e.get("status"):
                L.append(f"| {name} | {e['status']} | | | | | | | | |")
                continue
            w, lk = e["walk_forward"], e["lockbox"]
            L.append(f"| {name} | {w['n']:,} | {w['pinball_p10']} | {w['pinball_p50']} | {w['pinball_p90']} | "
                     f"{w['coverage_50']*100:.0f}% | {w['coverage_80']*100:.0f}% | {w['width_80_pct']:.1f}%(로그) | {w['mae_p50_pct']:.2f}% | "
                     f"{(str(round(lk['coverage_80']*100)) + '%') if lk.get('coverage_80') is not None else lk.get('status')} |")
        L.append("")
        b2 = res["horizons"][str(h)].get("B2 롤링 경험 분위(250일)", {})
        if b2.get("by_slice"):
            L.append("스트레스 구간 80% 포함률(롤링 경험 분위): " +
                     " · ".join(f"{k} {v['coverage_80']*100:.0f}%" for k, v in b2["by_slice"].items()))
            L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    inp = load_inputs()
    res = run_backtest(inp.close)
    res["basis"] = inp.basis
    Path("data/processed").mkdir(exist_ok=True, parents=True)
    Path("data/processed/g2_band_backtest_latest.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    out = Path("reports/market") / f"g2_band_backtest_{date.today().isoformat()}.md"
    out.write_text(render_markdown(res, inp.basis), encoding="utf-8")
    print(f"[완료] G2 밴드 백테스트 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
