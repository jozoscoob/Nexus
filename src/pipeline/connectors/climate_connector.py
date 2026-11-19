"""
기후·기상이상 커넥터 — WBS 1.1.5 / 1.1.20
수집 대상:
  ENSO 페이즈 (NOAA CPC ONI) · 원산지 기상이상 (OpenWeatherMap)
  Open-Meteo 아카이브 — 산지 일별 기후 (config/production_regions.yaml — tier1 12 + tier2 11)
  Open-Meteo 예보 — 산지 15일 일별 예보(FCST_ 접두, 참고 전용 — 2026-09-13 신설)
  ECMWF ERA5 기온·강수 이상 (ECMWF_API_KEY)
범위 제외: NASA POWER 농업기상 → production_connector.py 담당
실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions
"""

from __future__ import annotations

import os
import time
from datetime import date, timedelta
from typing import Any

import httpx
import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

OUTPUT_DIR = "data/raw"
NOAA_ENSO_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
OPEN_METEO_BASE = "https://archive-api.open-meteo.com/v1/archive"
# 2026-09-13: 예보 API(무료·키 불필요·최대 16일). models=best_match = ECMWF IFS/AIFS 0.25°
OPEN_METEO_FORECAST_BASE = "https://api.open-meteo.com/v1/forecast"
FORECAST_SOURCE_NAME = "OpenMeteo_forecast(best_match)"
FORECAST_CODE_PREFIX = "FCST_"
REGIONS_CONFIG_PATH = "config/production_regions.yaml"

# Open-Meteo 일별 수집 변수 (ERA5-Land 기반, API 키 불필요)
# 주의: direct_radiation_spread/soil_temperature_0_to_7cm_spread 는 비표준 — 표준명으로 교정
OPEN_METEO_VARS: list[str] = [
    "temperature_2m_max",          # 일 최고기온 (°C)
    "temperature_2m_min",          # 일 최저기온 (°C)
    "precipitation_sum",           # 일 강수량 (mm)
    "shortwave_radiation_sum",     # 일 단파복사 합계 (MJ/m²) ← direct_radiation 표준명
    "soil_temperature_0_to_7cm",   # 0–7cm 토양 온도 (°C, ERA5-Land 일평균)
    "soil_moisture_0_to_7cm",      # 0–7cm 토양 수분 (m³/m³, ERA5-Land 일평균)
    "et0_fao_evapotranspiration",  # FAO 기준증발산량 (mm)
    "sunshine_duration",           # 일조시간 (s/day)
]

# A-110(F15): NOAA CPC ONI 계절 코드 → 해당 3개월 구간의 **중간월**
# (DJF=12·1·2월의 중간 → 1월). 12개 계절이 12개 월에 1:1 대응한다.
_ONI_SEASON_MONTH: dict[str, int] = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}

# A-110(F3): Open-Meteo archive의 **daily 집계로 제공되지 않는** 변수.
# 이들은 hourly 전용이므로 별도 요청 후 일평균으로 집계해야 한다.
# (구 코드는 daily에 함께 요청 → HTTP 400 → 12개 지역 전부 실패)
HOURLY_ONLY_VARS: list[str] = ["soil_temperature_0_to_7cm", "soil_moisture_0_to_7cm"]

OPEN_METEO_UNITS: dict[str, str] = {
    "temperature_2m_max":         "°C",
    "temperature_2m_min":         "°C",
    "precipitation_sum":          "mm",
    "shortwave_radiation_sum":    "MJ/m²",
    "soil_temperature_0_to_7cm":  "°C",
    "soil_moisture_0_to_7cm":     "m³/m³",
    "et0_fao_evapotranspiration": "mm",
    "sunshine_duration":          "s",
}

# 예보 daily 변수 — 아카이브 daily 변수의 부분집합(토양·일조는 예보 daily 미제공)
FORECAST_VARS: list[str] = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
]

