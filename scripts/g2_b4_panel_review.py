"""G2 B4 패널 검토 — B2 vs EWMA-정규 vs EWMA+컨포멀(및 변형) 추가 증거.

누수 점검: t일 범위는 (a) 수익률·변동성은 lp[0..t]만, (b) 보정·경험분위 표본은 결과가 t까지 실현된 쌍(s+h <= t)만 사용.
HAR 회귀도 t 시점에 목표가 실현된 쌍만으로 20거래일마다 재적합(확장창).
변동성 3분위 층화는 평가 구간 전체 기준 사후 층화(보고용, 모델 입력 아님).
출력: 표준출력(가격 수준은 출력하지 않음 — 전부 현재가 대비 %).
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from src.reporting.g2_preview import _close

HORIZONS = (5, 20, 60)
EVAL_START, EVAL_END = pd.Timestamp("2012-01-01"), pd.Timestamp("2025-12-31")
LOCK_START, LOCK_END = pd.Timestamp("2025-07-01"), pd.Timestamp("2025-12-31")
Z = {0.10: -1.2816, 0.25: -0.6745, 0.75: 0.6745, 0.90: 1.2816}
TAUS = (0.10, 0.25, 0.75, 0.90)
CONF_MIN = 100

close = _close()
close = close[close.index >= "2010-01-01"]
dates = close.index
lp = np.log(close.to_numpy())
n = len(lp)
r = np.diff(lp)  # r[k] = lp[k+1]-lp[k]


def ewma_sig(lam: float) -> np.ndarray:
    s2 = np.empty(n)
    s2[0] = r[:20].var()
    for t in range(1, n):
        s2[t] = lam * s2[t - 1] + (1 - lam) * r[t - 1] ** 2
    return np.sqrt(s2)


SIG94, SIG97 = ewma_sig(0.94), ewma_sig(0.97)

# ---- HAR-direct 일변동성(지평별) ---------------------------------------------------
c2 = np.concatenate([[0.0], np.cumsum(r ** 2)])  # c2[k] = sum r[0..k-1]^2


def _rv_back(t: int, m: int) -> float:  # 평균 r^2, r[t-m..t-1] (lp[0..t] 사용)
    return (c2[t] - c2[t - m]) / m


def har_sig(h: int) -> np.ndarray:
    eps = 1e-10
    X = np.full((n, 5), np.nan)
    for t in range(66, n):
        X[t] = [1.0] + [math.log(_rv_back(t, m) + eps) for m in (1, 5, 22, 66)]
    Y = np.full(n, np.nan)  # 원점 s의 목표: 평균 r^2, r[s..s+h-1] → t=s+h에 실현
    for s in range(0, n - h):
        Y[s] = math.log((c2[s + h] - c2[s]) / h + eps)
    out = np.full(n, np.nan)
    beta, s2res = None, 0.0
    for t in range(66, n):
        if (t % 20 == 0 or beta is None) and t - h - 66 >= 500:
            idx = np.arange(66, t - h + 1)  # s+h <= t
            b, *_ = np.linalg.lstsq(X[idx], Y[idx], rcond=None)
            beta = b
            s2res = float(np.var(Y[idx] - X[idx] @ b))
        if beta is not None:
            out[t] = math.sqrt(math.exp(float(X[t] @ beta) + 0.5 * s2res))
    # 초기 구간은 EWMA로 대체
    return np.where(np.isnan(out), SIG94, out)


# ---- 범위 생성 ---------------------------------------------------------------------
def build(h: int) -> dict[str, np.ndarray]:
    """각 방법의 t별 로그수익률 분위 [q10,q25,q75,q90] (n×4, 미정의는 nan)."""
    Rh = np.full(n, np.nan)
    Rh[: n - h] = lp[h:] - lp[: n - h]  # Rh[s]: s→s+h, s+h에 실현
    sq = math.sqrt(h)
    sigs = {"94": SIG94, "97": SIG97, "HAR": har_sig(h)}
    Zs = {k: Rh / (v * sq) for k, v in sigs.items()}  # 원점 s 기준 표준화 점수
    M: dict[str, np.ndarray] = {}

    def new(name):
        M[name] = np.full((n, 4), np.nan)
        return M[name]

    b2, b2c = new("B2_250"), new("B2_250_무드리프트")
    specs = []  # (name, sigkey, kind, window)
    for lam in ("94", "97", "HAR"):
        specs.append((f"N_{lam}", lam, "normal", 0))
    for W in (250, 500, 750, 1000):
        specs.append((f"CONF{W}_94", "94", "sym", W))
        specs.append((f"ACONF{W}_94", "94", "asym", W))
    for W in (250, 750):
        specs.append((f"CONF{W}_97", "97", "sym", W))
        specs.append((f"CONF{W}_HAR", "HAR", "sym", W))
    specs.append(("ACONF750_97", "97", "asym", 750))
    specs.append(("CONF500_97", "97", "sym", 500))
    specs.append(("CONF1000_97", "97", "sym", 1000))  # 방법론 문서 §4 B4 기본값(h=60)
    for nm, *_ in specs:
        new(nm)
    for t in range(h + 250, n):
        hist = Rh[t - h - 249 : t - h + 1]
        q = np.quantile(hist, [0.10, 0.25, 0.50, 0.75, 0.90])
        b2[t] = q[[0, 1, 3, 4]]
        b2c[t] = q[[0, 1, 3, 4]] - q[2]
        for nm, sk, kind, W in specs:
            sd = sigs[sk][t] * sq
            if kind == "normal":
                M[nm][t] = [Z[a] * sd for a in TAUS]
                continue
            lo = max(0, t - h - W + 1)
            zz = Zs[sk][lo : t - h + 1]
            if len(zz) < CONF_MIN:
                M[nm][t] = [Z[a] * sd for a in TAUS]
            elif kind == "sym":
                k80, k50 = np.quantile(np.abs(zz), [0.8, 0.5])
                M[nm][t] = [-k80 * sd, -k50 * sd, k50 * sd, k80 * sd]
            else:
                M[nm][t] = np.quantile(zz, list(TAUS)) * sd
    return M, Rh


# ---- 평가 --------------------------------------------------------------------------
def metrics(Q: np.ndarray, y: np.ndarray, mask: np.ndarray) -> dict:
    q, yy = Q[mask], y[mask]
    if len(yy) == 0:
        return {}
    lo80, lo50, hi50, hi80 = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    pin = np.mean([np.maximum(a * (yy - q[:, i]), (a - 1) * (yy - q[:, i])) for i, a in enumerate(TAUS)], axis=0)
    return {
        "n": int(len(yy)),
        "cov80": 100 * np.mean((yy >= lo80) & (yy <= hi80)),
        "low80": 100 * np.mean(yy < lo80), "up80": 100 * np.mean(yy > hi80),
        "w80": 100 * np.mean(np.exp(hi80) - np.exp(lo80)),
        "cov50": 100 * np.mean((yy >= lo50) & (yy <= hi50)),
        "low50": 100 * np.mean(yy < lo50), "up50": 100 * np.mean(yy > hi50),
        "w50": 100 * np.mean(np.exp(hi50) - np.exp(lo50)),
        "pin": 1e3 * float(np.mean(pin)),
    }


def block_ci(x: np.ndarray, b: int, reps: int = 2000, seed: int = 7) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    m = len(x)
    k = int(np.ceil(m / b))
    st = rng.integers(0, m - b + 1, size=(reps, k))
    means = np.array([np.concatenate([x[s : s + b] for s in row])[:m].mean() for row in st])
    return float(np.percentile(means, 5)), float(np.percentile(means, 95))


def main() -> None:
    out = {"as_of": str(dates[-1].date()), "h": {}}
    sig_eval = SIG94[(dates >= EVAL_START) & (dates <= EVAL_END)]
    t1, t2 = np.quantile(sig_eval, [1 / 3, 2 / 3])
    years = {"2012": 2012, "2018": 2018, "2020": 2020, "2022": 2022, "2025": 2025, "2026s": 2026}
    for h in HORIZONS:
        M, Rh = build(h)
        valid = np.arange(n) + h < n
        base = valid & (dates >= EVAL_START) & (dates <= EVAL_END)
        masks = {"WF": base, "LOCK25H2": valid & (dates >= LOCK_START) & (dates <= LOCK_END)}
        for k, yv in years.items():
            masks[k] = valid & (dates.year == yv)
        masks["VOL_L"] = base & (SIG94 <= t1)
        masks["VOL_M"] = base & (SIG94 > t1) & (SIG94 <= t2)
        masks["VOL_H"] = base & (SIG94 > t2)
        res = {}
        for nm, Q in M.items():
            okm = ~np.isnan(Q[:, 0])
            res[nm] = {mk: metrics(Q, Rh, m & okm) for mk, m in masks.items()}
            qn = Q[n - 1]
            res[nm]["now"] = {"q_pct": [round(100 * (math.exp(v) - 1), 1) for v in qn],
                              "w80": round(100 * (math.exp(qn[3]) - math.exp(qn[0])), 1),
                              "w50": round(100 * (math.exp(qn[2]) - math.exp(qn[1])), 1)}
            w80 = 100 * (np.exp(Q[:, 3]) - np.exp(Q[:, 0]))
            w50 = 100 * (np.exp(Q[:, 2]) - np.exp(Q[:, 1]))
            stab = {}
            for lab, mm in (("WF", (dates >= EVAL_START) & (dates <= EVAL_END) & okm), ("last250", (np.arange(n) >= n - 250) & okm)):
                d80 = np.abs(np.diff(w80[mm]))
                d50 = np.abs(np.diff(w50[mm]))
                stab[lab] = {"d80_mean": float(d80.mean()), "d80_p95": float(np.percentile(d80, 95)),
                             "d80_max": float(d80.max()), "d80_gt1": 100 * float(np.mean(d80 > 1.0)),
                             "d50_mean": float(d50.mean()), "d50_p95": float(np.percentile(d50, 95)),
                             "w80_sd": float(np.std(w80[mm]))}
            res[nm]["stab"] = stab
        # 블록 부트스트랩: pinball 차이(방법 − B2), 80% coverage 90% CI
        boot = {}
        yb = Rh[base]
        def pinser(Q):
            q = Q[base]
            return np.mean([np.maximum(a * (yb - q[:, i]), (a - 1) * (yb - q[:, i])) for i, a in enumerate(TAUS)], axis=0)
        pb2 = pinser(M["B2_250"])
        for nm in M:
            hit = ((yb >= M[nm][base][:, 0]) & (yb <= M[nm][base][:, 3])).astype(float)
            boot[nm] = {"cov80_ci": [100 * v for v in block_ci(hit, h)],
                        "dpin_vs_B2_ci": [1e3 * v for v in block_ci(pinser(M[nm]) - pb2, h)]}
        res["_boot"] = boot
        out["h"][h] = res
        print(f"[정보] h={h} 완료", flush=True)
    print("JSON_START")
    print(json.dumps(out, ensure_ascii=False, default=lambda o: round(float(o), 2)))


if __name__ == "__main__":
    main()
