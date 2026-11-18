"""
WASDE / USDA 작황 데이터 커넥터 — WBS 1.1.4
수집 대상: WASDE 대두 수급 (USDA FAS OpenData PSD API) · USDA ARMS 생산비용
API 변경 (2025):
  구: https://apps.fas.usda.gov/psdonline/api/psd/exporting  → 404 (폐기)
  신: https://apps.fas.usda.gov/OpenData/api/psd/commodity/{code}/country/all/year/{year}
  인증 방식: 쿼리 파라미터(apiKey) → 요청 헤더(API_KEY)
API 키:
  USDA_FAS_API_KEY  — FAS OpenData 포털(apps.fas.usda.gov/opendatawebV2)에서 발급
  USDA_ARM_API_KEY  — USDA ARMS 생산비용 데이터 (data.ers.usda.gov)
실행 환경: VS Code Web (Azure ML Studio) 또는 GitHub Actions
"""

from __future__ import annotations

import io
import os
import re
import time
import zipfile
from datetime import date

import httpx
import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

OUTPUT_DIR = "data/raw"
# USDA FAS OpenData PSD API (2025 신규 엔드포인트)
FAS_OPENDATA_BASE = "https://apps.fas.usda.gov/OpenData/api/psd"
SBO_COMMODITY_CODE = "2222000"  # Soybean Oil (USDA commodity code)
# USDA ARMS (Agricultural Resource Management Survey)
ARMS_BASE = "https://data.ers.usda.gov/api/Data"


# A-141(a): 전 연도 403의 유력 원인 = 인증 헤더 이름 불일치 (ESR 전례 A-019: X-Api-Key).
#           호스트·시기별로 X-Api-Key / API_KEY / ?api_key= 가 혼재 → 3방식 동시 시도 체인.
_FAS_AUTH_SUCCESS_LOGGED = False


def _fetch_fas(url: str, api_key: str = "", max_retries: int = 2) -> list | dict:
    """USDA FAS OpenData API — 인증 3방식 시도 체인 (A-141a).

    ① 헤더 X-Api-Key (ESR 검증 방식, A-019)
    ② 헤더 API_KEY   (구 OpenData 방식, A-007)
    ③ 쿼리 ?api_key= (최초 방식 폴백)
    성공한 방식은 1회 로그로 남긴다. 401/403이면 다음 방식으로 즉시 전환.
    """
    global _FAS_AUTH_SUCCESS_LOGGED
    if api_key:
        auth_styles: list[tuple[str, dict, dict]] = [
            ("X-Api-Key 헤더", {"X-Api-Key": api_key}, {}),
            ("API_KEY 헤더",   {"API_KEY": api_key},   {}),
            ("api_key 쿼리",   {},                     {"api_key": api_key}),
        ]
    else:
        auth_styles = [("무인증", {}, {})]

    last_error: Exception | None = None
    for style_name, headers, params in auth_styles:
        delay = 2
        for attempt in range(max_retries):
            try:
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                if r.status_code in (401, 403):
                    print(f"[정보] USDA FAS {r.status_code} ({style_name}) — 다음 인증 방식 시도")
                    last_error = httpx.HTTPStatusError(
                        f"{r.status_code}", request=r.request, response=r)
                    break  # 인증 방식 전환 (재시도 무의미)
                r.raise_for_status()
                if not _FAS_AUTH_SUCCESS_LOGGED:
                    print(f"[정보] USDA FAS 인증 성공 방식: {style_name}")
                    _FAS_AUTH_SUCCESS_LOGGED = True
                return r.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                last_error = e
                if attempt == max_retries - 1:
                    break
                time.sleep(delay)
                delay *= 2
    raise RuntimeError(f"[오류] USDA FAS API 호출 실패 (인증 3방식 모두): {last_error}")