# 내장 12개 주요 생산지역 — soybean_oil_production_climate.md §3.2 (tier1 정본 좌표).
# 2026-09-13: 단일 진실 원천은 config/production_regions.yaml — 이 dict는 설정 파일 부재·
#   파싱 실패 시 **폴백**으로만 쓴다(tier2 11개 지역은 설정 파일에만 존재).
_BUILTIN_REGIONS: dict[str, dict[str, Any]] = {
    "CN_Heilongjiang": {"lat":  48.0, "lon":  128.0, "country": "China",     "role": "grow"},
    "CN_Shandong":     {"lat":  36.5, "lon":  118.0, "country": "China",     "role": "crush"},
    "CN_Jiangsu":      {"lat":  32.5, "lon":  120.0, "country": "China",     "role": "crush"},
    "US_Illinois":     {"lat":  40.0, "lon":  -89.0, "country": "USA",       "role": "grow_crush"},
    "US_Iowa":         {"lat":  42.0, "lon":  -93.5, "country": "USA",       "role": "grow_crush"},
    "US_Indiana":      {"lat":  40.2, "lon":  -86.1, "country": "USA",       "role": "grow"},
    "BR_MatoGrosso":   {"lat": -13.0, "lon":  -56.0, "country": "Brazil",    "role": "grow_crush"},
    "BR_Parana":       {"lat": -24.5, "lon":  -51.5, "country": "Brazil",    "role": "grow_crush"},
    "BR_MatoGrossodoSul": {"lat": -20.0, "lon": -54.5, "country": "Brazil",  "role": "grow"},
    "AR_Cordoba":      {"lat": -31.4, "lon":  -64.2, "country": "Argentina", "role": "grow"},
    "AR_SantaFe":      {"lat": -33.0, "lon":  -60.6, "country": "Argentina", "role": "crush"},
    "AR_BuenosAires":  {"lat": -36.0, "lon":  -60.0, "country": "Argentina", "role": "grow"},
}
_REGION_KEYS: tuple[str, ...] = (
    "lat", "lon", "country", "role", "crop", "tier", "name_ko", "coord_status")


def _coerce_scalar(raw: str) -> Any:
    """최소 YAML 스칼라 변환 — 따옴표 제거, 정수·실수 판정, 그 외 문자열."""
    s = raw.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def _parse_regions_minimal(text: str) -> list[dict[str, Any]]:
    """pyyaml 부재 시 폴백 — `regions:` 블록의 `- code:` 평면 매핑 목록만 읽는다.

    설정 파일이 이 형식만 쓰도록 헤더 주석에 제약을 명시했다(CI 기후 잡은 pyyaml을
    설치하지 않으므로, 의존성 하나 때문에 tier2 지역을 조용히 잃지 않기 위한 장치).
    """
    entries: list[dict[str, Any]] = []
    in_block = False
    cur: dict[str, Any] | None = None
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].rstrip() if not line.lstrip().startswith("#") else ""
        if not stripped.strip():
            continue
        if stripped.startswith("regions:"):
            in_block = True
            continue
        if not in_block:
            continue
        if not stripped.startswith(" "):        # 최상위 키 등장 → 블록 종료
            break
        body = stripped.strip()
        if body.startswith("- "):
            cur = {}
            entries.append(cur)
            body = body[2:].strip()
        if cur is None or ":" not in body:
            continue
        key, _, val = body.partition(":")
        cur[key.strip()] = _coerce_scalar(val)
    return entries


def load_production_regions(path: str | os.PathLike[str] = REGIONS_CONFIG_PATH,
                            ) -> dict[str, dict[str, Any]]:
    """config/production_regions.yaml → `{code: {lat, lon, country, role, tier, ...}}`.

    파일 부재·파싱 실패 시 `[경고]` 후 내장 12개(tier1)로 폴백한다. 상대 경로는 저장소
    루트 기준으로 해석한다(스크립트 직접 실행·pytest 양쪽에서 동일).
    """
    p = _Path(path)
    if not p.is_absolute():
        p = _Path(__file__).resolve().parents[3] / p
    fallback = {code: {**info, "tier": 1, "crop": "soy", "coord_status": "CONFIRMED"}
                for code, info in _BUILTIN_REGIONS.items()}
    if not p.exists():
        print(f"[경고] 산지 설정 파일 없음: {p} — 내장 12개 지역(tier1)으로 폴백")
        return fallback
    try:
        text = p.read_text(encoding="utf-8")
        try:
            import yaml  # noqa: WPS433 — 선택 의존성(CI 기후 잡 미설치 가능)
            entries = (yaml.safe_load(text) or {}).get("regions") or []
        except ImportError:
            entries = _parse_regions_minimal(text)
        regions: dict[str, dict[str, Any]] = {}
        for e in entries:
            code = str(e.get("code", "")).strip()
            if not code or "lat" not in e or "lon" not in e:
                raise ValueError(f"지역 항목 필수 필드(code/lat/lon) 누락: {e}")
            if code in regions:
                raise ValueError(f"지역 코드 중복: {code}")
            info = {k: e[k] for k in _REGION_KEYS if k in e}
            info["lat"] = float(info["lat"])
            info["lon"] = float(info["lon"])
            info["tier"] = int(info.get("tier", 1))
            regions[code] = info
        if not regions:
            raise ValueError("regions 목록이 비어 있음")
        return regions
    except Exception as e:  # 파싱 실패는 수집 중단 사유가 아님 — 폴백 후 계속
        print(f"[경고] 산지 설정 파싱 실패({type(e).__name__}: {str(e)[:80]}) — "
              "내장 12개 지역(tier1)으로 폴백")
        return fallback


