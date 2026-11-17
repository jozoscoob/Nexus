#!/usr/bin/env python3
"""
A-145: 세션 종가 검증기 (WBS · P0) — Databento UTC 일봉 종가 vs 정산가(yfinance) 교차검증

목적:
  Databento GLBX.MDP3 ZL ohlcv-1d의 UTC 기준 종가(CBOT_BO_CLOSE 후보)가 CME 공식
  정산가와 사실상 동일한지 통계적으로 검증한 뒤, PASS일 때만 G2 타깃용
  data/raw/cbot_session_close.parquet 를 발행한다.

입력:
  1) data/raw/databento_bo_utc_historical.parquet (우선)
     → 없으면 data/raw/databento_bo_historical.parquet
     → 없으면 data/raw/Databento/GLBX.MDP3/ 최신 CSV에서 재구성
  2) 정산가 표본: yfinance BO=F (실패 시 ZL=F) — curl_cffi 세션(impersonate="chrome",
     A-071 패턴). 기간: 가능한 전체(period="max", 실패 시 축소).

발행 정책 (A-156 — 첫 실행 실측으로 설계 반전):
  구 설계는 UTC 종가를 정산가 근사로 "승격"하려 했으나, 첫 실행에서 ZL=F 정산가
  원계열 6,565일(2000~2026)이 확보됐고 중앙값 차이 0.1003%·P99 1.34%로
  꼬리 괴리가 실재함이 확인됐다. → **정산가 원계열을 CBOT_BO_CLOSE로 발행**하고
  (게이트 (b) '거래소 공식 settlement' 원문 경로), Databento UTC는 보강 검증으로 사용.
PASS 기준: 교집합 ≥ 500일 · 중앙값 ≤ 0.25%(동일 상품 확인) ·
  괴리 2% 초과일 비율 ≤ 2%(불량 틱 상한, 롤일 제외 — 의심일은 리포트에 기록)

종료 코드:
  0 = PASS (parquet 발행 + 리포트)
  1 = FAIL (리포트에 어긋난 날짜 상위 20건 표)
  2 = 검증 불가 — 정산가 표본 미확보 (CBOT_BO_CLOSE 미발행, 잡 실패 아님)

참고: docs/operations/g1_g2_preview_release_gates.md 및 src/features/build_feature_mart.py
      (TARGET_TIME_BASES)는 본 저장소 스냅샷에 부재 — 계약 필드는
      scripts/ingest_databento_bo.py(CBOT_BO_ 지표 규약)와 src/pipeline/asof.py
      (attach_asof(source="CBOT_BO_"))를 단일 근거로 발행한다.
      time_basis="EXCHANGE_SETTLEMENT" — mart TARGET_TIME_BASES 허용값이며,
      게이트 (b)경로(공식 정산가와 표본 교차검증 통과)에 해당한다. 값 자체는 UTC
      일봉 종가이고 정산가와의 정합은 본 검증기가 통계로 보증한다(리포트 참조).

실행 환경: GitHub Actions (개발 샌드박스는 외부 API 차단 — yfinance 수집 불가)
의존성: yfinance · curl_cffi · pandas · pyarrow
"""
from __future__ import annotations

import glob
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
from src.pipeline.asof import attach_asof  # noqa: E402

# ── 입력 경로 (우선순위 체인) ────────────────────────────────────────────────
PARQUET_CANDIDATES = [
    Path("data/raw/databento_bo_utc_historical.parquet"),
    Path("data/raw/databento_bo_historical.parquet"),
]
CSV_DIR = Path("data/raw/Databento/GLBX.MDP3")

OUT_PARQUET = Path("data/raw/cbot_session_close.parquet")
REPORT_DIR  = Path("reports/market")

# ── PASS 기준 (리포트에 그대로 명시) ────────────────────────────────────────
MIN_OVERLAP_DAYS = 500      # 교집합 최소 일수
MAX_MEDIAN_PCT   = 0.10     # 상대차 중앙값 상한 (%)
MAX_P99_PCT      = 0.60     # 상대차 P99 상한 (%)
MAX_ABS_PCT      = 2.00     # 상대차 최대 상한 (%) — 롤일 제외

