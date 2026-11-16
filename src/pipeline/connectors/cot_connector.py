"""CFTC COT 대두유 포지션 수집 (G2 변동성 선행축 — R-043 B-9).

원천: CFTC Disaggregated Futures-Only (Socrata 72hh-3qpy, 키 불필요), 시장 코드 007601(CBOT 대두유).
기준일=화요일 포지션, 공개=금요일 15:30 ET(ZL 마감 이후) → as-of 규칙 COT_(lag_days=7, 연휴 지연 포함 보수 적용).
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import httpx
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

COT_URL = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
SBO_MARKET_CODE = "007601"
OUTPUT_DIR = "data/raw"
ROW_LIMIT = 50000
# (원천 컬럼 long, short) → 순포지션 지표 접미사
NET_PAIRS = {
    "MM": ("m_money_positions_long_all", "m_money_positions_short_all"),
    "PROD": ("prod_merc_positions_long", "prod_merc_positions_short"),
    "SWAP": ("swap_positions_long_all", "swap__positions_short_all"),
}


def fetch_cot(start_year: int) -> pd.DataFrame:
    params = {"cftc_contract_market_code": SBO_MARKET_CODE, "$limit": ROW_LIMIT,
              "$where": f"report_date_as_yyyy_mm_dd >= '{start_year}-01-01'",
              "$order": "report_date_as_yyyy_mm_dd"}
    r = httpx.get(COT_URL, params=params, timeout=60)
    r.raise_for_status()
    return pd.DataFrame(r.json())


def to_long(raw: pd.DataFrame) -> pd.DataFrame:
    cols = ["open_interest_all"] + [c for pair in NET_PAIRS.values() for c in pair]
    missing = [c for c in cols if c not in raw.columns]
    if missing:
        raise ValueError(f"[오류] COT 응답 컬럼 누락: {missing} — 원천 스키마 변경 확인 필요")
    w = pd.DataFrame({"price_date": pd.to_datetime(raw["report_date_as_yyyy_mm_dd"]).dt.normalize()})
    num = raw[cols].apply(pd.to_numeric, errors="coerce")
    w["COT_SBO_OI"] = num["open_interest_all"]
    for k, (lo, sh) in NET_PAIRS.items():
        w[f"COT_SBO_{k}_LONG"] = num[lo]
        w[f"COT_SBO_{k}_SHORT"] = num[sh]
        w[f"COT_SBO_{k}_NET"] = num[lo] - num[sh]
    w["COT_SBO_MM_NET_PCT_OI"] = w["COT_SBO_MM_NET"] / w["COT_SBO_OI"] * 100
    long = w.melt(id_vars="price_date", var_name="indicator_code", value_name="value").dropna()
    long["unit"] = long["indicator_code"].map(lambda c: "% of OI" if c.endswith("PCT_OI") else "contracts")
    long["source_name"] = "CFTC_COT_DISAGG"
    long["ingested_at"] = pd.Timestamp.now("UTC")
    return long


def run() -> None:
    start_year = int(os.environ.get("HISTORICAL_START_YEAR", "2010"))
    raw = fetch_cot(start_year)
    if raw.empty:
        raise SystemExit("[오류] COT 응답 0건 — 시장 코드·네트워크 확인 필요")
    df = attach_asof(to_long(raw), source="CFTC_COT")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = f"{OUTPUT_DIR}/cot_positions_{date.today():%Y%m%d}.parquet"
    df.to_parquet(out, index=False)
    print(f"[완료] COT 대두유 {df['price_date'].nunique()}주 · {len(df)}건 → {out} "
          f"(최신 기준일 {df['price_date'].max():%Y-%m-%d})")


if __name__ == "__main__":
    run()