# 수집 대상 산지 — 단일 진실 원천은 설정 파일(23개), 폴백은 내장 12개
PRODUCTION_REGIONS: dict[str, dict[str, Any]] = load_production_regions()


def _select_regions(regions: dict[str, dict[str, Any]] | None = None,
                    ) -> dict[str, dict[str, Any]]:
    """환경변수 CLIMATE_TIER(기본 all · '1' = tier1만)로 수집 대상 산지를 고른다.

    429(무료 티어 한도) 발생 시 CLIMATE_TIER=1로 즉시 축소 운용하는 것이 절차다.
    """
    base = regions if regions is not None else PRODUCTION_REGIONS
    tier_env = os.environ.get("CLIMATE_TIER", "all").strip().lower()
    if tier_env in ("", "all"):
        return dict(base)
    try:
        max_tier = int(tier_env)
    except ValueError:
        print(f"[경고] CLIMATE_TIER 값 해석 불가('{tier_env}') — 전체 지역 수집")
        return dict(base)
    return {c: i for c, i in base.items() if int(i.get("tier", 1)) <= max_tier}


def _tier_counts(regions: dict[str, dict[str, Any]]) -> tuple[int, int]:
    t1 = sum(1 for i in regions.values() if int(i.get("tier", 1)) == 1)
    return t1, len(regions) - t1


# OpenWeatherMap 현재 기상 수집 (3개 원산지, 레거시)
# 2026-09-13: 마투그로수 좌표를 정본 좌표 표(-13.0/-56.0)와 정합(구 -12.6/-55.7)
ORIGIN_COORDS: dict[str, dict[str, float]] = {
    "US_Iowa":        {"lat": 42.0,  "lon": -93.5},
    "BR_Mato_Grosso": {"lat": -13.0, "lon": -56.0},
    "AR_Cordoba":     {"lat": -31.4, "lon": -64.2},
}


def _fetch(url: str, params: dict | None = None, max_retries: int = 4) -> httpx.Response:
    delay = 2
    for attempt in range(max_retries):
        try:
            r = httpx.get(url, params=params or {}, timeout=60)
            r.raise_for_status()
            return r
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"[오류] 기후 API 호출 실패: {e}") from e
            time.sleep(delay)
            delay *= 2


def fetch_enso_index(start_year: int = 2017) -> pd.DataFrame:
    """NOAA CPC ONI (Oceanic Niño Index) 수집 — API 키 불필요.
    파일 형식: SEAS YR ANOM (예: DJF 1950 -1.28)
    """
    r = _fetch(NOAA_ENSO_URL)
    lines = [l for l in r.text.strip().splitlines()
             if not l.startswith("SEAS") and not l.startswith("YR")]
    rows = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            try:
                season = parts[0]
                year   = int(parts[1])
                # A-179: oni.ascii.txt 실제 형식은 SEAS YR **TOTAL ANOM** 4열 —
                #   구 코드(A-005)가 parts[2](TOTAL = Niño3.4 절대 SST ~26-29°C)를
                #   ANOM으로 오독 → G1 경보값 29.02 이상값(16차 런 실증)·핵심 8변수 오염.
                #   마지막 열(ANOM) 사용 + 물리 범위(±5) 가드로 형식 변화에도 안전.
                oni    = float(parts[-1])
                if abs(oni) > 5:
                    print(f"[경고] ONI 물리 범위(±5) 밖 값 {oni} ({season} {year}) — "
                          "열 오독 의심, 행 건너뜀")
                    continue
                if year < start_year:
                    continue
                # A-110(F15): 구 코드는 연 12개 계절값을 **전부 1월 1일**에 찍었다.
                #   → 같은 날짜에 12행이 중복 적재되어 as-of join이 임의의 한 값을 집는다.
                #   ENSO_ONI는 D-015 핵심 8변수 중 하나라 오염 영향이 크다.
                #   계절 코드를 **중간월**로 변환한다(DJF→1월, JFM→2월, … NDJ→12월).
                month = _ONI_SEASON_MONTH.get(season)
                if month is None:
                    continue
                rows.append({
                    "price_date":     f"{year}-{month:02d}-01",
                    "source_name":    "NOAA_CPC",
                    "region_code":    "GLOBAL",
                    "country":        "Global",
                    "indicator_code": "ONI",
                    "season":         season,
                    "value":          oni,
                    "unit":           "°C anomaly",
                    "enso_phase":     "La_Nina" if oni <= -0.5 else ("El_Nino" if oni >= 0.5 else "Neutral"),
                })
            except (ValueError, IndexError):
                continue
    if not rows:
        print(f"[경고] NOAA ONI: {start_year}년 이후 데이터 파싱 실패. NOAA 파일 형식 확인 필요.")
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