def _fetch_arms(params: dict, api_key: str = "", max_retries: int = 4) -> list | dict:
    """USDA ERS ARMS API — 쿼리 파라미터 인증."""
    if api_key:
        params = {**params, "api_key": api_key}
    delay = 2
    for attempt in range(max_retries):
        try:
            # A-246: api.ers 302 리다이렉트를 따라가지 않으면 리다이렉트 본문을 JSON으로
            #        해석하다 예외 → 상위에서 '수집 실패'로 삼켜져 조용히 0건이 됐다.
            r = httpx.get(ARMS_BASE, params=params, timeout=30, follow_redirects=True)
            # A-080: ARMS 404 = 리포트/카테고리 조합 미존재(서비스 정상) → 치명 오류 아님.
            #        생산비용은 분석 보조 지표이므로 경고 후 빈 결과 반환.
            if r.status_code == 404:
                print(f"[경고] USDA ARMS 404 — 해당 리포트 조합 미제공(건너뜀): {params.get('year')}")
                return []
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"[오류] USDA ARMS API 호출 실패: {e}") from e
            time.sleep(delay)
            delay *= 2
    return []


def fetch_wasde_soybean_oil(marketing_year: int | None = None) -> pd.DataFrame:
    """USDA FAS OpenData PSD API에서 대두유(Soybean Oil) 수급 데이터 수집.
    URL: {FAS_OPENDATA_BASE}/commodity/{code}/country/all/year/{year}
    키 이름: USDA_FAS_API_KEY (구: USDA_FAS_PSD_API_KEY 하위 호환 유지)
    """
    year = marketing_year or date.today().year
    # 구 키 이름도 fallback으로 지원 (하위 호환)
    api_key = (
        os.environ.get("USDA_FAS_API_KEY", "")
        or os.environ.get("USDA_FAS_PSD_API_KEY", "")
    )
    # A-076: apps.fas.usda.gov OpenData PSD가 500 반환 — ESR 전례(A-019)와 동일하게
    # api.fas.usda.gov 신규 호스트로 이관된 것으로 추정. 신규 → 구 순서 폴백 체인.
    candidate_urls = [
        f"https://api.fas.usda.gov/api/psd/commodity/{SBO_COMMODITY_CODE}/country/all/year/{year}",
        f"{FAS_OPENDATA_BASE}/commodity/{SBO_COMMODITY_CODE}/country/all/year/{year}",
    ]
    data = None
    for url in candidate_urls:
        try:
            data = _fetch_fas(url, api_key=api_key)
            if data:
                break
        except Exception as e:
            # A-141(c): 구 코드 url.split('/api')[0]이 "https://api.…"를 '/api'에서 잘라
            #           "(https:/)"로 깨져 출력됨 → 호스트만 표기하도록 수정.
            host = httpx.URL(url).host
            print(f"[경고] PSD 엔드포인트 실패({host}): {e} — 다음 후보 시도")
            data = None
    if not data:
        print(f"[경고] USDA FAS PSD: {year}년 대두유 데이터 없음")
        return pd.DataFrame()

    rows = []
    for item in data:
        # FAS OpenData 응답 필드명 (구 API와 다를 수 있음)
        attr_id   = item.get("attributeId") or item.get("attributeName", "UNKNOWN")
        country   = item.get("countryName") or item.get("country", "")
        unit_desc = item.get("unitDescription") or item.get("unitDesc", "1000 MT")
        val       = item.get("value")
        # A-172 후속(11차 잔존 240건): country/all 응답의 65개국이 SBO_{attr} 하나에
        # 충돌 — 국가 축을 코드에 접미. countryCode 우선, 없으면 국가명 축약.
        cc = str(item.get("countryCode") or "").strip()
        suffix = cc or "".join(ch for ch in str(country).upper() if ch.isalpha())[:6] or "UNK"
        rows.append({
            "price_date":     f"{year}-10-01",  # WASDE 마케팅 연도 시작 (10월)
            "source_name":    "USDA_PSD",
            "indicator_code": f"SBO_{attr_id}_{suffix}",
            "country":        country,
            "value":          val,
            "unit":           unit_desc,
        })

    if not rows:
        print(f"[경고] USDA FAS PSD: {year}년 파싱 가능한 레코드 없음")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["value"]      = pd.to_numeric(df["value"], errors="coerce")
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df.dropna(subset=["value"])


