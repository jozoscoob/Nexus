"""
대두유 원산지별 생산량·농업기상 커넥터 — WBS 1.1.7
수집 대상:
  - 미국 주별 대두 생산량: USDA NASS QuickStats (API 키)
  - 국가별 대두 생산 시계열: FAOSTAT (공개) — AgML-CY-Bench 데이터소스
  - 아르헨티나 지역 농업통계: datos.gob.ar / INDEC (공개)
  - 원산지 농업기상 (6개 지역): NASA POWER API (공개, 키 불필요) — 기온·강수·습도
  - 원산지·지역 생산 컨텍스트: Perplexity Pro (실시간 작황 등급·생산량 가이던스)
범위 제외: USDA FAS PSD 글로벌 수급 → wasde_connector.py 담당 (중복 방지)
실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions
참고: github.com/kdmayer/nasa-power-api, github.com/datosgobar, github.com/WUR-AI/AgML-CY-Bench
"""

from __future__ import annotations

import os
import re
import time
from datetime import date, timedelta

import httpx
import pandas as pd
from openai import OpenAI

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

OUTPUT_DIR = "data/raw"
PERPLEXITY_MODEL = "sonar-pro"  # MEMORY L-007

# 주요 원산지 좌표 (NASA POWER / 기상 공통)
# 정본 좌표 표와 정합 — 2026-09-13 (docs/research_desk/_reference/soybean_oil_production_climate.md
#   §3.2 · config/production_regions.yaml tier1). 구: Illinois -89.2 · Mato Grosso -12.6/-55.7 ·
#   Parana -24.7/-51.7 · Santa Fe -31.7/-60.7 — 기후 커넥터 좌표와 어긋나 있었음.
ORIGIN_COORDS = {
    "US_Iowa":        {"lat": 42.0,  "lon": -93.5,  "country": "US"},
    "US_Illinois":    {"lat": 40.0,  "lon": -89.0,  "country": "US"},
    "BR_Mato_Grosso": {"lat": -13.0, "lon": -56.0,  "country": "BR"},
    "BR_Parana":      {"lat": -24.5, "lon": -51.5,  "country": "BR"},
    "AR_Cordoba":     {"lat": -31.4, "lon": -64.2,  "country": "AR"},
    "AR_Santa_Fe":    {"lat": -33.0, "lon": -60.6,  "country": "AR"},
}

NASS_BASE    = "https://quickstats.nass.usda.gov/api/api_GET/"
FAOSTAT_BASE = "https://fenixservices.fao.org/faostat/api/v1/en/data/QCL"
INDEC_API    = "https://apis.datos.gob.ar/series/api/series/"
NASA_POWER   = "https://power.larc.nasa.gov/api/temporal/monthly/point"


def _get(url: str, params: dict | None = None, max_retries: int = 4) -> httpx.Response:
    delay = 2
    for attempt in range(max_retries):
        try:
            r = httpx.get(url, params=params or {}, timeout=60)
            r.raise_for_status()
            return r
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"[오류] API 호출 실패 ({url}): {e}") from e
            time.sleep(delay)
            delay *= 2