def fetch_openmeteo_regional_climate(
    start_date: str = "2017-01-01",
    end_date: str | None = None,
    regions: dict[str, dict[str, Any]] | None = None,
) -> pd.DataFrame:
    """Open-Meteo 아카이브 API — 산지 일별 기후 수집.

    API 키 불필요. ERA5-Land 기반. 비상업적 무료 사용.
    수집 대상: config/production_regions.yaml — tier1 12(정본 좌표) + tier2 11(근사 좌표).
    tier2는 토양 hourly 호출을 생략(daily 6변수만)해 무료 티어 부하를 묶는다.
    CLIMATE_TIER=1 이면 tier1만 수집한다(429 발생 시 축소 절차).
    참고: docs/research_desk/_reference/soybean_oil_production_climate.md §3.2
    """
    if end_date is None:
        end_date = date.today().isoformat()
    targets = _select_regions(regions)
    if not targets:
        print("[경고] 수집 대상 산지 없음(CLIMATE_TIER 필터 결과) — 아카이브 수집 건너뜀")
        return pd.DataFrame()
    n_t1, n_t2 = _tier_counts(targets)
    # 호출 예상: 프로브 1 + tier1(daily+hourly 토양) 2회 + tier2(daily) 1회
    est_calls = 1 + n_t1 * 2 + n_t2
    print(f"[정보] 기후 지역 {len(targets)}개(tier1 {n_t1}·tier2 {n_t2}) · "
          f"호출 예상 {est_calls}")

    all_rows: list[dict] = []
    ingested_at = pd.Timestamp.utcnow()
    ok_regions: list[str] = []
    fail_regions: list[str] = []
    # A-107: Open-Meteo는 daily 집계로 지원되지 않는 변수가 **하나라도** 섞이면 HTTP 400을
    # 반환한다. 전체 변수를 한 번에 요청하는 구조에서는 그 한 개 때문에 **12개 지역 전부**가
    # 실패한다("수집된 데이터 없음"의 잠재 원인). 유효 변수 집합을 1회 자동 확정해 재사용한다.
    # A-110(F3): daily 후보에서 hourly 전용 변수를 애초에 제외한다(400 원인 제거)
    daily_candidates = [v for v in OPEN_METEO_VARS if v not in HOURLY_ONLY_VARS]
    active_vars = list(daily_candidates)

    def _fetch_hourly_soil(lat: float, lon: float) -> dict[str, dict[str, float]]:
        """A-110(F3): 토양 변수는 daily 집계가 없어 **hourly로 받아 일평균**을 만든다.

        구 구조는 이 둘을 daily에 넣어 400을 유발했고, A-107의 프로브는 이를 '미지원'으로
        **조용히 제외**했다 — 하필 대두 작황 설명력이 가장 큰 토양수분이 사라진다.
        시끄러운 실패를 조용한 능력 상실로 바꾸지 않기 위해 별도 경로로 복구한다.
        반환: {변수명: {날짜: 일평균}}
        """
        out: dict[str, dict[str, float]] = {v: {} for v in HOURLY_ONLY_VARS}
        try:
            r = _fetch(OPEN_METEO_BASE, params={
                "latitude": lat, "longitude": lon,
                "start_date": start_date, "end_date": end_date,
                "hourly": ",".join(HOURLY_ONLY_VARS), "timezone": "auto"})
            hourly = (r.json() or {}).get("hourly", {})
            times = hourly.get("time", [])
            if not times:
                return out
            for var in HOURLY_ONLY_VARS:
                vals = hourly.get(var) or []
                acc: dict[str, list[float]] = {}
                for t, v in zip(times, vals):
                    if v is None:
                        continue
                    acc.setdefault(t[:10], []).append(float(v))
                out[var] = {d: sum(xs) / len(xs) for d, xs in acc.items() if xs}
        except Exception as e:
            print(f"[경고] 토양 변수(hourly) 수집 실패: {type(e).__name__}: {str(e)[:70]}")
        return out

    def _probe_vars(lat: float, lon: float) -> list[str]:
        """짧은 구간으로 변수별 지원 여부를 확인해 유효 집합을 반환."""
        probe = {"latitude": lat, "longitude": lon,
                 "start_date": "2024-01-01", "end_date": "2024-01-03", "timezone": "auto"}
        try:
            r = httpx.get(OPEN_METEO_BASE, params={**probe, "daily": ",".join(daily_candidates)},
                          timeout=60)
            if r.status_code == 200:
                return list(daily_candidates)
            print(f"[정보] 전체 변수 요청 거부(HTTP {r.status_code}) — 변수별 개별 확인")
        except Exception as e:
            print(f"[경고] 변수 프로브 실패: {e}")
            return list(daily_candidates)
        good: list[str] = []
        for v in daily_candidates:
            try:
                rr = httpx.get(OPEN_METEO_BASE, params={**probe, "daily": v}, timeout=30)
                (good.append(v) if rr.status_code == 200
                 else print(f"[경고] daily 미지원 변수 제외: {v} (HTTP {rr.status_code})"))
            except Exception:
                print(f"[경고] 변수 확인 실패로 제외: {v}")
            time.sleep(0.2)
        return good

    _first = next(iter(targets.values()))
    active_vars = _probe_vars(_first["lat"], _first["lon"])
    if not active_vars:
        print("[오류] 유효한 daily 변수가 없음 — Open-Meteo 사양 변경 확인 필요")
        return pd.DataFrame()
    if len(active_vars) < len(daily_candidates):
        dropped = sorted(set(daily_candidates) - set(active_vars))
        print(f"[경고] daily 유효 변수 {len(active_vars)}/{len(daily_candidates)} — 제외: {dropped} "
              f"(수집 실패로 집계됨 — 조용한 상실 방지)")

    for region_code, info in targets.items():
        params = {
            "latitude":  info["lat"],
            "longitude": info["lon"],
            "start_date": start_date,
            "end_date":   end_date,
            "daily": ",".join(active_vars),
            "timezone": "auto",
        }
        try:
            r = _fetch(OPEN_METEO_BASE, params=params)
            data = r.json()
            daily = data.get("daily", {})
            times = daily.get("time", [])
            if not times:
                print(f"[경고] {region_code}: Open-Meteo 응답에 'daily.time' 없음")
                fail_regions.append(region_code)
                continue

            for var in active_vars:
                values = daily.get(var, [])
                for t, v in zip(times, values):
                    if v is None:
                        continue
                    all_rows.append({
                        "price_date":     t,
                        "source_name":    "OpenMeteo/ERA5Land",
                        "region_code":    region_code,
                        "country":        info["country"],
                        # A-172: 지역 축을 코드에 반영 — 구 공유 코드는 동일 일자에
                        #   12개 지역 값이 충돌(mart 하드 실패 48,789건의 대부분)
                        "indicator_code": f"{var}_{region_code}",
                        "value":          float(v),
                        "unit":           OPEN_METEO_UNITS.get(var, ""),
                        "ingested_at":    ingested_at,
                    })
            # A-110(F3): 토양 2종을 hourly→일평균으로 복구해 동일 스키마로 합류.
            # 2026-09-13: tier2(근사 좌표)는 hourly 호출 생략 — 값 규모의 약 89%가
            #   토양 hourly라 부하 상한을 tier1에만 허용한다(좌표 확정 후 승격 검토).
            is_t1 = int(info.get("tier", 1)) == 1
            soil = (_fetch_hourly_soil(info["lat"], info["lon"]) if is_t1
                    else {v: {} for v in HOURLY_ONLY_VARS})
            n_soil = 0
            for var, by_date in soil.items():
                for t, v in by_date.items():
                    all_rows.append({
                        "price_date":     t,
                        "source_name":    "OpenMeteo/ERA5Land",
                        "region_code":    region_code,
                        "country":        info["country"],
                        "indicator_code": f"{var}_{region_code}",   # A-172 지역 접미
                        "value":          float(v),
                        "unit":           OPEN_METEO_UNITS.get(var, ""),
                        "ingested_at":    ingested_at,
                    })
                    n_soil += 1

            ok_regions.append(region_code)
            soil_note = (f" + 토양 {n_soil:,}건(hourly→일평균)" if is_t1
                         else " (tier2 — 토양 hourly 생략)")
            print(f"[완료] {region_code} ({info['country']}): {len(times)}일 × "
                  f"{len(active_vars)}변수{soil_note}")
            time.sleep(0.3)  # 요청 간격 (API 레이트 리밋 준수)
        except Exception as e:
            fail_regions.append(region_code)
            print(f"[경고] {region_code} 기후 수집 실패: {e}")

    # A-107: 지역 수집 여부를 **명시 리포트**한다 — 조용한 부분 실패 방지
    total = len(targets)
    print(f"[집계] 지역 수집 {len(ok_regions)}/{total}"
          + (f" · 실패: {', '.join(fail_regions)}" if fail_regions else " (전 지역 성공)"))

    if not all_rows:
        print("[경고] Open-Meteo 지역 기후: 수집된 데이터 없음")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    total_regions = df["region_code"].nunique()
    per_region = df.groupby("region_code")["price_date"].nunique().to_dict()
    print(f"[완료] Open-Meteo 지역 기후 총 {len(df):,}건 ({total_regions}/{total}개 지역, "
          f"{start_date}~{end_date})")
    print(f"[커버리지] 지역별 일수: {per_region}")
    return df


