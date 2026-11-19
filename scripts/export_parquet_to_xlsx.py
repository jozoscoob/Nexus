#!/usr/bin/env python3
"""
수집 데이터(parquet) → .xlsx 자동 변환·보관 (WBS 1.1.46 · A-064)

목적(조정자 요청): 등록 API 데이터 + Perplexity 수집 데이터를 모두 .xlsx로 변환·저장해
      비개발 이해관계자가 열람 가능하게 함. 히스토리·실시간을 분리 보관.

입력: data/raw/**/*.parquet (커넥터·인제스터 산출물)
출력: data/raw/xlsx_exports/
        historical/{name}.xlsx   — 백필/수동 히스토리 (파일명에 historical|_hist 포함)
        realtime/{name}.xlsx     — 일별 실시간 커넥터 산출물 (그 외)
      각 xlsx는 indicator_code별 시트 분리(≤10종) 또는 단일 'data' 시트.

성격: 열람·감사용 사본. 분석 파이프라인의 소스는 여전히 parquet (CLAUDE.md §2).
      xlsx는 openpyxl write 예외 허용(산출물 export 용도, 입력 파이프라인 아님).

의존성: pandas >= 2.0 · openpyxl · pyarrow
"""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

RAW_ROOT   = Path("data/raw")
EXPORT_DIR = RAW_ROOT / "xlsx_exports"
_HIST_HINT = ("historical", "_hist", "gain_", "fao_amis", "te_commodities", "ice_monthly")
_MAX_SHEETS = 10          # indicator_code별 시트 분리 상한
_MAX_ROWS_PER_SHEET = 1_000_000  # xlsx 시트 한계 방지


def _is_historical(name: str) -> bool:
    low = name.lower()
    return any(h in low for h in _HIST_HINT)


def _safe_sheet(name: str) -> str:
    """엑셀 시트명 제약(31자·특수문자) 정리."""
    bad = ':\\/?*[]'
    for ch in bad:
        name = name.replace(ch, "_")
    return name[:31] or "data"


def _strip_tz(df: pd.DataFrame) -> pd.DataFrame:
    """엑셀은 tz-aware datetime 미지원 → 모든 datetime 컬럼을 tz-naive로 변환."""
    df = df.copy()
    for col in df.columns:
        s = df[col]
        if isinstance(s.dtype, pd.DatetimeTZDtype):
            df[col] = s.dt.tz_localize(None)
    return df


def _write_xlsx(df: pd.DataFrame, out_path: Path) -> None:
    df = _strip_tz(df)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        if "indicator_code" in df.columns and 1 < df["indicator_code"].nunique() <= _MAX_SHEETS:
            for code, g in df.groupby("indicator_code"):
                g.head(_MAX_ROWS_PER_SHEET).to_excel(
                    writer, sheet_name=_safe_sheet(str(code)), index=False)
        else:
            df.head(_MAX_ROWS_PER_SHEET).to_excel(writer, sheet_name="data", index=False)


def run() -> None:
    parquets = sorted(set(glob.glob(f"{RAW_ROOT}/**/*.parquet", recursive=True)))
    if not parquets:
        print("[정보] 변환할 parquet 없음.")
        return
    hist = rt = 0
    for p in parquets:
        name = Path(p).stem
        try:
            df = pd.read_parquet(p)
        except Exception as e:
            print(f"  [경고] 로드 실패 {name}: {e}")
            continue
        if df.empty:
            continue
        bucket = "historical" if _is_historical(name) else "realtime"
        out = EXPORT_DIR / bucket / f"{name}.xlsx"
        try:
            _write_xlsx(df, out)
            if bucket == "historical":
                hist += 1
            else:
                rt += 1
            print(f"  [xlsx] {bucket}/{name}.xlsx  ({len(df):,}행)")
        except Exception as e:
            print(f"  [경고] 변환 실패 {name}: {e}")

    print(f"\n[완료] xlsx 변환 → {EXPORT_DIR}/  (historical {hist} · realtime {rt})")


if __name__ == "__main__":
    run()