def fetch_usda_nass_soybeans(year: int | None = None) -> pd.DataFrame:
    """USDA NASS QuickStats — 미국 주별 대두 생산량.
    키 이름: USDA_NASS_QUICKSTATS_API_KEY 또는 USDA_API_KEY (하위 호환 fallback).
    """
    api_key = (
        os.environ.get("USDA_NASS_QUICKSTATS_API_KEY", "")
        or os.environ.get("USDA_API_KEY", "")
    )
    if not api_key:
        print("[경고] USDA_NASS_QUICKSTATS_API_KEY / USDA_API_KEY 미등록 — NASS 수집 건너뜀")
        return pd.DataFrame()
    start_year = year or int(os.environ.get("HISTORICAL_START_YEAR", "2010"))
    try:
        # A-172: 축 미분리 키 붕괴 수정 — 구 코드는 STATE 전 행(주×통계원천×기준기간×
        #   도메인)을 SOYBEAN_PROD_BU 하나에 적재해 동일 event_time에 3,000여 값이 충돌
        #   (mart 하드 실패의 예시 항목). ①서버측 필터로 확정 연간치(SURVEY·ANNUAL·
        #   YEAR·TOTAL)만 수집 ②NATIONAL=기본 코드, STATE는 _ST_{주} 접미 분리.
        common = {
            "key": api_key,
            "commodity_desc": "SOYBEANS",
            "statisticcat_desc": "PRODUCTION",
            "source_desc": "SURVEY",
            "freq_desc": "ANNUAL",
            "reference_period_desc": "YEAR",
            "domain_desc": "TOTAL",
            # A-174: 관개 주(AR·NE·KS 등)는 IRRIGATED/NON-IRRIGATED/ALL 3계열 반환
            #   (12차 잔존 32건 — 주·연도당 정확히 3개 값). 합계 계열만 고정.
            "prodn_practice_desc": "ALL PRODUCTION PRACTICES",
            "util_practice_desc": "ALL UTILIZATION PRACTICES",
            # 2010 기준선(조정자 지시) — HISTORICAL_START_YEAR 우선
            "year__GE": start_year,
            "unit_desc": "BU",
            "format": "JSON",
        }
        rows = []
        for agg in ("NATIONAL", "STATE"):
            r = _get(NASS_BASE, {**common, "agg_level_desc": agg})
            for it in r.json().get("data", []):
                try:
                    state = it.get("state_alpha", "") or "UNKNOWN"
                    code = ("SOYBEAN_PROD_BU" if agg == "NATIONAL"
                            else f"SOYBEAN_PROD_BU_ST_{state}")
                    rows.append({
                        "price_date": f"{it['year']}-10-01",
                        "source_name": "USDA_NASS",
                        "indicator_code": code,
                        "region": f"US_{state}" if agg == "STATE" else "US",
                        "country": "US",
                        "value": float(it["Value"].replace(",", "")),
                        "unit": "Bushels",
                    })
                except (ValueError, KeyError):
                    continue
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["price_date"] = pd.to_datetime(df["price_date"])
        df["ingested_at"] = pd.Timestamp.utcnow()
        return df
    except Exception as e:
        print(f"[경고] USDA NASS 수집 실패: {e}")
        return pd.DataFrame()


def fetch_faostat_soybeans(year_start: int = 2017) -> pd.DataFrame:
    """FAOSTAT — 국가별 대두 생산량 시계열 (공개, 키 불필요). AgML-CY-Bench 벤치마크 데이터소스."""
    try:
        r = _get(FAOSTAT_BASE, {
            "item": "2555",       # Soybeans
            "element": "5510",   # Production (tonnes)
            "year": ",".join(str(y) for y in range(year_start, date.today().year + 1)),
            "area": "9,21,32,138,231",  # Argentina, Brazil, China, Paraguay, USA
            "outputType": "csv",
        })
        # FAOSTAT CSV 파싱
        from io import StringIO
        df_raw = pd.read_csv(StringIO(r.text))
        df_raw.columns = [c.strip() for c in df_raw.columns]
        # A-172: 국가 축을 코드에 반영 — 구 단일 코드는 동일 연도에 5개국 값이 충돌
        _AREA_SUFFIX = {"Argentina": "AR", "Brazil": "BR", "China": "CN",
                        "China, mainland": "CN", "Paraguay": "PY",
                        "United States of America": "US"}
        rows = []
        for _, row in df_raw.iterrows():
            try:
                area = str(row.get("Area", ""))
                suffix = _AREA_SUFFIX.get(
                    area, "".join(ch for ch in area.upper() if ch.isalpha())[:3] or "UNK")
                rows.append({
                    "price_date": f"{int(row['Year'])}-10-01",
                    "source_name": "FAOSTAT",
                    "indicator_code": f"SOYBEAN_PROD_TONNE_{suffix}",
                    "country": area,
                    "value": float(str(row.get("Value", "0")).replace(",", "")),
                    "unit": "Tonnes",
                })
            except (ValueError, KeyError):
                continue
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["price_date"] = pd.to_datetime(df["price_date"])
        df["ingested_at"] = pd.Timestamp.utcnow()
        return df.dropna(subset=["value"])
    except Exception as e:
        print(f"[경고] FAOSTAT 수집 실패: {e}")
        return pd.DataFrame()