def fetch_openmeteo_forecast(
    regions: dict[str, dict[str, Any]] | None = None,
    forecast_days: int = 15,
    model: str = "best_match",
) -> pd.DataFrame:
    """Open-Meteo 예보 API — 산지 일별 예보(최대 16일) 수집. 참고 전용 층.

    행 규약(2026-09-14 개정, A-263): price_date = **발행일(수집일)** · valid_date = 유효일 ·
    lead_days = 유효일 − 발행일(0~16) · indicator_code = FCST_{var}_{region_code} ·
    source_vintage = 발행일. 산출은 관측 파케이가 아닌 **별도 파케이 climate_forecast_{date}**로
    저장한다(run() 참조).
    개정 근거: 구 규약(price_date=유효일·관측 파케이 동거)은 ①품질 게이트의 '미래 price_date'
    1,610건 실패(런 #99) ②마트가 같은 available_at의 15리드 중 최신 event_time 1행만 남겨
    14리드가 조용히 탈락하는 누락 구조를 만들었다. 발행일 키는 미래 일자를 없애고 리드별
    전 행을 보존해 30일 뒤 예보 skill 검증(관측 ERA5 대조)이 가능하다.
    예보는 관측 대체가 아니며 skill 검증 전 모델 투입 금지 — 마트·G1 FILE_PATTERNS 미등재.
    """
    targets = _select_regions(regions)
    if not targets:
        print("[경고] 예보 대상 산지 없음 — 건너뜀")
        return pd.DataFrame()
    forecast_days = max(1, min(int(forecast_days), 16))
    issue_date = date.today()
    ingested_at = pd.Timestamp.utcnow()
    rows: list[dict[str, Any]] = []
    ok: list[str] = []
    failed: list[str] = []
    print(f"[정보] 산지 예보 수집 — {len(targets)}개 지역 × {forecast_days}일 × "
          f"{len(FORECAST_VARS)}변수 (model={model}) · 호출 예상 {len(targets)}")
    for region_code, info in targets.items():
        params = {
            "latitude": info["lat"], "longitude": info["lon"],
            "daily": ",".join(FORECAST_VARS), "timezone": "UTC",
            "forecast_days": forecast_days, "models": model,
        }
        try:
            payload = _fetch(OPEN_METEO_FORECAST_BASE, params=params).json() or {}
            daily = payload.get("daily", {})
            times = daily.get("time", [])
            if not times:
                print(f"[경고] {region_code}: 예보 응답에 'daily.time' 없음")
                failed.append(region_code)
                continue
            n_before = len(rows)
            for var in FORECAST_VARS:
                for t, v in zip(times, daily.get(var) or []):
                    if v is None:
                        continue
                    valid = date.fromisoformat(str(t)[:10])
                    rows.append({
                        "price_date":     issue_date.isoformat(),   # 발행일 키(A-263)
                        "valid_date":     valid.isoformat(),
                        "lead_days":      (valid - issue_date).days,
                        "source_name":    FORECAST_SOURCE_NAME,
                        "region_code":    region_code,
                        "country":        info.get("country", region_code[:2]),
                        "indicator_code": f"{FORECAST_CODE_PREFIX}{var}_{region_code}",
                        "value":          float(v),
                        "unit":           OPEN_METEO_UNITS.get(var, ""),
                        "note":           (f"issue_date={issue_date.isoformat()} "
                                           f"lead_days={(valid - issue_date).days}"),
                        # vintage = 발행일 — attach_asof가 행 단위로 vintage_known=True 부여
                        "source_vintage": issue_date.isoformat(),
                        "ingested_at":    ingested_at,
                    })
            ok.append(region_code)
            print(f"[완료] {region_code} 예보 {len(times)}일 · {len(rows) - n_before}건")
        except Exception as e:   # 지역 단위 비치명 — 한 지역 실패가 전체를 죽이지 않게
            failed.append(region_code)
            print(f"[경고] {region_code} 예보 수집 실패: {type(e).__name__}: {str(e)[:80]}")
        time.sleep(0.3)
    print(f"[집계] 예보 지역 {len(ok)}/{len(targets)}"
          + (f" · 실패: {', '.join(failed)}" if failed else " (전 지역 성공)"))
    if not rows:
        print("[경고] Open-Meteo 예보: 수집된 데이터 없음")
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["valid_date"] = pd.to_datetime(df["valid_date"])
    return df