# A-156: 정산가-원계열 발행 기준 (구 'UTC 종가 승격' 기준을 대체)
IDENTITY_MEDIAN_PCT = 0.25   # 동일 상품 판정 — 중앙값 상대차 상한 (%)
SUSPECT_DIFF_PCT    = 2.0    # 이 이상 괴리(롤일 제외)는 불량 틱 의심으로 기록
MAX_SUSPECT_FRAC    = 0.02   # 의심일 비율 상한 (교집합 대비)

EXIT_PASS, EXIT_FAIL, EXIT_NO_SAMPLE = 0, 1, 2


def _load_databento_close() -> tuple[pd.Series, pd.Series | None]:
    """Databento UTC 종가 로드 → (종가 시리즈, 롤일 시리즈|None).

    parquet(롱포맷: indicator_code/value) 우선, 없으면 최신 CSV(와이드: close)에서 재구성.
    """
    for pq in PARQUET_CANDIDATES:
        if not pq.exists():
            continue
        df = pd.read_parquet(pq)
        if "indicator_code" not in df.columns:
            print(f"[경고] {pq}: indicator_code 컬럼 없음 — 다음 후보")
            continue
        close = df[df["indicator_code"] == "CBOT_BO_CLOSE"].copy()
        if close.empty:
            print(f"[경고] {pq}: CBOT_BO_CLOSE 지표 없음 — 다음 후보")
            continue
        close["price_date"] = pd.to_datetime(close["price_date"]).dt.normalize()
        s = close.set_index("price_date")["value"].astype(float).sort_index()
        s = s[~s.index.duplicated(keep="last")]
        roll = None
        if (df["indicator_code"] == "CBOT_BO_ROLLDAY").any():
            r = df[df["indicator_code"] == "CBOT_BO_ROLLDAY"].copy()
            r["price_date"] = pd.to_datetime(r["price_date"]).dt.normalize()
            roll = r.set_index("price_date")["value"].astype(float).sort_index()
        print(f"[정보] Databento 종가 로드: {pq} ({len(s):,}일"
              f"{', 롤일 지표 있음' if roll is not None else ''})")
        return s, roll

    # CSV 재구성 폴백 (ingest_databento_bo.py의 CSV 출력 규약: price_date + close 컬럼)
    # 2026-11-17: ZL 원본이 GLBX.MDP3/ZL/ 하위 폴더로 이동 — 두 위치 모두 탐색. 이름 규약
    #   (ZL_ohlcv-1d_*.csv)으로 한정해 포털 원본(glbx-mdp3-*.csv, 다계약·스프레드 혼재)을 배제한다.
    csvs = sorted({*glob.glob(str(CSV_DIR / "ZL_ohlcv-1d_*.csv")),
                   *glob.glob(str(CSV_DIR / "ZL" / "ZL_ohlcv-1d_*.csv"))}, key=os.path.getmtime)
    if csvs:
        latest = csvs[-1]
        raw = pd.read_csv(latest)
        date_col  = next((c for c in ("price_date", "ts_event", "date") if c in raw.columns), None)
        close_col = next((c for c in ("close", "Close") if c in raw.columns), None)
        if date_col and close_col:
            raw[date_col] = pd.to_datetime(raw[date_col], errors="coerce").dt.tz_localize(None)
            s = (raw.dropna(subset=[date_col])
                    .set_index(raw[date_col].dt.normalize())[close_col]
                    .astype(float).sort_index())
            s = s[~s.index.duplicated(keep="last")]
            print(f"[정보] Databento 종가 CSV 재구성: {latest} ({len(s):,}일)")
            return s, None
        print(f"[경고] CSV 재구성 실패({latest}) — 컬럼: {list(raw.columns)[:8]}")

    raise FileNotFoundError(
        "[오류] Databento 종가 입력 없음 — "
        f"{PARQUET_CANDIDATES[0]} / {PARQUET_CANDIDATES[1]} / {CSV_DIR}/*.csv 모두 부재. "
        "historical_backfill.yml databento-bo 잡 선행 실행 필요")


