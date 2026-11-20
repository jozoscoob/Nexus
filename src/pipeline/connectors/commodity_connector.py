"""
상품 가격 커넥터 — WBS 1.1.2 보완 (D-002 P0 갭 해소)
수집 대상:
  - CBOT 대두유 선물 BO=F: yfinance (기본) → Nasdaq Data Link CHRIS/CME_BO1 (폴백)
  - 팜유 글로벌 벤치마크: FRED PPOILUSDM (월별, CPO 대리지표)
  - ARS/USD 공식 환율: api.bcra.gob.ar (인증 불필요)
  - 미국 가뭄 지수 D0-D4: drought.gov USDM API (인증 불필요, 주별 갱신)
실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions
참고 MEMORY: D-002 (P0 데이터갭), M-002 (T+2 FX 오프셋)
"""
from __future__ import annotations

import os
import time
from datetime import date, timedelta

import httpx
import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof, drop_future_observations  # noqa: E402

OUTPUT_DIR = "data/raw"

# ── USDM 가뭄 지수 대상 주 (미국 대두 Top-5 생산 주) ────────────────────────
SOY_STATES_US = ["IA", "IL", "IN", "MN", "NE"]

# ── Nasdaq Data Link 주의 사항 ──────────────────────────────────────────────
# NASDAQ_DATALINK_API_KEY: CHRIS/CME_BO1 (대두유 선물)은 Nasdaq 인수 후 2018년 삭제됨
# BDI: Nasdaq Data Link에서 제공한 적 없음 (Baltic Exchange 라이선스 — Bloomberg/Refinitiv 전용)
# 이 키는 기타 Nasdaq 독점 데이터셋(예: AMTR, ZILL)에만 사용 가능
# BO=F 대안: yfinance(무료, IP 차단 위험) → 유료는 Databento($5-25/mo), Barchart OnDemand
# BDI 대안: Perplexity(현행), Trading Economics API($65-200/mo), Baltic Exchange Direct(엔터프라이즈)
NASDAQ_BASE = "https://data.nasdaq.com/api/v3/datasets"


def _get(url: str, params: dict | None = None, headers: dict | None = None,
         max_retries: int = 4) -> httpx.Response:
    delay = 2
    for attempt in range(max_retries):
        try:
            r = httpx.get(url, params=params or {}, headers=headers or {},
                          timeout=30)
            r.raise_for_status()
            return r
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"[오류] API 호출 실패 ({url}): {e}") from e
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"[오류] API 호출 반복 실패 ({url})")


# ── 1. CBOT 대두유 선물 (BO=F) ──────────────────────────────────────────────

def _yf_session():
    """curl_cffi 브라우저 임퍼소네이션 세션 — Yahoo 레이트리밋/차단 완화 (A-071).
    원인①: yfinance 기본 requests가 Yahoo에 429(레이트리밋)·차단 유발.
    해결: curl_cffi로 실제 브라우저 TLS 지문(impersonate) 모방 → 429 대폭 감소.
    미설치 시 None 반환(기본 세션 사용).
    """
    try:
        from curl_cffi import requests as cffi_requests
        return cffi_requests.Session(impersonate="chrome")
    except ImportError:
        print("[정보] curl_cffi 미설치 — 기본 세션 사용(429 위험). pip install curl_cffi 권장")
        return None


# A-151: BO=F는 야후에서 상장폐지(possibly delisted) 표기, ZL=F가 현행 CBOT 대두유 심볼.
#        같은 실행에서 검증기가 ZL=F period=max 6,565일 수집 성공 → ZL=F 1순위, BO=F 폴백 강등.
YF_SBO_SYMBOLS: tuple[str, ...] = ("ZL=F", "BO=F")