def fetch_argentina_indec() -> pd.DataFrame:
    """Argentina INDEC 대두 생산 시계열 — datos.gob.ar 공개 API.
    참고: github.com/datosgobar (Argentina Open Data)
    """
    # INDEC 농업통계 시계열 ID (대두 생산량 및 재배면적)
    SERIES_IDS = {
        # A-172: FAOSTAT 국가 접미(_AR)와의 코드 충돌 방지 — 원천 접미로 분리
        "170.1_SOJA_PRODUCCI_0_A_20": ("SOYBEAN_PROD_TONNE_AR_INDEC", "Tonnes"),
        "170.1_SOJA_SUPERFICI_0_A_20": ("SOYBEAN_AREA_HA_AR", "Hectares"),
    }
    rows = []
    for series_id, (code, unit) in SERIES_IDS.items():
        try:
            r = _get(INDEC_API, {
                "ids": series_id,
                "limit": 100,
                "sort": "desc",
                "format": "json",
            })
            data = r.json()
            for entry in data.get("data", []):
                try:
                    rows.append({
                        "price_date": entry[0],
                        "source_name": "INDEC_AR",
                        "indicator_code": code,
                        "country": "Argentina",
                        "value": float(entry[1]),
                        "unit": unit,
                    })
                except (ValueError, IndexError):
                    continue
        except Exception as e:
            # A-149: INDEC 400은 시리즈 ID 폐기 추정 — 아르헨 생산량은 PSD로 확보됨(INDEC은 보조).
            #        치명 아님 → [경고]에서 [정보]로 강등.
            print(f"[정보] INDEC {series_id} 수집 실패 (보조 소스 — PSD가 아르헨 생산량 커버): {e}")
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


# NASA POWER 파라미터 선별 (Standard Resolution · community=AG · A-065)
# C-03·P1-01·P1-03 협의: 대두 수율 구동 인자(열스트레스·수분·일사·토양수분)만 선별.
# High Resolution은 2024년만 제공 → 9개년 히스토리 부적합. Standard(월별, ~현재)로 확정.
# 근거 문서: docs/research_desk/realtime_data_acquisition/nasa_power_selection_2026_07_10.md
NASA_POWER_PARAMS: dict[str, tuple[str, str]] = {
    "T2M":               ("°C",          "기온(2m)"),
    "T2M_MAX":           ("°C",          "최고기온(열스트레스)"),
    "T2M_MIN":           ("°C",          "최저기온(냉해)"),
    "PRECTOTCORR":       ("mm/day",      "강수(수분 공급)"),
    "RH2M":              ("%",           "상대습도(병해·증산)"),
    "ALLSKY_SFC_SW_DWN": ("MJ/m^2/day",  "전천 일사(광합성 에너지)"),
    "ALLSKY_SFC_PAR_TOT":("W/m^2",       "광합성유효복사 PAR"),
    "GWETROOT":          ("0-1",         "근권 토양수분(가뭄)"),
    "GWETTOP":           ("0-1",         "표층 토양수분"),
}


# A-143: 422 재시도 1회용 핵심 6종 (PAR·토양수분 2종 제외) — 파라미터 조합 문제 절연
NASA_POWER_CORE_PARAMS: tuple[str, ...] = (
    "T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN",
)


