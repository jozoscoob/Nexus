"""
해운 지수 커넥터 — WBS 1.1.3
수집 대상: BCAA (Baltic Chemical and Agricultural Oil Assessments) — 식물성 유지 탱커 전용
방법: Perplexity Pro 실시간 검색 (Baltic Exchange/ICE 직접 API = 유료 기업 구독)

제외 근거:
  - BDI (Baltic Dry Index): 건화물 지수 — 대두유(액체 벌크)와 무관
  - SCFI/FBX/WCI/HRCI: 컨테이너 운임 지수 — 대두유는 탱커 선박 수송
  - BCAA: 2025년 2월 Baltic Exchange 출시, 식물성 유지 탱커 전용 (CPO·SBO·팜올레인 경로 포함)
    → 직접 API: Baltic Exchange/ICE 기업 구독 필요 (MEMORY A-013)
    → 현행: Perplexity 프록시로 최신값 수집

실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions
"""

from __future__ import annotations

import os
import re
from datetime import date

import httpx
import pandas as pd
from openai import OpenAI

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof, drop_future_observations  # noqa: E402

OUTPUT_DIR = "data/raw"
PERPLEXITY_MODEL = "sonar-pro"  # MEMORY L-006/L-007: 상수 사용, 하드코딩 금지


def _perplexity_client() -> OpenAI:
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise EnvironmentError("[오류] PERPLEXITY_API_KEY 환경변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")


def fetch_bcaa() -> pd.DataFrame:
    """Perplexity 실시간 검색으로 BCAA 최신 값 수집.

    BCAA(Baltic Chemical and Agricultural Oil Assessments): 2025년 2월 출시.
    식물성 유지(대두유·팜유·팜올레인) 탱커 운임 전용 지수.
    직접 API는 Baltic Exchange/ICE 기업 구독 필요 — Perplexity 프록시로 대체.
    """
    client = _perplexity_client()
    prompt = (
        "Provide the latest BCAA (Baltic Chemical and Agricultural Oil Assessments) index value. "
        "BCAA is the Baltic Exchange's vegetable oil tanker freight assessment launched February 2025. "
        "If BCAA is unavailable, provide the latest Baltic Clean Tanker Index (BCTI) as a proxy. "
        "Format: BCAA: [value] ([date]) or BCTI: [value] ([date]). "
        "Use exact numeric values only."
    )
    r = client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    text = r.choices[0].message.content

    # A-140(c): Perplexity가 "BCAA is unavailable / not included / no quote" 류로 회신하면
    #           숫자 오추출(연도 등) 위험 — 미공표로 판정하고 우아하게 결측 처리.
    unavailable_patterns = (
        "unavailable", "not available", "not include", "no quote",
        "no publicly available", "cannot find", "could not find", "does not provide",
    )
    lowered = text.lower()
    if any(p in lowered for p in unavailable_patterns):
        print("[정보] BCAA 미공표 회신 — 결측 처리 (Perplexity가 지수 미보유 응답)")
        return pd.DataFrame()

    rows = []
    today = date.today().isoformat()

    # D-027(파생 발견): 구 코드는 price_date를 **수집일**로 고정했다. available_at 관점에서는
    # 옳지만(오늘 알게 된 것은 사실이다) event_time이 부정확해진다 — 응답이 며칠 전 평가치를
    # 담고 있어도 오늘 관측된 것처럼 기록된다. 응답에서 평가일을 찾아 event_time을 교정한다.
    # 누수 위험은 없다(available_at은 여전히 수집일 = 늦은 쪽).
    _dm = re.search(r"(20\d{2})[-/.\s]+(\d{1,2})[-/.\s]+(\d{1,2})", text)
    assessed = today
    if _dm:
        try:
            _y, _mo, _d = (int(g) for g in _dm.groups())
            _cand = date(_y, _mo, _d)
            # 미래이거나 30일 이상 과거면 오탐으로 보고 수집일 유지
            if 0 <= (date.today() - _cand).days <= 30:
                assessed = _cand.isoformat()
        except ValueError:
            pass
    if assessed != today:
        print(f"[정보] BCAA 평가일 추출: {assessed} (수집일 {today})")

    # BCAA: 다양한 응답 형식 대응 ("BCAA: 1234", "BCAA index is 1,234", "BCAA stood at 1234.5")
    bcaa_match = re.search(
        r"BCAA[^0-9\n]{0,40}?(\d[\d,\.]*)",
        text, re.IGNORECASE
    )
    if bcaa_match:
        rows.append({
            "price_date":     assessed,
            "source_name":    "Perplexity/BalticExchange",
            "indicator_code": "BCAA",
            "value":          float(bcaa_match.group(1).replace(",", "")),
            "unit":           "USD/MT",
            "note":           "[PERPLEXITY-PROXY: BCAA — 식물성유지 탱커 지수 (2025-02 출시)]",
        })

    # BCTI: 다양한 응답 형식 대응
    bcti_match = re.search(
        r"BCTI[^0-9\n]{0,40}?(\d[\d,\.]*)",
        text, re.IGNORECASE
    )
    if bcti_match:
        rows.append({
            "price_date":     today,
            "source_name":    "Perplexity/BalticExchange",
            "indicator_code": "BCTI",
            "value":          float(bcti_match.group(1).replace(",", "")),
            "unit":           "points",
            "note":           "[PERPLEXITY-PROXY: BCTI — BCAA 직접 조회 불가 시 대리 지수]",
        })

    # 마지막 폴백: "Baltic" + 숫자가 포함된 경우 BCTI 추정값으로 사용
    if not rows:
        baltic_match = re.search(
            r"(?:Baltic[^\n]{0,60}?)(\d{3,5}(?:\.\d+)?)",
            text, re.IGNORECASE
        )
        if baltic_match:
            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/BalticExchange",
                "indicator_code": "BCTI_PROXY",
                "value":          float(baltic_match.group(1).replace(",", "")),
                "unit":           "points",
                "note":           "[PERPLEXITY-PROXY: Baltic 키워드 근처 추출값 — 해석 주의]",
            })

    if not rows:
        print(f"[경고] BCAA/BCTI 파싱 실패. 원문: {text[:300]}")

    df = pd.DataFrame(rows)
    if not df.empty:
        df["price_date"]  = pd.to_datetime(df["price_date"])
        df["ingested_at"] = pd.Timestamp.utcnow()
    return df