def fetch_weather_anomalies() -> pd.DataFrame:
    """OpenWeatherMap 원산지 기온·강수 이상 수집. 키 미등록 시 빈 DataFrame 반환."""
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        print("[경고] OPENWEATHERMAP_API_KEY 미등록 — 기상 이상 수집 건너뜀. openweathermap.org에서 무료 키 등록 필요.")
        return pd.DataFrame()

    rows = []
    today = date.today().isoformat()
    for location, coords in ORIGIN_COORDS.items():
        try:
            data = _fetch("https://api.openweathermap.org/data/2.5/weather", {
                "lat": coords["lat"], "lon": coords["lon"],
                "appid": api_key, "units": "metric",
            }).json()
            rows.append({
                "price_date":     today,
                "source_name":    "OpenWeatherMap",
                "region_code":    location,
                "country":        location.split("_")[0],
                "indicator_code": f"TEMP_{location}",
                "value":          data["main"]["temp"],
                "unit":           "°C",
            })
        except Exception as e:
            print(f"[경고] {location} 기상 데이터 수집 실패: {e}")
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


def fetch_ecmwf_era5() -> pd.DataFrame:
    """ECMWF CDS ERA5 — 원산지 월별 기온·강수 이상 (ECMWF_API_KEY 필요).
    ECMWF_API_KEY 형식: '{uid}:{key}' (Copernicus CDS 계정에서 발급)
    """
    # A-282: CDS v2 API는 폐기됐고(A-083 308/404 · A-100 'CDS 미사용' 확정) 실제 기후 수집원은
    #        Open-Meteo ERA5-Land(fetch_openmeteo_regional_climate)다. 키가 등록돼 있으면 이 함수가
    #        매 런 3지역 404 경고를 찍으며 죽은 엔드포인트를 호출했으므로 호출 자체를 중단한다.
    print("[정보] ECMWF CDS v2 경로는 폐기(A-100) — Open-Meteo ERA5-Land가 기후 수집원, 건너뜀")
    return pd.DataFrame()
    api_key = os.environ.get("ECMWF_API_KEY", "")   # pragma: no cover — 아래는 보존용 구 경로
    if not api_key:
        print("[경고] ECMWF_API_KEY 미등록 — ERA5 수집 건너뜀")
        return pd.DataFrame()
    rows = []
    today_iso = date.today().isoformat()
    for location, coord in ORIGIN_COORDS.items():
        try:
            r = httpx.get(
                "https://cds.climate.copernicus.eu/api/v2/resources/reanalysis-era5-land-monthly-means",
                headers={"Authorization": f"Basic {api_key}"},
                timeout=30,
            )
            if r.status_code == 200:
                data = r.json()
                rows.append({
                    "price_date":     today_iso,
                    "source_name":    "ECMWF_ERA5",
                    "region_code":    location,
                    "country":        location.split("_")[0],
                    "indicator_code": f"T2M_ANOMALY_{location}",
                    "value":          data.get("value", 0),
                    "unit":           "°C anomaly",
                })
            else:
                print(f"[경고] ECMWF ERA5 {location}: HTTP {r.status_code}")
        except Exception as e:
            print(f"[경고] ECMWF ERA5 {location} 수집 실패: {e}")
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


