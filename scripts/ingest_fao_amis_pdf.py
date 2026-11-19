#!/usr/bin/env python3
"""
FAO AMIS Market Monitor PDF 수집 스크립트

입력: data/raw/FAO/AMIS/*.pdf
출력: data/raw/fao_amis_historical.parquet

파일 명명 규칙:
  {YY}년 {MM}월_Market Monitor Issue.pdf
  예: "17년 10월_Market Monitor Issue.pdf" → 2017-10-01

수집 지표:
  FAO_VEGEOIL_PRICE_IDX    : FAO 식물성유지 가격지수 (2014-16=100)
  FAO_AMIS_VEGEOIL_PRODUCTION : 전세계 식물성유지 생산량 (100만 MT)
  FAO_AMIS_VEGEOIL_CONSUMPTION: 전세계 식물성유지 소비량 (100만 MT)
  FAO_AMIS_VEGEOIL_STOCKS  : 전세계 식물성유지 기말재고 (100만 MT)
  FAO_AMIS_VEGEOIL_STU     : 식물성유지 재고사용비율 (%)
  FAO_AMIS_SOY_PRODUCTION  : 전세계 대두 생산량 (100만 MT)
  FAO_AMIS_SOY_STOCKS      : 전세계 대두 기말재고 (100만 MT)
  FAO_AMIS_SOY_STU         : 대두 재고사용비율 (%)

의존성:
  pdfplumber >= 0.9 (또는 pypdf >= 3.0)
  pandas >= 2.0

D-016: FAO AMIS 통합 우선순위 (2026-06-17)
D-017: 파이프라인 통합 방식 (2026-06-17)
"""
from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

# A-153: "Could not get FontBBox..."는 pdfminer(pdfplumber 백엔드)의 손상 폰트
#        디스크립터 경고 — 추출 자체는 진행됨, 로그 폭주만 차단.
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from src.pipeline.asof import attach_asof  # noqa: E402

AMIS_DIR   = Path("data/raw/FAO/AMIS")
OUTPUT_DIR = Path("data/raw")

_YEAR_MONTH_RE = re.compile(r"^(\d{2})년\s+(\d{1,2})월")

# 지표명 → 코드 매핑 (보고서 내 영문 키워드 기준)
_VEGEOIL_KEYWORD_MAP: dict[str, str] = {
    r"vegetable\s+oil\s+price\s+index":          "FAO_VEGEOIL_PRICE_IDX",
    r"vegeoil\s+price":                          "FAO_VEGEOIL_PRICE_IDX",
    r"food\s+price\s+index.*?oils":              "FAO_VEGEOIL_PRICE_IDX",
}

# 식물성유지 S&D 테이블 행 키워드
_VEGEOIL_SD_ROWS: dict[str, str] = {
    r"production":    "FAO_AMIS_VEGEOIL_PRODUCTION",
    r"consumption|utilization|use": "FAO_AMIS_VEGEOIL_CONSUMPTION",
    r"closing\s+stock|ending\s+stock|stocks": "FAO_AMIS_VEGEOIL_STOCKS",
    r"stock.?to.?use":                        "FAO_AMIS_VEGEOIL_STU",
}

# 대두 Oilcrops S&D 테이블 행 키워드
_SOY_SD_ROWS: dict[str, str] = {
    r"production":    "FAO_AMIS_SOY_PRODUCTION",
    r"closing\s+stock|ending\s+stock|stocks": "FAO_AMIS_SOY_STOCKS",
    r"stock.?to.?use":                        "FAO_AMIS_SOY_STU",
}

# 가장 최근 연도 열 추출용 패턴 (예: "2024/25", "2025")
_YEAR_COL_RE = re.compile(r"\b(20\d{2})(?:/\d{2})?\b")


def _year_month_from_filename(fname: str) -> Optional[tuple[int, int]]:
    """파일명 → (year, month). 예: '17년 10월_...' → (2017, 10)."""
    m = _YEAR_MONTH_RE.match(fname)
    if not m:
        return None
    yy, mm = int(m.group(1)), int(m.group(2))
    return (2000 + yy, mm)


def _extract_text(pdf_path: Path) -> str:
    """PDF 텍스트 추출 (pdfplumber 우선, fallback: pypdf)."""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except ImportError:
        pass

    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
    except ImportError:
        raise RuntimeError(
            "[오류] PDF 파싱 라이브러리 없음. pdfplumber 또는 pypdf를 설치하세요. "
            "러너 컨테이너: pip install pdfplumber 또는 pypdf"
        )