# A-150: 재등록 키(3개월 구독)인데 BDI/BALTDRYIDX/bdi 전부 '빈 응답'(200 + 빈 배열)
#        — 하드코딩 심볼 추측이 전부 틀린 것. 검색 API로 실제 심볼을 자기발견한다.
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
    symbols.sort(key=lambda x: (0 if x.endswith(":COM") else 1 if x.endswith(":IND") else 2))  # A-159
    if symbols:
        print(f"[정보] TE 심볼 자기발견({search_term}): {symbols} (:COM/:IND 우선 — A-159)")
    else:
        print(f"[정보] TE 심볼 자기발견 실패({search_term}) — 기존 추측 체인으로 폴백")
    return symbols


def fetch_bdi_te(start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """Trading Economics REST API 직접 호출로 BDI 히스토리 수집.

    SDK의 getMarketsHistorical()은 설치된 TE 버전에서 미지원 (MEMORY A-034).
    pandas 2.0과 구형 TE SDK의 deprecate_kwarg() 호환성 오류도 동시 해소.
    REST: GET https://api.tradingeconomics.com/markets/historical/{symbol}
    파라미터: c={api_key}&d1={start}&d2={end}&f=json
    """
    te_key = os.environ.get("TRADING_ECONOMICS_API_KEY", "").strip()
    if not te_key:
        print("[정보] TRADING_ECONOMICS_API_KEY 미등록 — BDI TE REST 수집 건너뜀")
        return pd.DataFrame()

    _start = start_date or "2017-01-01"
    _end   = end_date or date.today().isoformat()

    # A-150: 검색으로 발견된 실제 심볼을 1순위로, 기존 추측(BDI/BALTDRYIDX/bdi)은 폴백 유지
    # A-282: 지수(:IND)·상품(:COM)만 허용 — 검색 결과의 해운 기업 주가가 BDI로 적재되는 경로 차단
    discovered = [s for s in _te_discover_symbols(te_key, "baltic dry", ("baltic", "dry"))
                  if s.endswith((":IND", ":COM"))]
    symbol_chain = tuple(dict.fromkeys((*discovered, "BDI", "BALTDRYIDX", "bdi")))

    for symbol in symbol_chain:
        try:
            url = f"https://api.tradingeconomics.com/markets/historical/{symbol}"
            params = {"c": te_key, "d1": _start, "d2": _end, "f": "json"}
            r = httpx.get(url, params=params, timeout=30)
            if r.status_code == 401:
                print("[경고] TE API 401 인증 실패 — TRADING_ECONOMICS_API_KEY 값 확인 필요")
                return pd.DataFrame()
            if r.status_code == 403:
                print("[경고] TE API 403 권한 없음 — TE 구독 플랜에서 Markets Historical 포함 확인")
                return pd.DataFrame()
            # A-140(a): 409 = 구독 플랜이 markets/historical 미포함 추정(키는 유효).
            #           실측: /markets/historical 호출 시 409 반환 — 코드 문제 아님.
            if r.status_code == 409:
                print("[정보] TE API 409 — 구독 플랜이 markets/historical 미포함 추정. "
                      "BDI 히스토리는 수동 xlsx(te_commodities, 2010~2026-07 보유)로 커버됨(A-061)")
                return pd.DataFrame()
            r.raise_for_status()
            data = r.json()
            if not data or not isinstance(data, list):
                print(f"[경고] TE REST BDI({symbol}): 빈 응답 — 다음 심볼 시도")
                continue
            df_raw = pd.DataFrame(data)
            date_col  = next((c for c in ["Date", "DateTime", "date"] if c in df_raw.columns), None)
            value_col = next((c for c in ["Close", "Last", "close", "Value"] if c in df_raw.columns), None)
            if not date_col or not value_col:
                print(f"[경고] TE REST BDI({symbol}): 예상 컬럼 없음 ({list(df_raw.columns)[:5]})")
                continue
            # A-282: TE REST 날짜는 dd/mm/yyyy — 추론(dayfirst=False 경고)에 맡기지 않고 형식 고정
            _dates = pd.to_datetime(df_raw[date_col], format="%d/%m/%Y", errors="coerce")
            if _dates.isna().any():
                _dates = _dates.where(_dates.notna(),
                                      pd.to_datetime(df_raw[date_col], errors="coerce", format="ISO8601"))
            df = pd.DataFrame({
                "price_date":     _dates,
                "value":          pd.to_numeric(df_raw[value_col], errors="coerce"),
                "source_name":    "TradingEconomics/BalticExchange",
                "indicator_code": "BDI",
                "unit":           "points",
                "note":           f"[TE-REST: BDI 히스토리 ({_start}~{_end}) — SDK 미사용 직접 호출]",
                "ingested_at":    pd.Timestamp.utcnow(),
            }).dropna(subset=["price_date", "value"])
            if not df.empty:
                print(f"[완료] TE REST BDI {len(df)}건 수집 ({symbol}, {_start}~{_end})")
                return df.sort_values("price_date").reset_index(drop=True)
        except httpx.HTTPStatusError as e:
            print(f"[경고] TE REST BDI({symbol}) HTTP {e.response.status_code}: {e}")
            continue
        except Exception as e:
            print(f"[경고] TE REST BDI({symbol}) 실패: {e}")
            continue

    print("[경고] TE REST BDI 전체 심볼 실패 — stooq 폴백으로 전환")
    return pd.DataFrame()


def fetch_bdi_stooq(start_date: str = "2017-01-01") -> pd.DataFrame:
    """stooq.com CSV 직접 다운로드로 BDI 히스토리 수집 (TE 키 미등록/실패 시 폴백).

    A-053: 기존 pandas-datareader는 pandas 2.x/3.x와 호환 불가
    (`deprecate_kwarg() missing 1 required positional argument`). httpx로 stooq CSV
    엔드포인트를 직접 호출해 의존성 제거.

    stooq CSV: https://stooq.com/q/d/l/?s=<symbol>&d1=YYYYMMDD&d2=YYYYMMDD&i=d
    응답 형식: Date,Open,High,Low,Close,Volume — API 키 불필요.
    """
    import io

    end = date.today()
    d1 = start_date.replace("-", "")
    d2 = end.strftime("%Y%m%d")
    # stooq Baltic Dry 심볼: ^bdi (인덱스). 폴백 심볼 순차 시도.
    for symbol in ("^bdi", "bdi"):
        url = f"https://stooq.com/q/d/l/?s={symbol}&d1={d1}&d2={d2}&i=d"
        try:
            resp = httpx.get(url, timeout=30)
            # A-140(b): stooq ^bdi 404 = 심볼 소멸(서비스 정상) — 치명 오류가 아니라 [정보] 강등.
            #           심볼 체인은 유지(재상장 가능성 대비).
            if resp.status_code == 404:
                print(f"[정보] stooq {symbol}: 404 — 심볼 소멸 추정(다음 심볼 시도)")
                continue
            resp.raise_for_status()
            text = resp.text.strip()
            # stooq는 데이터 없을 때 'No data' 또는 HTML 반환
            if not text or "No data" in text or text.lower().startswith("<"):
                print(f"[정보] stooq {symbol}: 데이터 없음")
                continue
            raw = pd.read_csv(io.StringIO(text))
            if "Date" not in raw.columns or "Close" not in raw.columns:
                print(f"[경고] stooq {symbol}: 예상 컬럼 없음 ({list(raw.columns)})")
                continue
            df = pd.DataFrame({
                "price_date":     pd.to_datetime(raw["Date"], errors="coerce"),
                "value":          pd.to_numeric(raw["Close"], errors="coerce"),
                "source_name":    "stooq/BalticExchange",
                "indicator_code": "BDI",
                "unit":           "points",
                "note":           f"[STOOQ-FREE: BDI 히스토리 ({start_date}~{end.isoformat()})]",
                "ingested_at":    pd.Timestamp.utcnow(),
            }).dropna(subset=["price_date", "value"])
            if not df.empty:
                print(f"[완료] BDI stooq 히스토리 {len(df)}건 ({symbol})")
                return df.sort_values("price_date").reset_index(drop=True)
        except Exception as e:
            print(f"[경고] stooq {symbol} 실패: {e}")
            continue
    return pd.DataFrame()


TE_XLSX_BDI_GLOB = "data/raw/Trading Economics/Markets/Commodities/Shipping Indices/*BDI*.xlsx"
TE_XLSX_RECENT_DAYS = 120


def fetch_bdi_te_xlsx(recent_days: int = TE_XLSX_RECENT_DAYS) -> pd.DataFrame:
    """3순위 폴백(A-263) — 저장소 커밋 TE xlsx(BDI 시트)에서 최근 N일을 재구성한다.

    왜 필요한가: TE historical 409(플랜 미포함, A-140)·stooq 404(심볼 소멸)가 겹치는 날은
    파케이에 Perplexity BCAA 1행만 남아 품질 게이트 `MIN_ROWS`에 걸렸다(런 #97). BDI 일별
    계열은 `te_xlsx_update.yml` 스냅샷이 평일마다 xlsx에 append하므로(DQ-21 확정 경로) 저장소
    사본이 곧 최신 정본이다 — 이 사본을 읽으면 BDI 일별 계열이 비는 날이 없다.
    파서는 scripts/ingest_te_xlsx.parse_te_file 재사용(연도 시트·정렬 교정 포함).
    source_name을 구분해 API 수집분과 섞이지 않게 한다.
    """
    import glob as _glob

    files = sorted(_glob.glob(TE_XLSX_BDI_GLOB))
    if not files:
        print("[정보] TE xlsx BDI 사본 없음(sparse checkout 범위 밖?) — 3순위 폴백 건너뜀")
        return pd.DataFrame()
    try:
        from scripts.ingest_te_xlsx import parse_te_file
        raw = parse_te_file(_Path(files[-1]))
    except Exception as e:
        print(f"[경고] TE xlsx BDI 파싱 실패: {type(e).__name__}: {str(e)[:80]}")
        return pd.DataFrame()
    if raw.empty:
        return pd.DataFrame()
    cutoff = pd.Timestamp(date.today() - __import__("datetime").timedelta(days=recent_days))
    sub = raw[raw["price_date"] >= cutoff]
    if sub.empty:
        print("[경고] TE xlsx BDI: 최근 구간 행 없음")
        return pd.DataFrame()
    df = pd.DataFrame({
        "price_date":     pd.to_datetime(sub["price_date"]),
        "value":          pd.to_numeric(sub["value"], errors="coerce"),
        "source_name":    "TradingEconomics_xlsx_snapshot",
        "indicator_code": "BDI",
        "unit":           "points",
        "note":           f"[TE-XLSX: 저장소 스냅샷 사본 최근 {recent_days}일 — API 미수신 폴백]",
        "ingested_at":    pd.Timestamp.utcnow(),
    }).dropna(subset=["price_date", "value"])
    print(f"[완료] BDI TE xlsx 사본 {len(df)}건 (최근 {recent_days}일, 마지막 "
          f"{df['price_date'].max().date()})")
    return df.sort_values("price_date").reset_index(drop=True)


def run() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")
    frames = []

    # BACKFILL_MODE=true: Perplexity BCAA(오늘만 반환) 건너뜀 — 역사 데이터는 TE/stooq BDI만 사용
    backfill_mode = os.environ.get("BACKFILL_MODE", "").lower() == "true"

    if backfill_mode:
        print("[정보] BACKFILL_MODE 활성화 — Perplexity BCAA 수집 건너뜀 (BDI 역사 데이터만 수집)")
    else:
        # BCAA: 식물성유지 탱커 운임 (Perplexity 프록시 — TE 미제공)
        try:
            bcaa = fetch_bcaa()
            if not bcaa.empty:
                frames.append(bcaa)
        except EnvironmentError:
            print("[경고] PERPLEXITY_API_KEY 미등록 — BCAA 수집 건너뜀")

    # BDI: 구조적 단절 모니터링 (Trading Economics REST API → stooq → TE xlsx 사본 3단 폴백, A-263)
    hist_start = f"{os.environ.get('HISTORICAL_START_YEAR', '2017')}-01-01"
    bdi = fetch_bdi_te(start_date=hist_start)
    if not bdi.empty:
        frames.append(bdi)
    else:
        print(f"[정보] TE BDI 미수집 — stooq 폴백 시도 ({hist_start}~)")
        bdi_stooq = fetch_bdi_stooq(start_date=hist_start)
        if not bdi_stooq.empty:
            frames.append(bdi_stooq)
        else:
            # A-263: 3순위 — 저장소 TE xlsx 스냅샷 사본(최근 120일). BDI 일별 계열 무결성 보장.
            print("[정보] stooq BDI 미수집 — TE xlsx 스냅샷 사본 폴백 시도")
            bdi_xlsx = fetch_bdi_te_xlsx()
            if not bdi_xlsx.empty:
                frames.append(bdi_xlsx)

    if not frames:
        # A-140(d): 전 소스 실패여도 exit 0 — BDI 히스토리는 수동 TE xlsx로 이미 확보(A-061).
        #           빈 parquet은 쓰지 않음(기존 동작 유지). 잡 실패로 파이프라인 차단 금지.
        print("[경고] 해운 실시간 수집 전 소스 실패 (TE 409/stooq 404/BCAA 미공표). "
              "BDI 히스토리는 수동 TE xlsx로 확보 상태(A-061) — 이번 실패는 실시간 갱신분만 영향.")
        return

    df = pd.concat(frames, ignore_index=True)
    df = drop_future_observations(df, "shipping_indices")   # A-246: 관측 계열 미래 행 차단
    out = f"{OUTPUT_DIR}/shipping_indices_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    df = attach_asof(df, source="SHIPPING")
    df.to_parquet(out, index=False)
    print(f"[완료] 해운 지수 {len(df)}건 저장 → {out}")


if __name__ == "__main__":
    run()
