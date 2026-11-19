"""
데이터 내보내기 유틸리티 — WBS 1.1.22
수집된 parquet 파일 → Excel (.xlsx) 변환 (다운로드·보고용)

실행: python src/pipeline/export_data.py [--source data/raw] [--output data/exports]
GitHub Actions에서 pipeline-summary / backfill-summary 단계 이후 자동 실행됨.

설계 원칙:
  - 저장소 parquet이 파이프라인의 단일 소스. 이 스크립트는 보고/다운로드 전용 내보내기.
  - data/exports/ 는 .gitignore에 포함 (data/raw/ 와 동일 규칙)
  - 시트 구성: 파일별 개별 시트 + 'SUMMARY' 시트
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import pandas as pd

DEFAULT_SOURCE = "data/raw"
DEFAULT_OUTPUT = "data/exports"
MAX_ROWS_PER_SHEET = 1_000_000  # Excel 행 한도: 1,048,576


def _to_excel_safe(df: pd.DataFrame, max_rows: int = MAX_ROWS_PER_SHEET) -> pd.DataFrame:
    """Excel 안전 형식으로 변환: datetime timezone 제거, 행 수 제한."""
    df = df.copy()
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)
    if len(df) > max_rows:
        print(f"[경고] 행 수 {len(df):,} > Excel 한도 {max_rows:,} — 최신 {max_rows:,}행만 내보냄")
        df = df.tail(max_rows)
    return df


def export_all(source_dir: str = DEFAULT_SOURCE, output_dir: str = DEFAULT_OUTPUT) -> list[str]:
    """source_dir의 모든 parquet → output_dir의 Excel 개별 파일 + 통합 파일.

    Returns:
        생성된 Excel 파일 경로 목록
    """
    os.makedirs(output_dir, exist_ok=True)
    files = sorted(
        glob.glob(f"{source_dir}/**/*.parquet", recursive=True)
        + glob.glob(f"{source_dir}/*.parquet")
    )

    if not files:
        print(f"[경고] {source_dir}에서 parquet 파일 없음 — Excel 내보내기 건너뜀")
        return []

    created: list[str] = []
    summary_rows: list[dict] = []

    # ── 파일별 개별 Excel 내보내기 ────────────────────────────────────────────
    for f in files:
        stem = Path(f).stem
        out_path = f"{output_dir}/{stem}.xlsx"
        try:
            df = pd.read_parquet(f)
            df_safe = _to_excel_safe(df)
            df_safe.to_excel(out_path, index=False, engine="openpyxl")
            size_kb = os.path.getsize(out_path) / 1024
            print(f"[완료] {stem}.xlsx ({len(df_safe):,}행, {size_kb:.1f}KB) → {out_path}")
            created.append(out_path)
            summary_rows.append({
                "파일명": Path(f).name,
                "행 수": len(df),
                "컬럼 수": len(df.columns),
                "크기 (KB)": round(size_kb, 1),
                "수집 시각": str(df["ingested_at"].max())[:19] if "ingested_at" in df.columns else "N/A",
                "상태": "OK",
            })
        except Exception as e:
            print(f"[오류] {stem} Excel 변환 실패: {e}")
            summary_rows.append({
                "파일명": Path(f).name, "행 수": "–", "컬럼 수": "–",
                "크기 (KB)": "–", "수집 시각": "–", "상태": f"오류: {e}",
            })

    # ── 통합 Excel (시트별 커넥터) ────────────────────────────────────────────
    combined_path = f"{output_dir}/nexus_all_data.xlsx"
    try:
        with pd.ExcelWriter(combined_path, engine="openpyxl") as writer:
            # SUMMARY 시트 (첫 번째)
            summary_df = pd.DataFrame(summary_rows)
            summary_df.to_excel(writer, sheet_name="SUMMARY", index=False)

            for f in files:
                stem = Path(f).stem
                # Excel 시트명 최대 31자 제한
                sheet_name = stem[:31] if len(stem) > 31 else stem
                try:
                    df = pd.read_parquet(f)
                    _to_excel_safe(df).to_excel(writer, sheet_name=sheet_name, index=False)
                except Exception as e:
                    pd.DataFrame({"오류": [str(e)]}).to_excel(
                        writer, sheet_name=sheet_name, index=False
                    )

        size_kb = os.path.getsize(combined_path) / 1024
        print(f"[완료] 통합 Excel {size_kb:.0f}KB ({len(files)}개 시트) → {combined_path}")
        created.append(combined_path)
    except Exception as e:
        print(f"[오류] 통합 Excel 생성 실패: {e}")

    print(f"\n[완료] Excel 내보내기: {len(created)}개 파일 → {output_dir}/")
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexus parquet → Excel 내보내기")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="parquet 소스 디렉터리")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Excel 출력 디렉터리")
    args = parser.parse_args()
    export_all(source_dir=args.source, output_dir=args.output)


if __name__ == "__main__":
    main()