def _last_complete_month(today: date | None = None) -> date:
    """직전 완결 월의 1일 반환 — 미완결 월(end=당월) 요청이 422의 유력 원인 (A-143)."""
    d = today or date.today()
    first_of_month = d.replace(day=1)
    prev_month_last_day = first_of_month - timedelta(days=1)
    return prev_month_last_day.replace(day=1)


def _fetch_power_monthly(query: dict) -> dict | None:
    """NASA POWER monthly point 호출 — 422면 응답 본문 로그 후 None (A-143)."""
    r = httpx.get(NASA_POWER, params=query, timeout=60)
    if r.status_code == 422:
        print(f"[경고] NASA POWER 422 — 요청 파라미터: {query} · 응답 본문: {r.text[:600]}")  # A-160: 원인 확정용 전문 로그
        return None
    r.raise_for_status()
    return r.json()


def fetch_nasa_power_agromet(start_date: date | None = None) -> pd.DataFrame:
    """NASA POWER API — 원산지별 월별 농업기상 (선별 9종 파라미터).
    참고: github.com/kdmayer/nasa-power-api | 키 불필요 | community=AG (Agroclimatology)
    수집 범위: start_date(기본 2017-01-01)부터 **직전 완결 월**까지 (A-143).
    선별 근거: 대두 수율 구동 = 열(T2M/MAX/MIN)·수분(강수/토양수분)·일사(SW/PAR)·습도(A-065).

    A-143: monthly point 422 원인 = end에 미완결 월(당월) 지정 추정 → 직전 완결 월로
           클램프. 잔여 422는 파라미터 조합 문제 절연을 위해 핵심 6종 축소 재시도 1회.
    A-149: 422 진짜 원인 = monthly/annual API의 start/end는 **연도 4자리(YYYY)** 형식
           (YYYYMMDD는 daily 전용 — power.larc.nasa.gov/docs). 기존 YYYYMM(예: 201701)
           전달이 422 유발 → 연도 정수로 수정. A-143 축소 재시도는 유지.
    """
    end   = _last_complete_month()          # A-143: 미완결 월 제외
    start = start_date if start_date else date(2017, 1, 1)
    param_csv = ",".join(NASA_POWER_PARAMS)
    rows = []
    for location, coord in ORIGIN_COORDS.items():
        base_query = {
            # A-149: monthly API는 연도(YYYY)만 허용 — end는 직전 완결 월이 속한 연도
            "start":      start.year,
            "end":        end.year,
            "latitude":   coord["lat"],
            "longitude":  coord["lon"],
            "community":  "AG",
            "format":     "JSON",
            # A-277: POWER API가 밑줄 포함 user를 422로 거부("alphanumeric user") — 영숫자만 사용
            "user":       "nexusproject",
            "header":     "true",
        }
        try:
            payload = _fetch_power_monthly({**base_query, "parameters": param_csv})
            if payload is None:
                # A-143: 422 → 핵심 6종(PAR·GWETROOT·GWETTOP 제거)으로 1회 축소 재시도
                print(f"[정보] NASA POWER {location}: 핵심 6종으로 축소 재시도")
                payload = _fetch_power_monthly(
                    {**base_query, "parameters": ",".join(NASA_POWER_CORE_PARAMS)})
            if payload is None:
                print(f"[경고] NASA POWER {location}: 축소 재시도도 422 — 건너뜀")
                continue
            props   = payload.get("properties", {}).get("parameter", {})
            for param, (unit, _desc) in NASA_POWER_PARAMS.items():
                series = props.get(param, {})
                for ym, val in series.items():
                    if val is None or float(val) <= -999:   # POWER 결측 센티넬
                        continue
                    # A-277: monthly API는 연간 집계를 월 '13'(YYYY13) 키로 함께 반환 —
                    # "2017-13-01"이 to_datetime을 중단시킨 원인(런 #111). 1~12월만 적재.
                    month = _power_month(ym)
                    if month is None:
                        continue
                    try:
                        rows.append({
                            "price_date":     f"{ym[:4]}-{month:02d}-01",
                            "source_name":    "NASA_POWER",
                            "indicator_code": f"{param}_{location}",
                            "region":         location,
                            "country":        coord["country"],
                            "value":          float(val),
                            "unit":           unit,
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"[경고] NASA POWER {location} 수집 실패: {e}")
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"], errors="coerce")
    df["ingested_at"] = pd.Timestamp.now("UTC")
    return df


def _power_month(ym: str) -> int | None:
    """NASA POWER monthly 키(YYYYMM)에서 월을 추출 — 연간 집계(월 13)·비정형 키는 None."""
    s = str(ym)
    if len(s) != 6 or not s.isdigit():
        return None
    month = int(s[4:])
    return month if 1 <= month <= 12 else None


def fetch_perplexity_production_regions() -> pd.DataFrame:
    """Perplexity Pro — 원산지별 생산 컨텍스트 (지역별 작황 등급, 생산량 가이던스)."""
    api_key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not api_key:
        print("[경고] PERPLEXITY_API_KEY 미등록 — 생산지역 컨텍스트 건너뜀")
        return pd.DataFrame()
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    prompt = (
        "Provide the latest soybean production estimates for major regions: "
        "U.S. (Iowa, Illinois), Brazil (Mato Grosso, Paraná), Argentina (Córdoba, Santa Fe). "
        "For each region: crop condition rating (Excellent/Good/Fair/Poor %) and "
        "latest production estimate in million metric tonnes. "
        "Format: REGION: [name] | CONDITION: [%Good+Excellent] | PRODUCTION: [MMT] | DATE: [date]"
    )
    try:
        r = client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text = r.choices[0].message.content
        today = date.today().isoformat()
        rows = []
        for match in re.finditer(
            r"REGION:\s*([^|]+)\|[^|]*CONDITION:\s*([0-9]+)[^|]*\|[^|]*PRODUCTION:\s*([0-9.]+)",
            text, re.IGNORECASE
        ):
            region, condition, production = match.groups()
            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/USDA_NASS_proxy",
                "indicator_code": f"CROP_CONDITION_{region.strip().replace(' ', '_')}",
                "region":         region.strip(),
                "country":        region.strip()[:2],
                "value":          float(condition),
                "unit":           "% Good+Excellent",
            })
            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/USDA_NASS_proxy",
                "indicator_code": f"PROD_ESTIMATE_{region.strip().replace(' ', '_')}",
                "region":         region.strip(),
                "country":        region.strip()[:2],
                "value":          float(production),
                "unit":           "MMT",
            })
        if not rows:
            print(f"[경고] Perplexity 생산지역 파싱 실패. 원문: {text[:200]}")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["price_date"] = pd.to_datetime(df["price_date"])
        df["ingested_at"] = pd.Timestamp.utcnow()
        return df
    except Exception as e:
        print(f"[경고] Perplexity 생산지역 수집 실패: {e}")
        return pd.DataFrame()