def fetch_wasde_multi_year(start_year: int = 2010) -> pd.DataFrame:
    """2020년부터 현재까지 연도별 WASDE PSD 수급 데이터를 일괄 수집."""
    current_year = date.today().year
    frames = []
    for yr in range(start_year, current_year + 1):
        try:
            df = fetch_wasde_soybean_oil(marketing_year=yr)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"[경고] USDA FAS PSD {yr}년 수집 실패: {e}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# A-141(b): API 전 연도 실패(403/500) 대비 — 키 불필요 공개 벌크 CSV 폴백.
#           PSD Online 공식 벌크 다운로드(oilseeds 전 품목·전 연도, 수십 MB zip).
PSD_BULK_ZIP_URL = "https://apps.fas.usda.gov/psdonline/downloads/psd_oilseeds_csv.zip"


def _find_col(cols: list[str], *candidates: str) -> str | None:
    """CSV 실물 컬럼명 유연 탐지 — 대소문자·언더스코어 무시 부분 일치."""
    normalized = {c: c.lower().replace("_", "").replace(" ", "") for c in cols}
    for cand in candidates:
        key = cand.lower().replace("_", "").replace(" ", "")
        for orig, norm in normalized.items():
            if key == norm:
                return orig
    # 부분 일치 폴백
    for cand in candidates:
        key = cand.lower().replace("_", "").replace(" ", "")
        for orig, norm in normalized.items():
            if key in norm:
                return orig
    return None