def _find_number_after_keyword(text: str, keyword_re: str) -> Optional[float]:
    """텍스트에서 키워드 다음에 나오는 첫 번째 숫자 추출."""
    pattern = keyword_re + r"[^\n]{0,120}?([\d,]+\.?\d*)"
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if m:
        raw = m.group(1).replace(",", "")
        try:
            return float(raw)
        except ValueError:
            pass
    return None


def _extract_sd_table_value(
    text: str,
    section_keywords: list[str],
    row_map: dict[str, str],
    latest_year: Optional[int] = None,
) -> dict[str, float]:
    """
    S&D 테이블 섹션 탐색 → 행별 최신 연도 수치 추출.

    section_keywords: 해당 섹션 시작을 표시하는 키워드 목록
    row_map: {행 키워드 regex → 지표 코드}
    latest_year: 보고서의 최신 마케팅연도 (None이면 자동 탐지)
    """
    results: dict[str, float] = {}

    # 섹션 위치 찾기
    section_start = -1
    for kw in section_keywords:
        idx = text.lower().find(kw.lower())
        if idx != -1:
            section_start = idx
            break

    if section_start == -1:
        return results

    # 섹션에서 500자 추출 (테이블 범위 근사)
    section_text = text[section_start : section_start + 800]

    # 최신 연도 탐지 (없으면 보고서 연도 기준)
    if latest_year is None:
        years_found = _YEAR_COL_RE.findall(section_text)
        if years_found:
            latest_year = max(int(y) for y in years_found)

    for row_re, indicator_code in row_map.items():
        val = _find_number_after_keyword(section_text, row_re)
        if val is not None:
            results[indicator_code] = val

    return results


def _extract_vegeoil_price_index(text: str) -> Optional[float]:
    """FAO Vegetable Oil Price Index 추출."""
    patterns = [
        r"vegetable\s+oil[s]?\s+price\s+index[^\n]{0,80}?([\d,]+\.?\d*)",
        r"oils\s+&\s+fats[^\n]{0,80}?([\d,]+\.?\d*)",
        r"oils\s+and\s+fats[^\n]{0,80}?([\d,]+\.?\d*)",
        r"food\s+price\s+index.*?oils[^\n]{0,120}?([\d,]+\.?\d*)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                v = float(raw)
                # 합리적 범위 필터 (지수 값: 50–300)
                if 50 <= v <= 300:
                    return v
            except ValueError:
                continue
    return None


def parse_amis_file(pdf_path: Path) -> pd.DataFrame:
    """단일 FAO AMIS PDF → 정규화 DataFrame."""
    ym = _year_month_from_filename(pdf_path.name)
    if ym is None:
        print(f"  [건너뜀] 날짜 파싱 실패: {pdf_path.name}")
        return pd.DataFrame()

    year, month = ym
    price_date = date(year, month, 1)

    try:
        text = _extract_text(pdf_path)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"[오류] PDF 로드 실패: {pdf_path}: {e}") from e

    if not text.strip():
        print(f"  [경고] 텍스트 추출 빈 결과: {pdf_path.name}")
        return pd.DataFrame()

    records: list[dict] = []
    base = {
        "source_name": "FAO_AMIS_PDF",
        "ingested_at": pd.Timestamp.utcnow(),
        "note":        pdf_path.name,
    }

    # 1. FAO Vegetable Oil Price Index
    price_idx = _extract_vegeoil_price_index(text)
    if price_idx is not None:
        records.append({
            **base,
            "price_date":     price_date,
            "indicator_code": "FAO_VEGEOIL_PRICE_IDX",
            "value":          price_idx,
            "unit":           "index_2014_16_100",
        })

    # 2. Vegetable Oils S&D 테이블
    vegeoil_section_kws = [
        "vegetable oils supply and demand",
        "vegetable oils s&d",
        "oils & fats",
        "oilseed products",
    ]
    vegeoil_vals = _extract_sd_table_value(
        text, vegeoil_section_kws, _VEGEOIL_SD_ROWS, latest_year=year
    )
    for code, val in vegeoil_vals.items():
        unit = "percent" if "STU" in code else "million_MT"
        records.append({
            **base,
            "price_date":     price_date,
            "indicator_code": code,
            "value":          val,
            "unit":           unit,
        })

    # 3. Oilcrops (대두) S&D 테이블
    soy_section_kws = [
        "soybeans supply and demand",
        "oilcrops supply",
        "soybean s&d",
    ]
    soy_vals = _extract_sd_table_value(
        text, soy_section_kws, _SOY_SD_ROWS, latest_year=year
    )
    for code, val in soy_vals.items():
        unit = "percent" if "STU" in code else "million_MT"
        records.append({
            **base,
            "price_date":     price_date,
            "indicator_code": code,
            "value":          val,
            "unit":           unit,
        })

    return pd.DataFrame(records)


