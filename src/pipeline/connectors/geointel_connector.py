"""
지정학 인텔리전스 커넥터 — WBS 1.1.33 (Shadowbroker 오픈소스 아키텍처 참조)
참조: github.com/BigBodyCobain/Shadowbroker (Python 62% / FastAPI / APScheduler)

Docker 없이 실행 가능한 이유:
  Shadowbroker는 Docker Compose 기반이나, 개별 데이터 피드는 순수 Python httpx GET 요청.
  본 커넥터는 APScheduler/FastAPI 레이어를 GitHub Actions cron으로 대체하여 구현.

수집 대상 (모두 무료 공개 API, Docker/설치 불필요):
  USGS 지진     — earthquake.usgs.gov (SBO 생산지·해협 반경 500km 내 규모2.5+)
  NOAA 기상경보 — api.weather.gov (미국 대두 생산 주 중서부 기상 위협)
  GDELT 이벤트  — api.gdeltproject.org (대두유·무역·관세 관련 지정학 이벤트)
  NASA FIRMS    — firms.modaps.eosdis.nasa.gov (NASA_FIRMS_MAP_KEY 선택적, 무료 가입)

유료/선택 API:
  AIS 탱커 데이터: ais_connector.py에서 별도 처리 (AISSTREAM_API_KEY)
  재무 데이터: commodity_connector.py (yfinance)

대두유 연관성:
  지진 → 항만 운영 중단 → 수출 지연 → CFR 프리미엄 상승
  기상경보 → 수확 차질 → 수급 불균형
  GDELT 이벤트 → 정책 변화 선행 신호 (수출세·수입관세)
  화재 → 인프라 손상 + 대두유 재배 면적 손실

실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions(external_data_refresh 일별 스케줄)
"""

from __future__ import annotations

import math
import os
from datetime import date

import httpx
import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

OUTPUT_DIR = "data/raw"

USGS_EQ_URL  = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
NOAA_URL     = "https://api.weather.gov/alerts/active"
GDELT_URL    = "https://api.gdeltproject.org/api/v2/doc/doc"
FIRMS_BASE   = "https://firms.modaps.eosdis.nasa.gov/api/country/csv"

# 대두유 공급망 핵심 지역 (지진 필터링 기준)
SBO_REGIONS: dict[str, dict[str, float]] = {
    "MATO_GROSSO_BR": {"lat": -13.0, "lon": -55.0, "radius_km": 500},
    "PAMPA_AR":       {"lat": -35.0, "lon": -63.0, "radius_km": 600},
    "IOWA_US":        {"lat":  41.9, "lon": -93.6, "radius_km": 400},
    "PANAMA_CANAL":   {"lat":   9.1, "lon": -79.7, "radius_km": 100},
    "HORMUZ":         {"lat":  26.5, "lon":  56.6, "radius_km": 200},
    "MALACCA":        {"lat":   2.0, "lon": 102.0, "radius_km": 300},
}

ALERT_SEVERITY = {"Extreme": 4, "Severe": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}

GDELT_QUERIES = [
    "soybean oil trade embargo",
    "argentina export tax soybean",
    "india palm oil import duty",
    "biodiesel mandate policy",
    "port strike grain export",
]

# 복합 지수 가중치 + 정규화 최댓값
# A-259 — GDELT 키를 "GDELT_SBO"→"GDELT_EVENT"로: 발행 코드 GDELT_EVENT_SCORE의 부분 문자열이라
#   _compute_composite 의 substring 매칭(가중 0.30·정규화 20)이 그대로 적용된다.
WEIGHTS   = {"SEISMIC": 0.30, "NOAA_WEATHER": 0.20, "GDELT_EVENT": 0.30, "FIRMS_FIRE": 0.20}
MAX_NORMS = {"SEISMIC": 7.0,  "NOAA_WEATHER": 4.0,  "GDELT_EVENT": 20.0, "FIRMS_FIRE": 200.0}


def _retry_get(url: str, params: dict | None = None, timeout: int = 30) -> httpx.Response:
    """외부 API 호출 — 지수 백오프 4회 재시도 (data_pipeline.md 표준 패턴)."""
    import time
    delay = 2
    for attempt in range(4):
        try:
            r = httpx.get(url, params=params or {}, timeout=timeout)
            r.raise_for_status()
            return r
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == 3:
                raise RuntimeError(f"[오류] API 호출 실패 ({url}): {e}") from e
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"[오류] 재시도 한도 초과: {url}")