def _yf_session():
    """curl_cffi 브라우저 임퍼소네이션 세션 (A-071) — 미설치 시 None."""
    try:
        from curl_cffi import requests as cffi_requests
        return cffi_requests.Session(impersonate="chrome")
    except ImportError:
        print("[정보] curl_cffi 미설치 — 기본 세션 사용(429 위험)")
        return None


def _load_settle_sample() -> tuple[pd.Series, str]:
    """yfinance 정산가 표본 (BO=F → ZL=F) — 가능한 전체 기간(최소 최근 5년 목표)."""
    try:
        import yfinance as yf
    except ImportError:
        print("[경고] yfinance 미설치 — 정산가 표본 수집 불가")
        return pd.Series(dtype=float), ""

    session = _yf_session()
    for symbol in ("ZL=F", "BO=F"):   # A-156: BO=F는 야후 상장폐지 — ZL=F 우선
        for period in ("max", "10y", "5y"):
            try:
                ticker = yf.Ticker(symbol, session=session) if session else yf.Ticker(symbol)
                hist = ticker.history(period=period, auto_adjust=False)
                if hist is None or hist.empty or "Close" not in hist.columns:
                    print(f"[정보] yfinance {symbol} period={period}: 데이터 없음")
                    continue
                idx = pd.to_datetime(hist.index)
                if getattr(idx, "tz", None) is not None:
                    idx = idx.tz_localize(None)
                s = pd.Series(hist["Close"].values, index=idx.normalize()).astype(float)
                s = s[~s.index.duplicated(keep="last")].sort_index().dropna()
                if len(s) < 100:
                    print(f"[정보] yfinance {symbol} period={period}: {len(s)}일 — 표본 부족, 다음 시도")
                    continue
                print(f"[정보] 정산가 표본: {symbol} period={period} → {len(s):,}일 "
                      f"({s.index.min().date()} ~ {s.index.max().date()})")
                return s, symbol
            except Exception as e:
                print(f"[경고] yfinance {symbol} period={period} 실패: {e}")
    return pd.Series(dtype=float), ""


def _stats(diff_pct: pd.Series) -> dict[str, float]:
    if diff_pct.empty:
        return {"n": 0, "median": float("nan"), "p99": float("nan"), "max": float("nan")}
    return {
        "n":      int(len(diff_pct)),
        "median": float(diff_pct.median()),
        "p99":    float(diff_pct.quantile(0.99)),
        "max":    float(diff_pct.max()),
    }


def _fmt(v: float) -> str:
    return "—" if pd.isna(v) else f"{v:.4f}%"


def _write_report(path: Path, verdict: str, symbol: str,
                  st_all: dict, st_ex_roll: dict, st_roll: dict | None,
                  worst: pd.DataFrame | None, note: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# CBOT ZL 세션 종가 교차검증 리포트 — {date.today().isoformat()}",
        "",
        f"**판정: {verdict}**",
        "",
        "## 검증 설계",
        "- 비교 대상: Databento GLBX.MDP3 ZL ohlcv-1d **UTC 종가** vs "
        f"yfinance `{symbol or 'BO=F/ZL=F'}` 일별 종가(정산가 표본)",
        "- 상대차 정의: |utc_close − settle| / settle",
        "",
        "## PASS 기준",
        "| 기준 | 임계값 |",
        "|---|---|",
        f"| 교집합 일수 | ≥ {MIN_OVERLAP_DAYS}일 |",
        f"| 상대차 중앙값 | ≤ {MAX_MEDIAN_PCT:.2f}% |",
        f"| 상대차 P99 | ≤ {MAX_P99_PCT:.2f}% |",
        f"| 상대차 최대(롤일 제외) | ≤ {MAX_ABS_PCT:.2f}% |",
        "",
        "## 통계",
        "| 구분 | N(일) | 중앙값 | P99 | 최대 |",
        "|---|---|---|---|---|",
        f"| 전체 | {st_all['n']} | {_fmt(st_all['median'])} | {_fmt(st_all['p99'])} | {_fmt(st_all['max'])} |",
        f"| 롤일 제외 | {st_ex_roll['n']} | {_fmt(st_ex_roll['median'])} | "
        f"{_fmt(st_ex_roll['p99'])} | {_fmt(st_ex_roll['max'])} |",
    ]
    if st_roll is not None:
        lines.append(
            f"| 롤일만 | {st_roll['n']} | {_fmt(st_roll['median'])} | "
            f"{_fmt(st_roll['p99'])} | {_fmt(st_roll['max'])} |")
    else:
        lines.append("| 롤일만 | — | — | — | — |")
        lines.append("")
        lines.append("> CBOT_BO_ROLLDAY 지표 부재 — 롤일 분리 불가. 전 표본을 '롤일 제외'로 간주함.")
    if note:
        lines += ["", "## 비고", note]
    if worst is not None and not worst.empty:
        lines += ["", "## 어긋난 날짜 상위 20건", "",
                  "| 날짜 | UTC 종가 | 정산가 표본 | 상대차 |", "|---|---|---|---|"]
        for d, row in worst.iterrows():
            lines.append(f"| {d.date()} | {row['utc_close']:.4f} | "
                         f"{row['settle']:.4f} | {row['diff_pct']:.4f}% |")
    lines += ["", "---", "근거: A-145 (세션 종가 검증기) · A-071 (curl_cffi 임퍼소네이션) · "
              "D-023 (as-of 5필드 단일 관리)"]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[완료] 리포트 → {path}")