# A-148: ESR 403 대응 — 같은 실행에서 WASDE/PSD는 "X-Api-Key 헤더"로 성공했으나 ESR은 403.
#        호스트·시기별 인증 헤더 이름이 혼재하므로 wasde_connector의 3방식 체인(A-141a)과
#        동일 패턴 적용: ①X-Api-Key 헤더 ②API_KEY 헤더 ③?api_key= 쿼리. 성공 방식 1회 로그.
_FAS_ESR_AUTH_SUCCESS_LOGGED = False


def _fetch_fas_esr(url: str, api_key: str = "", max_retries: int = 2) -> list | dict | None:
    """USDA FAS ESR API — 인증 3방식 시도 체인 (A-148, 패턴은 A-141a 동일).

    ① 헤더 X-Api-Key (ESR 문서 방식, A-019)
    ② 헤더 API_KEY   (구 OpenData 방식, A-007)
    ③ 쿼리 ?api_key= (최초 방식 폴백)
    성공한 방식은 1회 로그. 401/403이면 다음 방식으로 즉시 전환.
    404는 None 반환(해당 연도·상품 데이터 없음 — 인증 문제 아님).
    """
    global _FAS_ESR_AUTH_SUCCESS_LOGGED
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
                r = httpx.get(
                    url,
                    headers={"accept": "application/json", **headers},
                    params=params,
                    timeout=30,
                )
                if r.status_code == 404:
                    return None  # 해당 연도 데이터 없음 — 인증 방식 전환 불필요
                if r.status_code in (401, 403):
                    print(f"[정보] FAS ESR {r.status_code} ({style_name}) — 다음 인증 방식 시도")
                    last_error = httpx.HTTPStatusError(
                        f"{r.status_code}", request=r.request, response=r)
                    break  # 인증 방식 전환 (재시도 무의미)
                r.raise_for_status()
                if not _FAS_ESR_AUTH_SUCCESS_LOGGED:
                    print(f"[정보] FAS ESR 인증 성공 방식: {style_name}")
                    _FAS_ESR_AUTH_SUCCESS_LOGGED = True
                return r.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                last_error = e
                if attempt == max_retries - 1:
                    break
                time.sleep(delay)
                delay *= 2
    raise RuntimeError(f"[오류] FAS ESR API 호출 실패 (인증 3방식 모두): {last_error}")