def _nearest_region(lat: float, lon: float) -> str | None:
    """좌표가 SBO 핵심 공급망 지역 반경 내에 있으면 지역명, 없으면 None."""
    for name, r in SBO_REGIONS.items():
        dist_km = math.sqrt((lat - r["lat"]) ** 2 + (lon - r["lon"]) ** 2) * 111
        if dist_km <= r["radius_km"]:
            return name
    return None


def _make_row(indicator: str, value: float, unit: str, note: str) -> dict:
    return {
        "price_date":     date.today().isoformat(),
        "source_name":    "GeoIntel",
        "indicator_code": indicator,
        "value":          value,
        "unit":           unit,
        "note":           note,
    }


def _to_df(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"]  = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


def fetch_usgs_earthquakes() -> pd.DataFrame:
    """USGS 지진 데이터 — SBO 공급망 핵심 지역 반경 내 규모 2.5+ 이벤트.

    Shadowbroker earth_observation.py 패턴 참조 (API 키 불필요).
    """
    try:
        data = _retry_get(USGS_EQ_URL).json()
    except RuntimeError as e:
        print(f"[경고] USGS 지진 수집 실패: {e}")
        return pd.DataFrame()

    rows = []
    for f in data.get("features", []):
        props = f.get("properties", {})
        geo   = f.get("geometry", {}).get("coordinates", [])
        if len(geo) < 2:
            continue
        region = _nearest_region(geo[1], geo[0])
        if region is None:
            continue
        mag = float(props.get("mag") or 0.0)
        rows.append(_make_row(
            f"SEISMIC_{region}_MAG", mag, "magnitude",
            f"[GEOINTEL:USGS] {props.get('place', region)} M{mag} — SBO 공급망 리스크",
        ))
    # A-216 예방: 같은 지역에 하루 복수 지진이면 동일 코드 복수 행 → mart 값충돌.
    # 지역별 최대 규모 1행으로 집계(리스크 지표 의미론), 건수는 note에 보존.
    if rows:
        best: dict[str, dict] = {}
        counts: dict[str, int] = {}
        for r in rows:
            code = r["indicator_code"]
            counts[code] = counts.get(code, 0) + 1
            if code not in best or r["value"] > best[code]["value"]:
                best[code] = r
        rows = []
        for code, r in best.items():
            if counts[code] > 1:
                r["note"] = f"[집계 {counts[code]}건·최대 규모] " + str(r.get("note", ""))[:300]
            rows.append(r)
    print(f"[완료] USGS 지진 — 지역별 최대 규모 {len(rows)}행 (SBO 반경 내)")
    return _to_df(rows)


def fetch_noaa_weather_alerts() -> pd.DataFrame:
    """NOAA 기상 경보 — 미국 중서부 대두 생산 주 Moderate 이상 경보.

    Shadowbroker infrastructure.py 패턴 참조 (API 키 불필요).
    """
    try:
        r = _retry_get(NOAA_URL, params={"area": "IA,IL,IN,OH,MO,KS,NE,MN", "status": "actual"})
        features = r.json().get("features", [])
    except RuntimeError as e:
        print(f"[경고] NOAA 기상경보 수집 실패: {e}")
        return pd.DataFrame()

    # A-216: 같은 날 복수 경보가 하나의 지표코드로 복수 행 발행 → mart 값충돌 하드 실패
    # (런 #79·#80 Readiness RuntimeError — D-033 게이트 정당 차단). 일 단위 1행으로 집계:
    # 값 = 최대 심각도(경보 지표의 의미론), 건수·이벤트 목록은 note에 보존(S-5).
    alerts = []
    for f in features[:20]:
        props    = f.get("properties", {})
        severity = ALERT_SEVERITY.get(props.get("severity", "Unknown"), 0)
        if severity < 2:
            continue
        alerts.append((severity, props.get("event", "경보"), props.get("areaDesc", "중서부")))
    if not alerts:
        print("[완료] NOAA 기상경보 0건 (Moderate+)")
        return pd.DataFrame()
    max_sev = max(a[0] for a in alerts)
    events = " · ".join(f"{e}({a[:40]})" for _, e, a in alerts[:5])
    rows = [_make_row(
        "NOAA_WEATHER_ALERT_SEVERITY", float(max_sev),
        "1=Minor/2=Mod/3=Sev/4=Ext",
        f"[GEOINTEL:NOAA] 경보 {len(alerts)}건 · 최대 심각도 {max_sev} — {events}",
    )]
    print(f"[완료] NOAA 기상경보 {len(alerts)}건 → 일 단위 최대 심각도 1행 집계 (Moderate+)")
    return _to_df(rows)


def fetch_gdelt_sbo_events() -> pd.DataFrame:
    """GDELT 지정학 이벤트 — 대두유 무역/관세/정책 관련 24시간 이벤트 수.

    Shadowbroker news.py 패턴 참조 (API 키 불필요).
    발행 코드는 GDELT_EVENT_SCORE — A-259: 코드명을 소비자(chokepoints.yaml·digest·ontology·
    brief)와 일치시킴, 값 의미는 기사 수 합산(5쿼리×최대 5건 = 0~25). 구 코드
    GDELT_SBO_EVENT_COUNT 는 어느 소비자도 읽지 않아 해상 위협 경보 원천이 발화하지 않았다.
    """
    import time

    # A-142: GDELT 무료 API는 초당/분당 레이트리밋이 엄격 — 쿼리 간 6초 + 429 재시도.
    # A-220: 런 #80·#81에서 5쿼리 중 4개가 'SSL handshake timed out'으로 누락 —
    #   구 코드는 timeout=20 + 예외 시 즉시 break(타임아웃 무재시도). GDELT는 부하
    #   시간대에 응답이 느린 것으로 실측 → timeout 60s + 타임아웃·전송오류에도
    #   최대 3회 재시도(10→20s 백오프, 매 시도 새 커넥션).
    rows = []
    query_counts: list[tuple[str, int]] = []
    for i, query in enumerate(GDELT_QUERIES):
        if i > 0:
            time.sleep(6)   # 쿼리 간 최소 간격 (GDELT 레이트리밋 회피)
        params = {
            "query": query, "mode": "artlist",
            "maxrecords": "5", "format": "json", "timespan": "1d",
        }
        for attempt in range(3):
            try:
                # 매 시도 새 클라이언트 — SSL 핸드셰이크 타임아웃 시 커넥션 재사용 방지
                with httpx.Client(timeout=httpx.Timeout(60, connect=20)) as _c:
                    r = _c.get(GDELT_URL, params=params)
                if r.status_code == 429:
                    if attempt < 2:
                        print(f"[정보] GDELT 429 ('{query[:30]}') — 30초 대기 후 재시도")
                        time.sleep(30)
                        continue
                    print(f"[경고] GDELT '{query[:30]}' 재시도 후에도 429 — 건너뜀")
                    break
                r.raise_for_status()
                count = len(r.json().get("articles", []))
                if count > 0:
                    # A-242: 쿼리별 행을 그대로 append하면 같은 날 동일 코드에 복수 값
                    # → mart 값충돌 하드 실패(런 #84 — A-220 재시도 수정으로 복수 쿼리
                    # 성공이 처음 가능해지며 드러난 잠재 결함). 루프 밖에서 일 단위
                    # 합산 1행으로 집계한다(쿼리별 내역은 note 보존 — A-216 NOAA 동일 원리).
                    query_counts.append((query[:40], count))
                break
            except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
                if attempt < 2:
                    wait = 10 * (attempt + 1)
                    print(f"[정보] GDELT '{query[:30]}' 오류({type(e).__name__}) — {wait}s 후 재시도")
                    time.sleep(wait)
                    continue
                print(f"[경고] GDELT '{query[:30]}' 3회 실패: {e}")
                break
    if query_counts:
        total = sum(c for _, c in query_counts)
        detail = " · ".join(f"'{q}' {c}건" for q, c in query_counts)
        # A-259 — 코드명을 소비자(chokepoints.yaml·digest·ontology·brief)와 일치시킴,
        #   값 의미는 기사 수 합산(단위 문자열에 범위 명시).
        rows.append(_make_row(
            "GDELT_EVENT_SCORE", float(total), "articles/day (5쿼리×최대5건 합산, 0~25)",
            f"[GEOINTEL:GDELT] {len(query_counts)}/{len(GDELT_QUERIES)}쿼리 합산 — {detail}",
        ))
    if query_counts:
        print(f"[완료] GDELT 이벤트 {len(query_counts)}/{len(GDELT_QUERIES)}개 쿼리 성공 → 일 합산 1행")
    else:   # 성공 쿼리 0개면 행을 만들지 않음 — '완료'로 보이지 않게 경고로 남김(Codex 교차검증 지적)
        print(f"[경고] GDELT 성공 쿼리 0/{len(GDELT_QUERIES)}개 — 오늘 GDELT 행 없음(이전 값으로 진행)")
    return _to_df(rows)


def fetch_nasa_firms_fires() -> pd.DataFrame:
    """NASA FIRMS 산불/화재 — SBO 주요 생산국 화재 감지 건수.

    NASA_FIRMS_MAP_KEY 미등록 시 건너뜀 (firms.modaps.eosdis.nasa.gov 무료 가입 후 발급).
    Shadowbroker earth_observation.py 패턴 참조.
    """
    firms_key = os.environ.get("NASA_FIRMS_MAP_KEY", "").strip()
    if not firms_key:
        print("[정보] NASA_FIRMS_MAP_KEY 미등록 — FIRMS 산불 건너뜀 (무료 가입: firms.modaps.eosdis.nasa.gov)")
        return pd.DataFrame()

    today = date.today().isoformat()
    rows  = []
    for country in ("BRA", "ARG", "USA", "IDN", "MYS"):
        try:
            url = f"{FIRMS_BASE}/{firms_key}/VIIRS_SNPP_NRT/{country}/1/{today}"
            text = _retry_get(url).text
            count = sum(1 for ln in text.split("\n") if ln and not ln.startswith("latitude"))
            if count > 0:
                rows.append(_make_row(
                    f"FIRMS_FIRE_COUNT_{country}", float(count), "hotspots/day",
                    f"[GEOINTEL:FIRMS] VIIRS 위성 화재 — {country} {count}건",
                ))
        except RuntimeError as e:
            print(f"[경고] NASA FIRMS {country} 실패: {e}")
    print(f"[완료] NASA FIRMS 산불 {len(rows)}개 국가")
    return _to_df(rows)


def _compute_composite(frames: list[pd.DataFrame]) -> list[dict]:
    """USGS + NOAA + GDELT + FIRMS 신호를 종합한 GeoIntel 복합 지수 산출 (0-100)."""
    all_rows: list[dict] = []
    for f in frames:
        all_rows.extend(f.to_dict("records"))

    signals: dict[str, float] = {k: 0.0 for k in WEIGHTS}
    for row in all_rows:
        code = str(row.get("indicator_code", ""))
        val  = float(row.get("value", 0.0))
        for key in WEIGHTS:
            if key in code:
                signals[key] = max(signals[key], val)

    composite = sum(
        WEIGHTS[k] * min(1.0, signals[k] / MAX_NORMS[k])
        for k in WEIGHTS if MAX_NORMS[k] > 0
    ) * 100.0
    return [_make_row(
        "GEOINTEL_RISK_COMPOSITE", round(composite, 1),
        "0-100 (높을수록 공급망 리스크)",
        f"[COMPOSITE: 지진30%+기상20%+GDELT30%+화재20% | {signals}]",
    )]


def run() -> None:
    """지정학 인텔리전스 수집 및 복합 지수 산출. BACKFILL_MODE에서는 건너뜀."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")

    if os.environ.get("BACKFILL_MODE", "").lower() == "true":
        print("[정보] BACKFILL_MODE 활성화 — GeoIntel 실시간 전용 데이터 건너뜀")
        return

    frames: list[pd.DataFrame] = []
    for fetcher, label in [
        (fetch_usgs_earthquakes,    "USGS 지진"),
        (fetch_noaa_weather_alerts, "NOAA 기상경보"),
        (fetch_gdelt_sbo_events,    "GDELT 이벤트"),
        (fetch_nasa_firms_fires,    "NASA FIRMS"),
    ]:
        try:
            df = fetcher()
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"[경고] {label} 수집 실패: {e}")

    if frames:
        composite = _to_df(_compute_composite(frames))
        frames.append(composite)

    if not frames:
        print("[경고] GeoIntel: 수집된 데이터 없음 — 네트워크 또는 API 상태 확인")
        return

    df = pd.concat(frames, ignore_index=True)
    out = f"{OUTPUT_DIR}/geointel_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    df = attach_asof(df, source="GEOINTEL")
    df.to_parquet(out, index=False)
    print(f"[완료] GeoIntel 지정학 인텔리전스 {len(df)}건 → {out}")


if __name__ == "__main__":
    run()