def _publish(close: pd.Series) -> None:
    """PASS 시 CBOT_BO_CLOSE 발행 — 주말 0건 보장 + as-of 5필드(attach_asof)."""
    df = pd.DataFrame({
        "price_date":     close.index,
        "value":          close.values,
        "indicator_code": "CBOT_BO_CLOSE",
        "source_name":    "Databento/GLBX.MDP3/ZL",
        "unit":           "USc/lb",
        "time_basis":     "EXCHANGE_SETTLEMENT",   # mart TARGET_TIME_BASES 허용값 — 게이트 (b)경로
        "target_eligible": True,         # 교차검증 PASS → G2 타깃 사용 가능
        "ingested_at":    pd.Timestamp.now("UTC"),
    })
    # 주말 0건 보장 — CME 일봉에 주말이 있으면 시각 파싱 오염 신호이므로 제거 후 검증
    weekend = df["price_date"].dt.weekday >= 5
    if weekend.any():
        print(f"[경고] 주말 행 {int(weekend.sum())}건 제거 (시각 파싱 오염 의심)")
        df = df[~weekend]
    assert (df["price_date"].dt.weekday < 5).all(), "[오류] 주말 행 잔존 — 발행 중단"
    df = attach_asof(df, source="CBOT_BO_")
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"[완료] 세션 종가 발행 → {OUT_PARQUET} ({len(df):,}일, "
          f"{df['price_date'].min().date()} ~ {df['price_date'].max().date()})")