# A-277: ESR v2 응답 실필드(공식 문서 — weekEndingDate·weeklyExports·outstandingSales·
# currentMYNetSales·accumulatedExports). 구 코드의 weeklyExportSalesDate/weekSales는 존재하지 않는
# 키라 1,058행 전량이 날짜 결측·값 0으로 폐기돼 왔다(A-175의 '1,048행 결측'이 이 결함).
_ESR_DATE_KEYS = ("weekEndingDate", "weeklyExportSalesDate", "weekEnding", "date")
_ESR_VALUE_KEYS = {
    "WEEKLY_EXPORTS": ("weeklyExports", "weekSales"),
    "OUTSTANDING_SALES": ("outstandingSales",),
    "NET_SALES": ("currentMYNetSales", "netSales"),
    "ACCUM_EXPORTS": ("accumulatedExports",),
}


def _esr_rows(entry: dict, indicator_prefix: str, yr: int) -> list[dict]:
    """ESR 레코드 1건 → 지표별 행. 날짜 키 부재 시 빈 목록(상위에서 필드명 자기발견 로그)."""
    wk_date = next((str(entry[k])[:10] for k in _ESR_DATE_KEYS if entry.get(k)), "")
    if not wk_date:
        return []
    # 지표코드는 'ESR_' 접두 — asof.py RELEASE_RULES["ESR_"](대상주 다음 목요일 발표) 적용 대상.
    # 마케팅연도별 코드 분리는 시계열을 조각내므로 폐기 — market_year 컬럼으로 보존.
    base = f"ESR_{indicator_prefix.replace('_EXPORT', '')}_KR"
    out: list[dict] = []
    for suffix, keys in _ESR_VALUE_KEYS.items():
        raw = next((entry[k] for k in keys if entry.get(k) is not None), None)
        if raw is None:
            continue
        try:
            val = float(raw)
        except (ValueError, TypeError):
            continue
        out.append({
            "price_date":     wk_date,
            "source_name":    "USDA_FAS_ESR",
            "indicator_code": f"{base}_{suffix}",
            "country":        "KOR",
            "value":          val,
            "unit":           str(entry.get("unitName") or "MT"),
            "market_year":    yr,
        })
    return out