def fetch_bo_futures_yfinance(days_back: int = 10) -> pd.DataFrame:
    """CBOT 대두유 선물 일간 OHLCV — yfinance + curl_cffi 세션 (A-071).

    심볼 체인(A-151): ZL=F(현행) → BO=F(구 심볼, 야후 상장폐지 표기 — 폴백만 유지).
    지표코드는 하위 호환을 위해 CBOT_BO_* 접두를 유지한다(다운스트림 FILE_PATTERNS 불변).

    미수집 원인·해결(조정자 확인):
      ① 레이트리밋(429) → curl_cffi 브라우저 임퍼소네이션 세션 사용(하단 _yf_session).
      ② 사내 IP 방화벽 → yfinance 요청 도메인(query1/2.finance.yahoo.com) 승인 요청 필요
         (담당자 방화벽 허용). Actions runner는 사내망 밖이라 ②는 해당 없음.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("[경고] yfinance 미설치 — CBOT 대두유 yfinance 건너뜀 (Nasdaq Data Link 폴백 사용)")
        return pd.DataFrame()

    session = _yf_session()
    for symbol in YF_SBO_SYMBOLS:                      # A-151: ZL=F 우선
        delay = 10
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol, session=session) if session else yf.Ticker(symbol)
                # A-158: 백필인데 "10d"만 수집되던 원인 — days_back 기본값이 증분용.
                #   BACKFILL_MODE에서는 HISTORICAL_START_YEAR부터 전체 창을 요청한다.
                if os.environ.get("BACKFILL_MODE", "").lower() == "true":
                    _start = f"{os.environ.get('HISTORICAL_START_YEAR', '2010')}-01-01"
                    df = ticker.history(start=_start, auto_adjust=True)
                else:
                    df = ticker.history(period=f"{days_back}d", auto_adjust=True)
                if df.empty:
                    print(f"[경고] {symbol} yfinance: 데이터 없음 — 다음 심볼 시도")
                    break
                df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
                df.index.name = "price_date"
                df = df.reset_index()
                df["price_date"] = pd.to_datetime(df["price_date"]).dt.tz_localize(None)
                result = df.melt(id_vars=["price_date"], var_name="indicator_code", value_name="value")
                result["source_name"] = f"yfinance/CME_{symbol.split('=')[0]}"
                # 지표코드 CBOT_BO_* 유지 — 심볼 교체가 다운스트림 분석 코드를 깨지 않게(A-151)
                # A-165: 캐노니컬 타깃명(CBOT_BO_CLOSE)은 세션 종가 검증기(A-145/A-156)가
                #   계약 필드(target_eligible·time_basis)와 함께 발행하는 전유물 —
                #   미검증 yfinance 경로가 같은 이름을 쓰면 C-08 타깃 하드 계약이
                #   REJECTED로 파이프라인을 중단시킨다(런 31753575819 실증).
                result["indicator_code"] = "CBOT_BO_YF_" + result["indicator_code"].str.upper()
                result["unit"] = "USc/lb"
                result["ingested_at"] = pd.Timestamp.utcnow()
                print(f"[정보] CBOT 대두유 선물 수집 성공 (심볼: {symbol}, {days_back}d)")
                return result
            except Exception as e:
                if "429" in str(e) or "RateLimit" in str(e) or "Too Many" in str(e):
                    print(f"[경고] Yahoo Finance 레이트 리밋 ({symbol} 시도 {attempt + 1}/3): {e}")
                    if attempt < 2:
                        time.sleep(delay)
                        delay *= 2
                else:
                    print(f"[경고] {symbol} yfinance 실패: {e} — 다음 심볼 시도")
                    break
    return pd.DataFrame()


def fetch_krw_usd_yfinance(days_back: int = 400) -> pd.DataFrame:
    """원/달러 일별 종가 — yfinance KRW=X(2026-11-20 신설).

    화면의 원화 환산이 FRED DEXKOUS(주 1회 일괄 게시 → 최대 1주 지연)에 묶여 11/13에 멈춰 있던 문제 대응.
    실패해도 비치명 — 화면은 DEXKOUS로 대체하고 기준일을 그대로 표시한다.
    """
    try:
        import yfinance as yf
    except ImportError:
        return pd.DataFrame()
    session = _yf_session()
    try:
        t = yf.Ticker("KRW=X", session=session) if session else yf.Ticker("KRW=X")
        h = t.history(period=f"{days_back}d", auto_adjust=False)
    except Exception as e:  # 네트워크·레이트리밋 — 비치명
        print(f"[경고] 원/달러(KRW=X) 수집 실패: {e} — FRED DEXKOUS로 대체")
        return pd.DataFrame()
    h = h.dropna(subset=["Close"])
    if h.empty:
        print("[경고] 원/달러(KRW=X) 데이터 없음 — FRED DEXKOUS로 대체")
        return pd.DataFrame()
    out = pd.DataFrame({"price_date": pd.to_datetime(h.index).tz_localize(None).normalize(),
                        "indicator_code": "FX_KRW_USD_YF", "value": h["Close"].astype(float).to_numpy(),
                        "unit": "KRW per USD", "source_name": "yfinance/KRW=X", "ingested_at": pd.Timestamp.utcnow()})
    out = out.drop_duplicates("price_date", keep="last")
    print(f"[정보] 원/달러 일별 {len(out)}일 수집(최신 {out['price_date'].max():%Y-%m-%d})")
    return out


def fetch_cbot_soybean_oil(days_back: int = 10) -> pd.DataFrame:
    """CBOT 대두유 선물 종합 수집 — yfinance(무료, IP차단 위험).
    심볼: ZL=F 1순위, BO=F 폴백 (A-151 — BO=F는 야후 상장폐지 표기).
    유료 대안: Databento(CME ZL 일간 $5-25/mo) · Barchart OnDemand.
    Nasdaq DataLink CHRIS/CME_BO1: 2018년 삭제 — 사용 불가.
    """
    df = fetch_bo_futures_yfinance(days_back)
    if df.empty:
        print("[경고] CBOT 대두유(ZL=F/BO=F) 수집 실패 — 유료 대안(Databento/Barchart) 도입 검토 필요")
    return df


# ── 2. 팜유 글로벌 벤치마크 (FRED PPOILUSDM — 월별, CPO 대리지표) ────────────

def fetch_cpo_proxy_fred(start: str = "2017-01-01") -> pd.DataFrame:
    """
    IMF 팜유 글로벌 벤치마크 (FRED PPOILUSDM) — 한국 CIF CPO 대리 지표.
    주의: 월별 데이터. 실제 한국 CIF 가격은 MPOB/Reuters 수동 수집 필요.
    """
    api_key = os.environ.get("FRED_API_KEY", "")
    if not api_key:
        print("[경고] FRED_API_KEY 미등록 — CPO 프록시 건너뜀")
        return pd.DataFrame()
    try:
        r = _get("https://api.stlouisfed.org/fred/series/observations", params={
            "series_id": "PPOILUSDM",
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start,
        })
        obs = r.json().get("observations", [])
        if not obs:
            return pd.DataFrame()
        df = pd.DataFrame(obs)[["date", "value"]]
        df.columns = ["price_date", "value"]
        df["price_date"] = pd.to_datetime(df["price_date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["source_name"] = "FRED"
        df["indicator_code"] = "CPO_GLOBAL_USD_MT_PROXY"
        df["unit"] = "USD/mt"
        df["ingested_at"] = pd.Timestamp.utcnow()
        return df.dropna(subset=["value"])
    except Exception as e:
        print(f"[경고] FRED CPO 프록시 수집 실패: {e}")
        return pd.DataFrame()


# ── 3. ARS/USD 공식 환율 (api.bcra.gob.ar — 인증 불필요) ─────────────────────

# A-144: /estadisticas/v3.0/cotizaciones/{date} 404 — 엔드포인트 개편 추정.
#        신규 estadisticascambiarias/v1.0 (기간 조회) 우선, 구 v3.0 폴백 체인.
def _bcra_extract_rate(entry: dict) -> float | None:
    """BCRA 응답 상세 항목에서 환율 숫자 필드 유연 추출 (A-144).

    알려진 필드(tipoCotizacion/tipoPase) 우선, 없으면 첫 양수 숫자 필드 자동 탐지.
    """
    for key in ("tipoCotizacion", "tipoPase"):
        v = entry.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    for v in entry.values():
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
            return float(v)
    return None


def _fetch_bcra_v1_range(start: date, end: date) -> list[dict]:
    """BCRA estadisticascambiarias v1.0 — USD 기간 조회 (단일 호출)."""
    url = (
        "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD"
        f"?fechadesde={start.isoformat()}&fechahasta={end.isoformat()}"
    )
    r = _get(url, headers={"Accept": "application/json"}, max_retries=2)
    data = r.json()
    results = data.get("results", data if isinstance(data, list) else [])
    rows: list[dict] = []
    for item in results:
        fecha = item.get("fecha") or item.get("fechaCotizacion")
        detalles = item.get("detalle", [item])   # detalle 없으면 항목 자체를 상세로 간주
        for entry in detalles:
            rate = _bcra_extract_rate(entry)
            if fecha and rate is not None:
                rows.append({
                    "price_date":     fecha,
                    "source_name":    "BCRA_OFICIAL",
                    "indicator_code": "ARS_USD_OFICIAL",
                    "value":          rate,
                    "unit":           "ARS/USD",
                })
                break
    if rows:
        print(f"[정보] BCRA 성공 URL: {url} ({len(rows)}건)")
    return rows


def fetch_ars_usd_bcra(days_back: int = 10) -> pd.DataFrame:
    """
    아르헨티나 중앙은행(BCRA) 공식 ARS/USD 환율 (A-144: 후보 엔드포인트 체인).
    ① estadisticascambiarias/v1.0/Cotizaciones/USD (기간 조회, 신규)
    ② estadisticas/v3.0/cotizaciones/{date} (일별, 구 — 폴백)
    """
    start = date.today() - timedelta(days=days_back)
    rows: list[dict] = []

    # ① v1.0 기간 조회 (단일 호출)
    try:
        rows = _fetch_bcra_v1_range(start, date.today())
    except Exception as e:
        print(f"[경고] BCRA v1.0 기간 조회 실패: {e} — 구 v3.0 폴백 시도")

    # ② 구 v3.0 일별 폴백
    if not rows:
        v3_logged = False
        for d in range(days_back):
            target = date.today() - timedelta(days=d)
            if target.weekday() >= 5:  # 주말 건너뜀
                continue
            url = f"https://api.bcra.gob.ar/estadisticas/v3.0/cotizaciones/{target.isoformat()}"
            try:
                r = _get(url, headers={"Accept": "application/json"}, max_retries=2)
                data = r.json()
                for entry in data.get("results", []):
                    if entry.get("codigoMoneda") == "USD":
                        rate = _bcra_extract_rate(entry)
                        if rate is not None:
                            rows.append({
                                "price_date":     target.isoformat(),
                                "source_name":    "BCRA_OFICIAL",
                                "indicator_code": "ARS_USD_OFICIAL",
                                "value":          rate,
                                "unit":           "ARS/USD",
                            })
                            if not v3_logged:
                                print(f"[정보] BCRA 성공 URL(폴백 v3.0): {url}")
                                v3_logged = True
                        break
            except Exception as e:
                print(f"[경고] BCRA ARS/USD {target}: {e}")

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


# ── 4. 미국 가뭄 지수 D0-D4 (USDM API — 인증 불필요, 주별 갱신) ─────────────

DROUGHT_API = (
    "https://usdmdataservices.unl.edu/api/"
    "StateStatistics/GetDroughtSeverityStatisticsByArea"
)

def fetch_us_drought_stats(states: list[str] = SOY_STATES_US,
                           lookback_days: int = 21) -> pd.DataFrame:
    """
    미국 가뭄 모니터 D0-D4 통계 — drought.gov USDM API (인증 불필요).
    대두 주요 생산 주: Iowa·Illinois·Indiana·Minnesota·Nebraska.
    갱신 주기: 매주 목요일. 일간 파이프라인에서 동일 주 중복 저장 허용 (idempotent).
    """
    end   = date.today()
    start = end - timedelta(days=lookback_days)
    rows  = []
    for state in states:
        try:
            r = _get(DROUGHT_API, params={
                "aoi":            state,
                "startdate":      start.strftime("%-m/%-d/%Y"),
                "enddate":        end.strftime("%-m/%-d/%Y"),
                "statisticsType": 2,  # 배타적(exclusive) 카테고리
            }, headers={"Accept": "application/json"})
            entries = r.json()
            for entry in entries:
                map_date = entry.get("MapDate", "")
                if not map_date:
                    continue
                for level in ["None", "D0", "D1", "D2", "D3", "D4"]:
                    val = entry.get(level)
                    if val is None:
                        continue
                    rows.append({
                        "price_date":     map_date[:10],  # YYYY-MM-DD
                        "source_name":    "USDM_drought.gov",
                        "indicator_code": f"DROUGHT_{level}_{state}",
                        "region":         state,
                        "country":        "US",
                        "value":          float(val),
                        "unit":           "% of area",
                    })
        except Exception as e:
            print(f"[경고] USDM 가뭄 지수 {state} 수집 실패: {e}")
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


# A-150: TE 하드코딩 심볼 추측(cpo/palm-oil 등) 실패 대응 — 검색 API로 실제 심볼 자기발견.
#        shipping_connector._te_discover_symbols와 동일 패턴 (잡별 의존성 격리를 위해 중복 정의
#        — shipping은 openai 의존, commodity 잡 pip에는 openai 없음).
def _te_discover_symbols(te_key: str, search_term: str,
                         name_keywords: tuple[str, ...]) -> list[str]:
    """TE 심볼 자기발견 (A-150).

    ① GET /markets/search/{search_term} → ② 실패 시 GET /markets/commodities 폴백.
    이름에 name_keywords가 모두 포함된 항목의 Symbol 필드를 추출해 로그로 남긴다.
    심볼 필드명은 'Symbol'(대문자) 우선, 소문자 'symbol' 폴백.
    발견 실패 시 빈 리스트 반환 — 호출부는 기존 추측 체인으로 폴백한다.
    """
    from urllib.parse import quote

    candidates: list = []
    urls = (
        f"https://api.tradingeconomics.com/markets/search/{quote(search_term)}",
        "https://api.tradingeconomics.com/markets/commodities",
    )
    for url in urls:
        try:
            r = httpx.get(url, params={"c": te_key}, timeout=30)
            if r.status_code != 200:
                print(f"[정보] TE 심볼 검색 HTTP {r.status_code} ({url.rsplit('/', 1)[-1]}) — 다음 방식 시도")
                continue
            data = r.json()
            if isinstance(data, list) and data:
                candidates = data
                break
        except Exception as e:
            print(f"[정보] TE 심볼 검색 실패 ({url.rsplit('/', 1)[-1]}): {e}")

    symbols: list[str] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name") or item.get("name") or "")
        if all(kw.lower() in name.lower() for kw in name_keywords):
            sym = item.get("Symbol") or item.get("symbol")  # 대문자 우선 (A-150)
            if sym and str(sym) not in symbols:
                symbols.append(str(sym))
    # A-159: 검색 결과에 기업 주가가 섞인다(실측: 'palm oil' 검색 1위가 OKOMUOIL:NL —
    #   Okomu Oil Palm **주식**). TE 심볼 접미사가 자산 유형을 나타내므로(:COM=상품,
    #   :IND=지수, 그 외=주식 등) 상품·지수를 앞으로 정렬해 주가 오선택을 차단한다.
    symbols.sort(key=lambda x: (0 if x.endswith(":COM") else 1 if x.endswith(":IND") else 2))
    if symbols:
        print(f"[정보] TE 심볼 자기발견({search_term}): {symbols} (:COM/:IND 우선 정렬 — A-159)")
    else:
        print(f"[정보] TE 심볼 자기발견 실패({search_term}) — 기존 추측 체인으로 폴백")
    return symbols


# A-282: TE 팜유 상품 호가(PLO:COM)는 Bursa Malaysia 선물 — 단위 MYR/MT. 구 코드는 이를 CPO_USD_MT
#        (USD/MT)로 적재해 FRED 달러 프록시와 같은 코드에 섞었고, 상품 심볼이 409면 검색 결과의
#        **기업 주가(OKOMUOIL:NL)** 로 넘어가 주가를 팜유 가격으로 적재했다(런 #113 실측 2,323건).
CPO_TE_INDICATOR = "CPO_MYR_MT"
CPO_MYR_PLAUSIBLE = (1_500.0, 9_000.0)     # Bursa CPO 3개월물 MYR/MT 관측 범위(2010~2026)의 여유 폭


def _te_commodity_symbols(symbols: list[str]) -> list[str]:
    """자기발견 결과에서 상품(:COM) 심볼만 남긴다 — 지수·주식 폴백 금지(A-282)."""
    return [s for s in symbols if s.endswith(":COM")]


def _parse_te_dates(series: pd.Series) -> pd.Series:
    """TE REST 날짜 파싱 — dd/mm/yyyy 우선(추론 의존 금지), 실패분은 ISO로 재시도(A-282)."""
    first = pd.to_datetime(series, format="%d/%m/%Y", errors="coerce")
    missing = first.isna()
    if missing.any():
        first = first.where(~missing, pd.to_datetime(series[missing], errors="coerce", format="ISO8601"))
    return first


def _fetch_cpo_te_rest(te_key: str, start_date: str = "2017-01-01") -> pd.DataFrame:
    """TE REST /markets/historical/{symbol} — 자기발견 심볼로 CPO 히스토리 수집 (A-150)."""
    discovered = _te_commodity_symbols(_te_discover_symbols(te_key, "palm oil", ("palm", "oil")))
    if not discovered:
        print("[정보] TE 팜유 상품(:COM) 심볼 없음 — 주가·지수 폴백 금지(A-282), FRED 프록시로")
        return pd.DataFrame()
    _end = date.today().isoformat()
    for symbol in discovered:
        try:
            r = httpx.get(
                f"https://api.tradingeconomics.com/markets/historical/{symbol}",
                params={"c": te_key, "d1": start_date, "d2": _end, "f": "json"},
                timeout=30,
            )
            if r.status_code != 200:
                print(f"[정보] TE CPO({symbol}) HTTP {r.status_code} — 다음 심볼 시도")
                continue
            data = r.json()
            if not data or not isinstance(data, list):
                print(f"[정보] TE CPO({symbol}): 빈 응답 — 다음 심볼 시도")
                continue
            df_raw = pd.DataFrame(data)
            date_col  = next((c for c in ["Date", "DateTime", "date"] if c in df_raw.columns), None)
            value_col = next((c for c in ["Close", "Last", "close", "Value"] if c in df_raw.columns), None)
            if not date_col or not value_col:
                print(f"[경고] TE CPO({symbol}): 예상 컬럼 없음 ({list(df_raw.columns)[:5]})")
                continue
            df = pd.DataFrame({
                "price_date":     _parse_te_dates(df_raw[date_col]),
                "value":          pd.to_numeric(df_raw[value_col], errors="coerce"),
                "source_name":    "TradingEconomics/BursaMalaysia",
                "indicator_code": CPO_TE_INDICATOR,
                "unit":           "MYR/MT",
                "note":           f"[TE-REST: Bursa CPO 상품 심볼 {symbol} ({start_date}~{_end}) — MYR/MT]",
                "ingested_at":    pd.Timestamp.now("UTC"),
            }).dropna(subset=["price_date", "value"])
            if df.empty:
                continue
            med = float(df["value"].median())
            if not (CPO_MYR_PLAUSIBLE[0] <= med <= CPO_MYR_PLAUSIBLE[1]):
                print(f"[경고] TE CPO({symbol}) 중앙값 {med:,.0f}이 MYR/MT 관측 범위 밖 — 폐기(단위·자산 혼입 의심)")
                continue
            print(f"[완료] TE REST CPO {len(df)}건 수집 ({symbol}, {CPO_TE_INDICATOR} MYR/MT)")
            return df.sort_values("price_date").reset_index(drop=True)
        except Exception as e:
            print(f"[경고] TE REST CPO({symbol}) 실패: {e}")
            continue
    return pd.DataFrame()


def fetch_cpo_te() -> pd.DataFrame:
    """Trading Economics CPO 현물 가격 — FRED 월별 프록시보다 갱신 빈도 높음.

    TRADING_ECONOMICS_API_KEY 등록 시 FRED 프록시 대신 사용.
    A-150: 자기발견 REST 히스토리 우선 → te_connector/SDK 추측 체인 폴백.
    """
    te_key = os.environ.get("TRADING_ECONOMICS_API_KEY", "").strip()
    if not te_key:
        return pd.DataFrame()
    # A-150: 자기발견 심볼로 REST 히스토리 우선 시도
    rest_df = _fetch_cpo_te_rest(te_key)
    if not rest_df.empty:
        return rest_df
    try:
        from src.pipeline.connectors.te_connector import fetch_cpo  # type: ignore
        return fetch_cpo()
    except ImportError:
        pass
    try:
        import tradingeconomics as te  # type: ignore
        te.login(te_key)
        for symbol in ("cpo", "palm-oil"):
            try:
                result = te.getMarketsBySymbol(symbols=symbol, output_type="df")
                if result is not None and len(result) > 0:
                    date_col  = next((c for c in ["DateTime", "Date", "date"] if c in result.columns), None)
                    value_col = next((c for c in ["Last", "Close", "Value"] if c in result.columns), None)
                    if date_col and value_col:
                        df = pd.DataFrame({
                            "price_date":     pd.to_datetime(result[date_col], errors="coerce"),
                            "value":          pd.to_numeric(result[value_col], errors="coerce"),
                            "source_name":    "TradingEconomics/BursaMalaysia",
                            "indicator_code": "CPO_USD_MT",
                            "unit":           "USD/MT",
                            "ingested_at":    pd.Timestamp.utcnow(),
                        })
                        return df.dropna(subset=["price_date", "value"])
            except Exception:
                continue
    except Exception as e:
        print(f"[경고] Trading Economics CPO 수집 실패: {e}")
    return pd.DataFrame()


def run() -> None:
    import os as _os
    _os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")

    frames = []
    # 1. CBOT 대두유 선물
    frames.append(fetch_cbot_soybean_oil(days_back=10))
    # 2. CPO — A-282: TE(MYR/MT, CPO_MYR_MT)와 FRED 달러 프록시(USD/MT, CPO_USD_MT)는 단위가 다른
    #    별개 계열이므로 **둘 다** 수집한다(구 '성공 시 FRED 건너뜀'은 같은 코드에 통화를 섞던 원인).
    cpo_te = fetch_cpo_te()
    if not cpo_te.empty:
        frames.append(cpo_te)
    frames.append(fetch_cpo_proxy_fred())
    # 2-1. 원/달러 일별(화면 원화 환산·환율 범위층)
    frames.append(fetch_krw_usd_yfinance())
    # 3. ARS/USD 공식 환율
    frames.append(fetch_ars_usd_bcra(days_back=10))
    # 4. 미국 가뭄 지수
    frames.append(fetch_us_drought_stats())

    frames = [f for f in frames if not f.empty]
    if not frames:
        print("[경고] 상품 가격 데이터: 수집된 항목 없음 — API 키 및 네트워크 확인 필요")
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = drop_future_observations(combined, "commodity_data")   # A-246
    out = f"{OUTPUT_DIR}/commodity_data_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="COMMODITY")
    combined.to_parquet(out, index=False)
    print(f"[완료] 상품 가격·가뭄 데이터 {len(combined)}건 저장 → {out}")


if __name__ == "__main__":
    run()
