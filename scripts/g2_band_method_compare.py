"""G2 참고 범위 산출 방식 비교 — walk-forward 백테스트(2012~2025, 80% 구간).

비교 대상(B2는 과거 수익률 분위를 그대로 — 중심도 과거 추세를 따름 / 나머지는 중심 = 현재가, 무변화):
  B2_250 / B2_120 : 최근 250/120일 겹치는 h일 로그수익률의 경험 분위(구 g2_preview 기준선)
  EWMA_N          : EWMA(λ=0.94) 일변동성 × √h × 정규 분위
  FHS_750         : 과거 750일 h일 수익률을 당시 EWMA로 표준화한 경험 분위 × 현재 σ
  EWMA_CONF       : EWMA 폭 × 롤링 컨포멀 배수(최근 250개 '이미 실현된' 표준화 점수의 80% 분위)

누수 점검: t 시점 계산은 결과가 t까지 실현된 쌍(s+h ≤ t)만 사용함.
출력은 로컬 전용(reports/g2_preview/ — gitignore). 가격 수치는 저장소에 커밋하지 않음.
실행: docker exec -w /repo docker-runner-1 python scripts/g2_band_method_compare.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.reporting.g2_preview import _close

EWMA_LAMBDA = 0.94
EWMA_SEED_DAILY_VOL = 0.015  # 초기 일변동성 사전값(연율 약 24%) — 2010년 초 몇 달 뒤 영향 소멸
Z10 = 1.2816  # 정규 10% 분위 절댓값
CONF_WINDOW = 250
CONF_MIN = 50
FHS_WINDOW = 750
EVAL_START, EVAL_END = pd.Timestamp("2012-01-01"), pd.Timestamp("2025-12-31")
HORIZONS = (5, 20, 60)
OUT = Path("reports/g2_preview/band_method_compare.json")


def _ewma_sigma(r: np.ndarray, n: int) -> np.ndarray:
    s2 = np.empty(n)
    s2[0] = EWMA_SEED_DAILY_VOL ** 2      # 미래 수익률을 쓰지 않는 고정 사전값(평가 시작 2012 전에 소멸)
    for t in range(1, n):
        s2[t] = EWMA_LAMBDA * s2[t - 1] + (1 - EWMA_LAMBDA) * r[t - 1] ** 2
    return np.sqrt(s2)


def _bands(lp: np.ndarray, sig: np.ndarray, t: int, h: int, scores: list[float]) -> dict:
    sd = sig[t] * np.sqrt(h)
    hist = lp[h : t + 1] - lp[: t + 1 - h]
    q = {name: np.quantile(hist[-win:], [0.1, 0.9]) for name, win in (("B2_250", 250), ("B2_120", 120))}
    q["EWMA_N"] = np.array([-Z10 * sd, Z10 * sd])
    idx = np.arange(max(0, t - FHS_WINDOW - h + 1), t - h + 1)   # 결과가 실현된 쌍 정확히 750개
    if len(idx) > 100:
        std = (lp[idx + h] - lp[idx]) / (sig[idx] * np.sqrt(h))
        q["FHS_750"] = np.quantile(std, [0.1, 0.9]) * sd
    else:
        q["FHS_750"] = q["EWMA_N"]
    k = np.quantile(scores[-CONF_WINDOW:], 0.8) if len(scores) > CONF_MIN else Z10
    q["EWMA_CONF"] = np.array([-k * sd, k * sd])
    return q


def evaluate(close: pd.Series, h: int) -> dict:
    dates = close.index
    lp = np.log(close.to_numpy())
    n = len(lp)
    sig = _ewma_sigma(np.diff(lp), n)
    out: dict[str, dict[str, list]] = {}
    scores: list[float] = []
    for t in range(h, n):
        # 컨포멀 점수: t에서 막 실현된 쌍(t-h → t)만 추가
        scores.append(abs(lp[t] - lp[t - h]) / (sig[t - h] * np.sqrt(h)))
        if t + h >= n or not (EVAL_START <= dates[t] <= EVAL_END):
            continue
        y = lp[t + h] - lp[t]
        for name, (a, b) in _bands(lp, sig, t, h, scores).items():
            o = out.setdefault(name, {"hit": [], "w": [], "pin": []})
            o["hit"].append(a <= y <= b)
            o["w"].append(np.exp(b) - np.exp(a))
            o["pin"].append((0.1 * max(y - a, 0) + 0.9 * max(a - y, 0) + 0.9 * max(y - b, 0) + 0.1 * max(b - y, 0)) / 2)
    res = {
        name: {
            "n": len(o["hit"]),
            "cov80_pct": round(float(np.mean(o["hit"])) * 100, 1),
            "width_pct": round(float(np.mean(o["w"])) * 100, 1),
            "pinball_x1e3": round(float(np.mean(o["pin"])) * 1e3, 2),
        }
        for name, o in out.items()
    }
    last = float(close.iloc[-1])
    for name, (a, b) in _bands(lp, sig, n - 1, h, scores).items():
        res[name]["now"] = [round(last * np.exp(a), 2), round(last * np.exp(b), 2), round((np.exp(b) - np.exp(a)) * 100, 1)]
    return res


def main() -> None:
    close = _close()
    close = close[close.index >= "2010-01-01"]
    result = {"as_of": str(close.index[-1].date()), "horizons": {h: evaluate(close, h) for h in HORIZONS}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    for h, rows in result["horizons"].items():
        print(f"[정보] h={h}: " + " · ".join(f"{k} cov {v['cov80_pct']}% 폭 {v['width_pct']}%" for k, v in rows.items()))
    print(f"[완료] {OUT}")


if __name__ == "__main__":
    main()