def fetch_fas_esr_soybean_oil(start_year: int = 2017) -> pd.DataFrame:
    """USDA FAS Export Sales Reporting (ESR) — 대두유 수출 판매량 (국가별·마케팅연도별).

    검증된 엔드포인트 (2026-05-13 사용자 확인):
      GET https://api.fas.usda.gov/api/esr/exports/commodityCode/{code}/countryCode/{cc}/marketYear/{yr}
      Header: X-Api-Key: {USDA_FAS_API_KEY}

    수집 대상:
      상품: 902(대두유), 801(대두) — 한국 수입 관련 주요 국가
      국가: 미국(5800=Korea 수출국 관점이 아닌 수입국으로 한국 조회 방식과 상이)
            → 대두유 주요 수출국: 아르헨티나(3570), 브라질(3510), 미국(5700=미국→한국X)

    주의: FAS ESR의 countryCode는 수입국 기준 (수출 목적지).
          한국으로의 수출: countryCode=5800 (Kor, Rep).
    """
    # 올바른 v2 API (api.fas.usda.gov — 사용자 확인)
    FAS_ESR_V2_BASE = "https://api.fas.usda.gov/api/esr/exports"
    api_key = (
        os.environ.get("USDA_FAS_API_KEY", "")
        or os.environ.get("USDA_FAS_PSD_API_KEY", "")
    )

    # 한국(5800)으로 수출하는 주요 대두유 관련 상품
    COMMODITY_CODES = {
        "902":  "SBO_EXPORT",      # Soybean Oil
        "801":  "SOYBEAN_EXPORT",  # Soybeans (원료 수급 맥락)
    }
    # 한국으로의 대두유 주요 수출국 → FAS ESR countryCode=5800(한국)으로 조회
    # 또는 대두유 주요 원산지 국가 코드로 수출 현황 파악
    DEST_KOREA = "5800"

    rows: list[dict] = []
    schema_logged = False

    for yr in range(start_year, date.today().year + 1):
        for cmd_code, indicator_prefix in COMMODITY_CODES.items():
            url = f"{FAS_ESR_V2_BASE}/commodityCode/{cmd_code}/countryCode/{DEST_KOREA}/marketYear/{yr}"
            try:
                # A-148: 단일 X-Api-Key 고정 → 인증 3방식 체인(_fetch_fas_esr)으로 교체
                data = _fetch_fas_esr(url, api_key=api_key)
                if not data:
                    continue
                entries = data if isinstance(data, list) else data.get("data", [])
                n_before = len(rows)
                for entry in entries:
                    rows.extend(_esr_rows(entry, indicator_prefix, yr))
                if entries and len(rows) == n_before and not schema_logged:
                    # A-277 자기발견: 필드명 불일치 시 실제 키를 노출(추측 교정 금지 — A-106 패턴)
                    print(f"[경고] FAS ESR 응답 필드 불일치 — 첫 레코드 키: {sorted(entries[0].keys())}")
                    schema_logged = True
                print(f"[정보] FAS ESR {cmd_code} → 한국 {yr}: {len(entries)}건")
            except Exception as e:
                print(f"[경고] FAS ESR {cmd_code}/{yr}: {e}")
            time.sleep(0.3)  # API 레이트 리밋 준수

    if not rows:
        print("[경고] FAS ESR: 수집된 데이터 없음 — USDA_FAS_API_KEY 등록 또는 엔드포인트 확인")
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"], errors="coerce")
    df["ingested_at"] = pd.Timestamp.now("UTC")
    return dedupe_esr_marketing_year_boundary(df.dropna(subset=["value"]))