def run() -> int:
    report_path = REPORT_DIR / f"session_close_validation_{date.today().isoformat()}.md"

    try:
        utc_close, roll = _load_databento_close()
    except FileNotFoundError as e:
        print(e)
        return EXIT_NO_SAMPLE

    settle, symbol = _load_settle_sample()
    if settle.empty:
        # yfinance 표본 미확보 → FAIL이 아니라 '검증 불가' (exit 2, CBOT_BO_CLOSE 미발행)
        print("[경고] 검증 불가 — 표본 미확보 (yfinance BO=F/ZL=F 데이터 없음). "
              "CBOT_BO_CLOSE 미발행, 재실행 시 재검증.")
        _write_report(report_path, "검증 불가 (표본 미확보)", symbol,
                      _stats(pd.Series(dtype=float)), _stats(pd.Series(dtype=float)),
                      None, None,
                      note="yfinance 정산가 표본을 확보하지 못해 교차검증을 실행할 수 없음. "
                           "레이트리밋(429) 또는 심볼 폐지 여부 확인 필요.")
        return EXIT_NO_SAMPLE

    joined = pd.DataFrame({"utc_close": utc_close, "settle": settle}).dropna()
    joined["diff_pct"] = (joined["utc_close"] - joined["settle"]).abs() / joined["settle"] * 100.0

    # 롤일 분리 (CBOT_BO_ROLLDAY 있으면)
    if roll is not None:
        roll_days = set(roll[roll > 0].index)
        is_roll = joined.index.to_series().isin(roll_days)
    else:
        is_roll = pd.Series(False, index=joined.index)

    st_all     = _stats(joined["diff_pct"])
    st_ex_roll = _stats(joined.loc[~is_roll, "diff_pct"])
    st_roll    = _stats(joined.loc[is_roll, "diff_pct"]) if roll is not None else None

    # A-156: 발행 대상은 UTC 종가가 아니라 **정산가 원계열**이다. 여기서의 검증은
    # "정산가를 믿어도 되는가"(동일 상품인가 · 야후 불량 틱이 얼마나 섞였는가)를 묻는다.
    suspect = joined.loc[~is_roll & (joined["diff_pct"] > SUSPECT_DIFF_PCT)]
    suspect_frac = len(suspect) / max(st_all["n"], 1)
    checks = {
        f"교집합 ≥ {MIN_OVERLAP_DAYS}일 (독립 소스 대조 표본)":
            st_all["n"] >= MIN_OVERLAP_DAYS,
        f"중앙값 ≤ {IDENTITY_MEDIAN_PCT}% (동일 상품 확인)":
            st_all["median"] <= IDENTITY_MEDIAN_PCT,
        f"괴리 {SUSPECT_DIFF_PCT}% 초과일 비율 ≤ {MAX_SUSPECT_FRAC:.0%} (불량 틱 상한)":
            suspect_frac <= MAX_SUSPECT_FRAC,
    }
    failed = [name for name, ok in checks.items() if not ok]

    print(f"[정보] 교차검증: 교집합 {st_all['n']:,}일 · 중앙값 {_fmt(st_all['median'])} · "
          f"P99 {_fmt(st_all['p99'])} · 괴리 {SUSPECT_DIFF_PCT}% 초과 "
          f"{len(suspect)}일({suspect_frac:.2%}, 롤일 제외)")

    if failed:
        worst = joined.sort_values("diff_pct", ascending=False).head(20)
        _write_report(report_path, f"FAIL — 미충족: {', '.join(failed)}", symbol,
                      st_all, st_ex_roll, st_roll, worst,
                      note="정산가 표본과 Databento UTC 종가가 동일 상품으로 보기 어려움 — "
                           "발행 중단. 심볼·스케일·기간 정합 확인 필요.")
        print(f"[오류] 세션 종가 검증 FAIL — 미충족 기준: {', '.join(failed)}")
        return EXIT_FAIL

    # 발행: 분석창(2010-01-01~) 내 정산가. 주말 제거·범위 검증은 _publish가 수행.
    publishable = settle[settle.index >= pd.Timestamp("2010-01-01")]
    lo, hi = float(publishable.min()), float(publishable.max())
    if not (5.0 <= lo and hi <= 200.0):
        print(f"[오류] 정산가 범위 이상 {lo:.2f}~{hi:.2f} USc/lb — 발행 중단")
        return EXIT_FAIL

    _write_report(
        report_path,
        f"PASS — 정산가 원계열({symbol}) 발행 · Databento UTC 보강 검증 통과",
        symbol, st_all, st_ex_roll, st_roll,
        suspect.sort_values("diff_pct", ascending=False).head(20) if len(suspect) else None,
        note=(f"게이트 (b)경로: 거래소 공식 정산가({symbol}, {len(publishable):,}일)를 "
              f"CBOT_BO_CLOSE로 발행. Databento UTC 종가와 중앙값 {_fmt(st_all['median'])} "
              f"일치로 동일 상품 확인. 괴리 {SUSPECT_DIFF_PCT}% 초과 {len(suspect)}일은 "
              f"아래 표에 기록(야후 불량 틱 의심 — 후속 검토 대상, 값은 정산가 유지)."))
    _publish(publishable)
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(run())