def run(start_year: int | None = None) -> None:
    # A-107: 기본값이 2017로 하드코딩돼 분석창(2010~, M-008)과 불일치했다.
    #        HISTORICAL_START_YEAR를 읽어 백필 워크플로우 지정 연도를 따르게 한다.
    if start_year is None:
        start_year = int(os.environ.get("HISTORICAL_START_YEAR", "2010"))
    # A-110(F4): 그러나 **일별 파이프라인이 매 실행마다 15년치를 재수집**하면
    #   12지역 × 8변수 × 약 6,000일이 되어 Open-Meteo 무료 티어 시간당 한도를 단일
    #   실행으로 초과한다(429 → 후반 지역 실패 → `지역 수집 7/12`가 매일 반복).
    #   백필 모드가 아니면 최근 N일 증분만 수집한다.
    backfill = os.environ.get("BACKFILL_MODE", "").lower() == "true"
    incr_days = int(os.environ.get("CLIMATE_INCREMENTAL_DAYS", "90"))
    if backfill:
        om_start = f"{start_year}-01-01"
        print(f"[C-03] 기후 수집 — 백필 모드: {om_start} ~ 현재")
    else:
        om_start = (date.today() - timedelta(days=incr_days)).isoformat()
        print(f"[C-03] 기후 수집 — 증분 모드: 최근 {incr_days}일({om_start}~). "
              f"전 구간 수집은 BACKFILL_MODE=true로 실행")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")
    frames = []

    # 1. ENSO 지수 (NOAA CPC ONI)
    enso = fetch_enso_index(start_year=start_year)
    if not enso.empty:
        frames.append(enso)

    # 2. Open-Meteo 산지 일별 기후 (config/production_regions.yaml — tier1 12 + tier2 11)
    regional = fetch_openmeteo_regional_climate(
        start_date=om_start,
        end_date=date.today().isoformat(),
    )
    if not regional.empty:
        frames.append(regional)

    # 2b. Open-Meteo 산지 15일 예보 (참고 전용 층 — 2026-09-13). 백필은 예보 개념이 없어
    #     건너뛰고, CLIMATE_FORECAST=0 으로 끌 수 있다(429 축소 절차의 첫 단계).
    forecast_on = os.environ.get("CLIMATE_FORECAST", "1").strip().lower() not in ("0", "false")
    if backfill:
        print("[정보] 백필 모드 — 산지 예보 수집 건너뜀(예보는 실시간 전용)")
    elif not forecast_on:
        print("[정보] CLIMATE_FORECAST=0 — 산지 예보 수집 비활성")
    else:
        forecast = fetch_openmeteo_forecast()
        if not forecast.empty:
            # A-263: 예보는 관측 파케이에 섞지 않고 별도 파일로 저장한다(품질 게이트·마트 분리).
            fout = f"{OUTPUT_DIR}/climate_forecast_{today}.parquet"
            forecast = attach_asof(forecast, source="CLIMATE")
            forecast.to_parquet(fout, index=False)
            print(f"[완료] 산지 예보 {len(forecast):,}건 저장 → {fout} (관측 파케이와 분리)")

    # 3. OpenWeatherMap 현재 기상 이상 (API 키 있을 때)
    owm = fetch_weather_anomalies()
    if not owm.empty:
        frames.append(owm)

    # 4. ECMWF ERA5 (API 키 있을 때)
    era5 = fetch_ecmwf_era5()
    if not era5.empty:
        frames.append(era5)

    if not frames:
        print("[경고] 기후 데이터: 수집된 항목 없음")
        return

    combined = pd.concat(frames, ignore_index=True)
    out = f"{OUTPUT_DIR}/climate_data_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="CLIMATE")
    combined.to_parquet(out, index=False)
    print(f"[완료] 기후 데이터 {len(combined):,}건 저장 → {out}")


if __name__ == "__main__":
    run()