def dedupe_esr_marketing_year_boundary(df: pd.DataFrame) -> pd.DataFrame:
    """마케팅연도 경계 주 중복 제거 — 신 마케팅연도 보고를 채택한다.

    A-280: ESR은 MY 경계 주(10월 첫 주)를 구 MY 조회(구곡 마감분)와 신 MY 조회(신곡 첫 주)
    양쪽에서 반환하며 누적치가 MY마다 리셋되므로 값이 다르다. 코드에 MY 축이 없으면
    (지표, event_time) 값충돌로 feature mart 게이트(D-033)가 차단된다(런 #113, 46건).
    규칙: 같은 (indicator_code, price_date)면 market_year가 큰 행(신 MY)만 남긴다.
    """
    if df.empty or "market_year" not in df.columns:
        return df
    before = len(df)
    out = (df.sort_values(["indicator_code", "price_date", "market_year"], kind="stable")
             .drop_duplicates(subset=["indicator_code", "price_date"], keep="last")
             .reset_index(drop=True))
    dropped = before - len(out)
    if dropped:
        print(f"[정보] FAS ESR 마케팅연도 경계 주 중복 {dropped}건 제거 — 신 마케팅연도 보고 채택")
    return out


def normalize_price_dates(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """원천 프레임의 price_date를 tz 없는 datetime으로 통일한 뒤 결합한다.

    A-277: naive·tz-aware price_date 프레임을 그대로 concat하면 object dtype이 되고
    이후 to_datetime(errors="coerce")가 aware 원소를 NaT로 만든다 — 원천별 파싱 실패와
    겹치면 event_time 전량 결측(런 #110)으로 fail-loud 중단. 프레임별 정규화 + 원천별
    NaT 건수 로그로 원인을 드러낸다.
    """
    normalized: list[pd.DataFrame] = []
    for f in frames:
        f = f.copy()
        src = str(f["source_name"].iloc[0]) if "source_name" in f.columns and len(f) else "?"
        if "price_date" not in f.columns:
            print(f"[경고] {src}: price_date 컬럼 없음 — 전 행 NaT 처리")
            f["price_date"] = pd.NaT
        pd_col = pd.to_datetime(f["price_date"], errors="coerce", utc=True)
        f["price_date"] = pd_col.dt.tz_localize(None)
        n_nat = int(f["price_date"].isna().sum())
        if n_nat:
            print(f"[경고] {src}: price_date 파싱 실패 {n_nat}/{len(f)}건")
        normalized.append(f)
    return pd.concat(normalized, ignore_index=True)


def run() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")
    frames = [
        fetch_usda_nass_soybeans(),                    # year__GE=2010 (A-080)
        fetch_faostat_soybeans(),                      # year_start=2020
        fetch_argentina_indec(),
        fetch_nasa_power_agromet(),                    # start_date=2020-01-01
        fetch_perplexity_production_regions(),
        fetch_fas_esr_soybean_oil(),
    ]
    frames = [f for f in frames if not f.empty]
    if not frames:
        print("[경고] 생산량 데이터: 수집된 항목 없음")
        return
    combined = normalize_price_dates(frames)
    out = f"{OUTPUT_DIR}/production_data_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="PRODUCTION")
    # A-175: 13차 런에서 1,048/1,580행 as-of 결측(ESR 등 날짜 미파싱 행) — 날짜 없는
    # 관측은 시계열 투입이 불가하므로 원인 로그 후 제외(전량 결측이면 결함으로 중단).
    if combined["event_time"].isna().all():
        diag = combined["source_name"].value_counts().to_dict()
        raise RuntimeError(
            f"[오류] production event_time 전량 결측 — price_date 파생 결함. 원천별 행 수: {diag}")
    n_nat = int(combined["event_time"].isna().sum())
    if n_nat:
        bad_src = combined.loc[combined["event_time"].isna(), "source_name"].value_counts()
        print(f"[경고] event_time 결측 {n_nat}건 제외 — 원천별: {bad_src.to_dict()}")
        combined = combined[combined["event_time"].notna()]
    combined.to_parquet(out, index=False)
    print(f"[완료] 원산지 생산량 데이터 {len(combined)}건 저장 → {out}")


if __name__ == "__main__":
    run()