def run(
    amis_dir: Path = AMIS_DIR,
    output_dir: Path = OUTPUT_DIR,
    ffill_missing_months: bool = True,
) -> None:
    """전체 FAO AMIS PDF 수집·정규화·저장."""
    # A-135: 재정리 후 PDF는 AMIS/{YYYY}/ 하위에 있다 — 비재귀 glob은 0건을 찾고도
#   exit 0으로 끝나 3중(스크립트·사전체크·warn 업로드)으로 조용히 실패했다.
#   A-083(GAIN)·D-027(ICE)과 동일한 버그 유형. 재귀 + 0건 시 실패로 전환.
    pdf_files = sorted(amis_dir.rglob("*.pdf"))
    if not pdf_files:
        print(f"[오류] {amis_dir}에 PDF 파일 없음.")
        raise SystemExit(1)   # A-135: 0건을 성공으로 위장하지 않는다

    print(f"[C-03] FAO AMIS PDF {len(pdf_files)}개 파싱 시작...")
    all_frames: list[pd.DataFrame] = []

    for f in pdf_files:
        print(f"  처리 중: {f.name}")
        try:
            df = parse_amis_file(f)
            if not df.empty:
                all_frames.append(df)
                print(f"    → {len(df)}건 추출")
            else:
                print("    → 0건 (건너뜀)")
        except Exception as e:
            print(f"    [오류] {f.name}: {e}")

    if not all_frames:
        print("[경고] 추출된 데이터 없음. pdfplumber/pypdf 설치 여부를 확인하세요.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    combined = combined.sort_values(["price_date", "indicator_code"]).reset_index(drop=True)

    # 누락 월 forward fill (1월·8월 보완)
    if ffill_missing_months:
        combined = _fill_missing_months(combined)

    out_path = output_dir / "fao_amis_historical.parquet"
    output_dir.mkdir(parents=True, exist_ok=True)
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="FAO_AMIS")
    combined.to_parquet(out_path, index=False)

    print(f"\n[완료] {len(combined)}건 → {out_path}")
    print(f"  기간: {combined['price_date'].min()} ~ {combined['price_date'].max()}")
    print(f"  지표: {sorted(combined['indicator_code'].unique())}")


def _fill_missing_months(df: pd.DataFrame) -> pd.DataFrame:
    """1월·8월 누락 월 데이터를 전월 forward fill (limit=1)."""
    if df.empty:
        return df

    indicators = df["indicator_code"].unique()
    date_min = df["price_date"].min()
    date_max = df["price_date"].max()

    # 월별 전체 날짜 범위 생성
    all_months = pd.date_range(
        start=pd.Timestamp(date_min),
        end=pd.Timestamp(date_max),
        freq="MS",
    )

    filled_frames = []
    for indicator in indicators:
        sub = df[df["indicator_code"] == indicator].copy()
        sub["price_date"] = pd.to_datetime(sub["price_date"])
        sub = sub.set_index("price_date").reindex(all_months)
        sub["indicator_code"] = indicator
        # 메타 컬럼 forward fill (source_name, unit 등)
        for col in ["source_name", "unit", "ingested_at", "note"]:
            if col in sub.columns:
                sub[col] = sub[col].ffill()
        # 수치 forward fill, limit=1 (2개월 이상 연속 결측은 NaN 유지)
        sub["value"] = sub["value"].ffill(limit=1)
        sub = sub.dropna(subset=["value"])
        sub.index.name = "price_date"
        sub = sub.reset_index()
        sub["price_date"] = sub["price_date"].dt.date
        filled_frames.append(sub)

    if not filled_frames:
        return df

    result = pd.concat(filled_frames, ignore_index=True)
    return result.sort_values(["price_date", "indicator_code"]).reset_index(drop=True)


if __name__ == "__main__":
    run()