def fetch_psd_bulk_csv(start_year: int = 2010) -> pd.DataFrame:
    """USDA PSD Online 벌크 CSV(zip) 폴백 — API 키 불필요 (A-141b).

    API가 전 연도 403/500일 때 사용. psd_oilseeds_csv.zip을 스트리밍 다운로드 →
    메모리 해제(zipfile) → 대두 관련 품목(SBO 2222000 + Commodity 설명에 soybean 포함)
    행만 필터 → 기존 지표코드 규약(PSD_ 접두) 롱포맷으로 정규화. 2010~현재 전 연도 커버.
    """
    print(f"[정보] PSD 벌크 CSV 폴백 시작 — {PSD_BULK_ZIP_URL} (수십 MB, 스트리밍)")
    buf = io.BytesIO()
    try:
        # A-246: 벌크 zip은 방금 타임아웃 난 apps.fas와 같은 호스트 — 300s는 무의미한 대기.
        with httpx.stream("GET", PSD_BULK_ZIP_URL, timeout=120,
                          follow_redirects=True) as r:
            r.raise_for_status()
            for chunk in r.iter_bytes():
                buf.write(chunk)
    except Exception as e:
        print(f"[경고] PSD 벌크 zip 다운로드 실패: {e}")
        return pd.DataFrame()

    try:
        zf = zipfile.ZipFile(buf)
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            print(f"[경고] PSD 벌크 zip 내 CSV 없음: {zf.namelist()[:5]}")
            return pd.DataFrame()
    except zipfile.BadZipFile as e:
        print(f"[경고] PSD 벌크 zip 판독 실패: {e}")
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for name in csv_names:
        try:
            with zf.open(name) as fh:
                raw = pd.read_csv(fh, low_memory=False)
        except Exception as e:
            print(f"[경고] PSD 벌크 CSV 파싱 실패({name}): {e}")
            continue

        cols = [str(c) for c in raw.columns]
        raw.columns = cols
        code_col  = _find_col(cols, "Commodity_Code")
        cdesc_col = _find_col(cols, "Commodity_Description", "Commodity_Name", "Commodity")
        my_col    = _find_col(cols, "Market_Year", "Marketing_Year")
        cy_col    = _find_col(cols, "Calendar_Year")
        attr_col  = _find_col(cols, "Attribute_Description", "Attribute_ID", "Attribute")
        ctry_col  = _find_col(cols, "Country_Name", "Country_Code", "Country")
        val_col   = _find_col(cols, "Value")
        unit_col  = _find_col(cols, "Unit_Description", "Unit_ID", "Unit")
        year_col  = my_col or cy_col
        print(f"[정보] PSD 벌크({name}) 컬럼 탐지: code={code_col}, year={year_col}"
              f"({'Market' if my_col else 'Calendar'}), attr={attr_col}, value={val_col}")
        if not (val_col and year_col and attr_col and (code_col or cdesc_col)):
            print(f"[경고] PSD 벌크({name}) 필수 컬럼 미탐지 — 실제 컬럼: {cols[:12]}")
            continue

        # 대두 관련 품목 필터: SBO 코드(2222000) + Commodity 설명에 soybean 포함
        # (대두유·대두·대두박 등 코드 체계 변동에도 견고)
        mask = pd.Series(False, index=raw.index)
        if code_col:
            code_str = raw[code_col].astype(str).str.replace(r"\.0$", "", regex=True)
            mask |= code_str.str.zfill(7) == SBO_COMMODITY_CODE
        if cdesc_col:
            mask |= raw[cdesc_col].astype(str).str.contains("soybean", case=False, na=False)
        sub = raw[mask].copy()
        if sub.empty:
            continue

        sub["_year"] = pd.to_numeric(sub[year_col], errors="coerce")
        sub = sub[sub["_year"] >= start_year].dropna(subset=["_year"])
        if sub.empty:
            continue

        attr = sub[attr_col].astype(str).str.strip().str.replace(r"[^0-9A-Za-z]+", "_", regex=True)
        commodity = (sub[cdesc_col].astype(str).str.strip()
                     if cdesc_col else pd.Series("SOYBEAN", index=sub.index))
        # 2026-11-17: 품목(대두·대두박·대두유)·국가 축을 코드에 반영 — 미분리 시 mart 값충돌 하드 실패
        #   (PSD_Total_Supply@2026-10-01 209개 값). API 경로의 국가 접미(A-173)와 같은 원칙.
        comm_code = commodity.str.lower().map(
            lambda s: "SBO" if "oil" in s else "SBM" if "meal" in s else "SOY" if "seed" in s
            else re.sub(r"[^0-9A-Za-z]+", "_", s).strip("_").upper())
        ctry_src = _find_col(cols, "Country_Code") or ctry_col
        ctry_code = (sub[ctry_src].astype(str).str.strip()
                     .str.replace(r"[^0-9A-Za-z]+", "_", regex=True)
                     if ctry_src else pd.Series("ALL", index=sub.index))
        out = pd.DataFrame({
            # Market_Year 기준: 마케팅연도 시작(10월)을 price_date로 (기존 규약과 동일)
            "price_date":     pd.to_datetime(
                sub["_year"].astype(int).astype(str) + "-10-01", errors="coerce"),
            "source_name":    "USDA_PSD_BULK",
            "indicator_code": "PSD_BULK_" + comm_code + "_" + attr + "_" + ctry_code,
            "country":        sub[ctry_col].astype(str) if ctry_col else "",
            "value":          pd.to_numeric(sub[val_col], errors="coerce"),
            "unit":           sub[unit_col].astype(str) if unit_col else "1000 MT",
            "note":           "[PSD-BULK-CSV: " + commodity + "]",
        }).dropna(subset=["price_date", "value"])
        frames.append(out)

    if not frames:
        print("[경고] PSD 벌크 CSV: 대두 관련 행 없음")
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["ingested_at"] = pd.Timestamp.utcnow()
    print(f"[완료] PSD 벌크 CSV 폴백 {len(df)}건 ({start_year}~) — "
          f"지표 {df['indicator_code'].nunique()}종")
    return df


def fetch_usda_arms_soybean_costs(year: int | None = None) -> pd.DataFrame:
    """USDA ARMS (Agricultural Resource Management Survey) — 대두 생산비용 수집.
    API: https://data.ers.usda.gov/api/Data
    USDA_ARM_API_KEY 미등록 시 공개 요청 (일부 데이터 제한 있음).
    """
    api_key = os.environ.get("USDA_ARM_API_KEY", "")
    target_year = year or date.today().year - 1  # ARMS는 전년도까지 공개
    params = {
        "year":      target_year,
        "report":    "ARMS",
        "farmtype":  "All Farms",
        "category":  "Soybeans",
        "item":      "Variable costs",
        "state":     "US",
    }
    try:
        data = _fetch_arms(params, api_key=api_key)
    except Exception as e:
        print(f"[경고] USDA ARMS 수집 실패 ({target_year}년): {e}")
        return pd.DataFrame()

    if not data:
        print(f"[경고] USDA ARMS: {target_year}년 대두 생산비용 데이터 없음")
        return pd.DataFrame()

    rows = []
    items = data if isinstance(data, list) else data.get("data", [])
    for item in items:
        val = item.get("value") or item.get("Value")
        rows.append({
            "price_date":     f"{target_year}-01-01",
            "source_name":    "USDA_ARMS",
            "indicator_code": f"SOYBEAN_VARIABLE_COST_{item.get('state', 'US')}",
            "country":        "US",
            "value":          val,
            "unit":           item.get("unit", "USD/acre"),
        })

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["value"]      = pd.to_numeric(df["value"], errors="coerce")
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df.dropna(subset=["value"])


def run() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")

    # HISTORICAL_START_YEAR: 백필 워크플로우가 주입 (미설정 시 기본 2020)
    start_year = int(os.environ.get("HISTORICAL_START_YEAR", "2010"))
    backfill_mode = os.environ.get("BACKFILL_MODE", "").lower() == "true"
    if backfill_mode:
        print(f"[정보] BACKFILL_MODE 활성화 — WASDE PSD {start_year}년~현재 연도별 일괄 수집")
    else:
        print(f"[정보] 일별 갱신 모드 — 현재 마케팅 연도({date.today().year}) 수집")

    frames = []
    # A-246: 일별 모드는 당해 연도만 호출한다 — 2010~현재 17년 × 2호스트 × 3인증 × 재시도가
    #        장애 시 최대 50분의 무의미한 대기를 만들었다(런 #93 1h30m). 히스토리는 수동
    #        업로드 parquet(wasde_historical·psd_historical)이 커버한다(A-216 관세청과 동일 원리).
    if not backfill_mode:
        start_year = date.today().year
    psd_df = fetch_wasde_multi_year(start_year=start_year)
    if psd_df.empty:
        # A-141(b): API 전 연도 실패(403/500) → 키 불필요 공개 벌크 CSV로 폴백
        print("[정보] PSD API 전 연도 실패 — 벌크 CSV 폴백으로 전환")
        psd_df = fetch_psd_bulk_csv(start_year=start_year)
    if not psd_df.empty:
        frames.append(psd_df)

    arms_df = fetch_usda_arms_soybean_costs()
    if not arms_df.empty:
        frames.append(arms_df)

    if not frames:
        # A-182: 0건을 조용히 success로 넘기면 crop_data 부재가 C-08 게이트에서야
        # 발각되는 '녹색 실패'가 됨(런 32068230640 실증 — 1시간 29분 돌고 산출 0건).
        # 원인 경고(PSD·ARMS 등)는 위 로그에 이미 노출됨 — 잡을 red로 표면화한다.
        raise SystemExit("[오류] WASDE: 수집된 데이터 0건 — 전 소스 실패. "
                         "위 경고 로그에서 소스별 원인을 확인하세요.")

    combined = pd.concat(frames, ignore_index=True)
    out = f"{OUTPUT_DIR}/crop_data_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="WASDE_")
    combined.to_parquet(out, index=False)
    print(f"[완료] WASDE+ARMS 작황 데이터 {len(combined)}건 저장 → {out}")


if __name__ == "__main__":
    run()
