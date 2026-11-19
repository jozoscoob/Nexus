"""
경제 지표 커넥터 — WBS 1.1.2
수집 대상: Fed 기준금리 (FRED) · 글로벌 CPI (FRED) · KRW/USD 환율 (BOK ECOS) · WTI/Brent 유가 (EIA)
실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions
"""

from __future__ import annotations

import os
import time
from datetime import date
from typing import Any, Callable

import httpx

# A-085: 한국 공공기관 호스트에서 러너 IPv6 경로 블랙홀 → IPv4 강제 트랜스포트
_KR_TRANSPORT = httpx.HTTPTransport(local_address="0.0.0.0", retries=2)
import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

# ── 상수 ──────────────────────────────────────────────────────────────────────
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
EIA_BASE  = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
BOK_BASE  = "https://ecos.bok.or.kr/api/StatisticSearch"
OUTPUT_DIR = "data/raw"


def _fetch(url: str, params: dict[str, Any], max_retries: int = 4) -> dict:
    """외부 API 호출 — 지수 백오프 재시도 (MEMORY A-003).
    400: 시리즈 미존재 또는 파라미터 오류 → 재시도 없이 빈 dict 반환.
    """
    delay = 2
    for attempt in range(max_retries):
        try:
            r = httpx.Client(transport=_KR_TRANSPORT, timeout=60).get(url, params=params)
            if r.status_code == 400:
                base = url.split("?")[0]
                print(f"[경고] API 400 응답 ({base}): 시리즈 미존재 또는 파라미터 오류. 건너뜀.")
                return {}
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"[오류] API 호출 실패 ({url}): {e}") from e
            time.sleep(delay)
            delay *= 2
    return {}


def fetch_fred_series(series_id: str, start: str, end: str) -> pd.DataFrame:
    """FRED 시계열 데이터 수집."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise EnvironmentError("[오류] FRED_API_KEY 환경변수가 설정되지 않았습니다.")
    # D-027: FRED(ALFRED)는 관측치마다 **최초 게시일(realtime_start)** 을 제공한다.
    #   이것이 available_at의 직접 근거이자 vintage 식별자다 — 발표일을 추정할 필요가 없다.
    #   `output_type=4`(최초 발표본만)로 요청하면 개정 전 원본 vintage를 얻는다.
    #   개정이 잦은 월간 지표(CPI·FEDFUNDS)는 이 값이 특히 중요하다
    #   (美 CPI는 매년 2월 계절조정 재산정으로 최근 5년이 소급 개정된다).
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
        "realtime_start": "1776-07-04",   # ALFRED 전 구간 — 최초 게시일 확보
        "realtime_end": "9999-12-31",
        "output_type": "4",               # 4 = initial release only
    }
    data = _fetch(FRED_BASE, params)
    obs = data.get("observations", [])
    if not obs:
        # ALFRED 파라미터를 지원하지 않는 응답이면 표준 요청으로 폴백
        print(f"[정보] FRED {series_id}: ALFRED 응답 없음 — 표준 요청으로 재시도")
        data = _fetch(FRED_BASE, {k: v for k, v in params.items()
                                  if k not in ("realtime_start", "realtime_end", "output_type")})
        obs = data.get("observations", [])
    if not obs:
        print(f"[경고] FRED {series_id}: 기간 {start}~{end} 데이터 없음")
        return pd.DataFrame()
    df = pd.DataFrame(obs)
    missing = [c for c in ["date", "value"] if c not in df.columns]
    if missing:
        print(f"[경고] FRED {series_id} 컬럼 누락: {missing}")
        return pd.DataFrame()

    keep = ["date", "value"] + [c for c in ("realtime_start",) if c in df.columns]
    df = df[keep].copy()
    df = df.rename(columns={"date": "price_date"})
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["source_name"] = "FRED"
    df["indicator_code"] = series_id
    if "realtime_start" in df.columns:
        # 실측 게시일 → release_time. as-of 부여 시 추정 규칙보다 우선한다.
        df["release_time"] = pd.to_datetime(df["realtime_start"], errors="coerce")
        df["source_vintage"] = df["realtime_start"]
        df = df.drop(columns=["realtime_start"])
        n = int(df["release_time"].notna().sum())
        print(f"[정보] FRED {series_id}: 실측 게시일 {n:,}/{len(df):,}건 확보(추정 불요)")
    df = df.dropna(subset=["value"])

    # A-170 (D-029 보완): output_type=4는 ALFRED 아카이브 **첫 vintage 이전** 관측치를
    # 아예 반환하지 않는다 → 시계열 앞구간 결손(FX BRL/USD 커버리지 74%의 원인 —
    # Model Readiness 게이트 85% 미달로 G1 차단). 결손 앞구간은 표준 요청으로 보충한다.
    # 보충분은 실측 게시일이 없으므로 release_time을 비워 두고 asof.py 규칙 추정에 맡긴다
    # (일간 FX는 개정이 사실상 없어 최신값=최초값으로 보아도 무방).
    if not df.empty:
        earliest = df["price_date"].min()
        want_start = pd.to_datetime(start)
        if (earliest - want_start).days > 45:
            gap_end = (earliest - pd.Timedelta(days=1)).date().isoformat()
            print(f"[정보] FRED {series_id}: ALFRED 초기 구간 결손 {start}~{gap_end} — 표준 요청 보충")
            std_params = {k: v for k, v in params.items()
                          if k not in ("realtime_start", "realtime_end", "output_type")}
            std_params["observation_end"] = gap_end
            obs2 = _fetch(FRED_BASE, std_params).get("observations", [])
            if obs2:
                df2 = pd.DataFrame(obs2)
                if {"date", "value"}.issubset(df2.columns):
                    df2 = df2[["date", "value"]].rename(columns={"date": "price_date"})
                    df2["price_date"] = pd.to_datetime(df2["price_date"])
                    df2["value"] = pd.to_numeric(df2["value"], errors="coerce")
                    df2["source_name"] = "FRED"
                    df2["indicator_code"] = series_id
                    df2 = df2.dropna(subset=["value"])
                    df = pd.concat([df2, df], ignore_index=True)
                    print(f"[정보] FRED {series_id}: 앞구간 {len(df2):,}건 병합 "
                          f"(총 {len(df):,}건)")
    return df


def fetch_eia_brent(start: str, end: str) -> pd.DataFrame:
    """EIA Brent Crude 일간 시계열 수집."""
    api_key = os.environ.get("EIA_API_KEY")
    if not api_key:
        raise EnvironmentError("[오류] EIA_API_KEY 환경변수가 설정되지 않았습니다.")
    data = _fetch(EIA_BASE, {
        "api_key": api_key,
        "frequency": "daily",
        "data[0]": "value",
        "facets[product][]": "EPCBRENT",
        "start": start,
        "end": end,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    })
    rows = data.get("response", {}).get("data", [])
    if not rows:
        print(f"[경고] EIA Brent: 기간 {start}~{end} 데이터 없음")
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    missing = [c for c in ["period", "value"] if c not in df.columns]
    if missing:
        print(f"[경고] EIA Brent 컬럼 누락: {missing}. 실제 컬럼: {list(df.columns)}")
        return pd.DataFrame()
    df = df[["period", "value"]].copy()
    df.columns = ["price_date", "value"]
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["source_name"] = "EIA"
    df["indicator_code"] = "BRENT_USD_BBL"
    return df.dropna(subset=["value"])


def fetch_bok_krw_usd(start: str, end: str) -> pd.DataFrame:
    """BOK ECOS KRW/USD 환율 수집. T+2 결제일 오프셋은 소비 측에서 적용 (MEMORY M-002)."""
    # A-078: ERROR-100(필수값 누락)의 흔한 원인 = 키 끝 공백/개행 → URL 경로 세그먼트 오염.
    #        반드시 strip. 또한 2010~2026 일별은 ~6,000행 → 요청건수 5000 초과분 잘림 → 100000.
    api_key = os.environ.get("BOK_ECOS_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError("[오류] BOK_ECOS_API_KEY 환경변수가 설정되지 않았습니다.")
    start_fmt = start.replace("-", "")
    end_fmt   = end.replace("-", "")
    # A-220: ERROR-100(필수값 누락) 재발의 유력 원인 — 주기 코드. ECOS 공식 주기는
    # A/S/Q/M/SM/'D'(일별)인데 구 코드가 'DD'를 사용 → 주기 후보를 순회해 실측 확정.
    data = None
    for cycle in ("D", "DD"):
        url = f"{BOK_BASE}/{api_key}/json/kr/1/100000/731Y001/{cycle}/{start_fmt}/{end_fmt}/0000001"
        data = _fetch(url, {})
        if data and "StatisticSearch" in data:
            print(f"[정보] BOK ECOS 주기 코드 '{cycle}' 성공")
            break
        rc = (data or {}).get("RESULT", {}).get("CODE", "EMPTY")
        print(f"[정보] BOK ECOS 주기 '{cycle}' 실패({rc}) — 다음 후보 시도")

    # BOK ECOS 오류 응답: 정상이면 "StatisticSearch" 키, 오류이면 "RESULT" 키
    if not data or "RESULT" in data:
        result_info = data.get("RESULT", {}) if data else {}
        code = result_info.get("CODE", "EMPTY")
        msg  = result_info.get("MESSAGE", "응답 없음")
        print(
            f"[경고] BOK ECOS API 오류 — 코드: {code}, 메시지: {msg}. "
            f"주기 D/DD 모두 실패 — 원/달러는 FRED DEXKOUS로 이중화돼 있어 비치명(A-129). "
            f"잔여 확인: ecos.bok.or.kr 키 상태·731Y001 통계표 개편 여부."
        )
        return pd.DataFrame()

    rows = data.get("StatisticSearch", {}).get("row", [])
    if not rows:
        print(f"[경고] BOK ECOS: 기간 {start}~{end} 데이터 없음. API 키 또는 날짜 범위 확인.")
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    missing = [c for c in ["TIME", "DATA_VALUE"] if c not in df.columns]
    if missing:
        print(f"[경고] BOK ECOS 컬럼 누락: {missing}. 실제 컬럼: {list(df.columns)}")
        return pd.DataFrame()
    df = df[["TIME", "DATA_VALUE"]].copy()
    df.columns = ["price_date", "value"]
    df["price_date"] = pd.to_datetime(df["price_date"], format="%Y%m%d")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["source_name"] = "BOK_ECOS"
    df["indicator_code"] = "KRW_USD"
    return df.dropna(subset=["value"])


def _kosis_b64_key(raw_key: str) -> str:
    """KOSIS API는 Base64 인코딩 키 사용. 미인코딩 키 자동 변환.
    포털에서 발급된 키가 hex(평문) 또는 Base64 중 어느 형식이든 대응.
    """
    import base64 as _b64
    stripped = raw_key.strip()
    try:
        decoded = _b64.b64decode(stripped, validate=True)
        if decoded:
            return stripped  # 이미 유효한 Base64
    except Exception:
        pass
    return _b64.b64encode(stripped.encode()).decode()


def fetch_kosis_cpi_korea(start_yyyymm: str = "201001") -> pd.DataFrame:
    """KOSIS API — 한국 소비자물가지수(CPI_KOREA) 수집 (신규 URL 방식, A-070).

    구 statisticsData.do 서비스 중단 → **statisticsParameterData.do** URL 생성 방식으로 전환
    (조정자 제공 신규 키·URL). 작성기관: 국가데이터처(orgId=101).
    참조 테이블 2종:
      - DT_1J22003: 소비자물가지수(2020=100) 전국 총지수 → CPI_KOREA_TOTAL
      - DT_1J22002: 품목성질별 소비자물가지수(2020=100) → CPI_KOREA_ITEM_CLASS
    파라미터(조정자 URL): itmId=T+ · objL1(테이블별) · format=json · jsonVD=Y · prdSe=M ·
      startPrdDe=201001 · outputFields · smblChk=N · orgId=101 · tblId
    ⚠️ 키는 env KOSIS_API_KEY (Base64) — 하드코딩 금지, 노출 시 로테이션.
    """
    api_key = os.environ.get("KOSIS_API_KEY", "").strip()
    if not api_key:
        print("[경고] KOSIS_API_KEY 미등록 — CPI_KOREA 수집 건너뜀")
        return pd.DataFrame()

    b64_key = _kosis_b64_key(api_key)
    end_yyyymm = date.today().strftime("%Y%m")
    # A-078: DT(관측값)가 outputFields에 없으면 레코드는 오지만 값 파싱이 전부 None → 0건 저장.
    OUTPUT_FIELDS = "ORG_ID+TBL_ID+OBJ_ID+ITM_ID+OBJ_NM_ENG+NM_ENG+ITM_NM_ENG+UNIT_NM_ENG+PRD_SE+PRD_DE+DT+"

    # 수집 대상 테이블 (CPI 총지수 + 품목성질별). objL1은 테이블별 분류값.
    KOSIS_TABLES = [
        {"tblId": "DT_1J22003", "objL1": "T10", "label": "CPI_KOREA_TOTAL"},
        {"tblId": "DT_1J22002", "objL1": "ALL", "label": "CPI_KOREA_ITEM_CLASS"},
    ]

    all_rows: list[dict] = []
    for tbl in KOSIS_TABLES:
        try:
            raw = _fetch("https://kosis.kr/openapi/Param/statisticsParameterData.do", {
                "method":       "getList",
                "apiKey":       b64_key,
                "itmId":        "T+",
                "objL1":        tbl["objL1"],
                "objL2":        "", "objL3": "", "objL4": "",
                "objL5":        "", "objL6": "", "objL7": "", "objL8": "",
                "format":       "json",
                "jsonVD":       "Y",
                "prdSe":        "M",
                "startPrdDe":   start_yyyymm,
                "endPrdDe":     end_yyyymm,
                "outputFields": OUTPUT_FIELDS,
                "smblChk":      "N",
                "orgId":        "101",
                "tblId":        tbl["tblId"],
            })
            if not raw:
                print(f"[경고] KOSIS {tbl['tblId']}: 응답 없음")
                continue
            records = raw if isinstance(raw, list) else raw.get("data", raw.get("row", []))
            if not records:
                # A-282: DT_1J22002가 매 런 0건 — 오류 본문을 숨기지 않고 노출(자기발견, A-106 패턴)
                print(f"[경고] KOSIS {tbl['tblId']}: 레코드 0건 — 응답 본문: {str(raw)[:300]}")
                continue
            n_before = len(all_rows)
            for rec in records:
                period = rec.get("PRD_DE", rec.get("prd_de", ""))
                value  = rec.get("DT", rec.get("dt", None))
                if not (period and value is not None):
                    continue
                # D-027: objL1="ALL"은 품목성질별 **여러 분류**를 반환하는데 구 코드는
                #   indicator_code에 테이블 라벨 하나만 넣었다 → 동일 (price_date,
                #   indicator_code)에 수십 행이 중복되어 **as-of join이 임의 행을 선택**한다.
                #   분류 코드를 접미해 키를 유일화한다(OUTPUT_FIELDS로 이미 요청 중이나 미사용).
                cls = next((str(rec[k]).strip() for k in
                            ("C1", "ITM_ID", "itm_id", "OBJ_ID", "obj_id")
                            if rec.get(k)), "")
                code = f"{tbl['label']}_{cls}" if (cls and tbl["objL1"] == "ALL") else tbl["label"]
                cls_name = next((str(rec[k]).strip() for k in
                                 ("C1_NM", "OBJ_NM_ENG", "ITM_NM_ENG") if rec.get(k)), "")
                all_rows.append({
                    "price_date":     pd.to_datetime(period, format="%Y%m", errors="coerce"),
                    "indicator_code": code,
                    "value":          pd.to_numeric(str(value).replace(",", ""), errors="coerce"),
                    "source_name":    "KOSIS/국가데이터처",
                    "tbl_id":         tbl["tblId"],
                    "class_name":     cls_name,
                })
            n_parsed = len(all_rows) - n_before
            print(f"[정보] KOSIS {tbl['tblId']} ({tbl['label']}): 수신 {len(records)}건 → 적재 {n_parsed}건")
            if n_parsed == 0:
                # A-282: 런 #113 실측 — 22003은 200건 수신인데 적재 0건('전체 수집 실패'로 오표기).
                #        PRD_DE·DT 키 부재가 원인이면 첫 레코드 키를 보여야 다음 런에서 교정 가능.
                first = records[0] if isinstance(records[0], dict) else {}
                print(f"[경고] KOSIS {tbl['tblId']}: 수신분 전량 미적재 — 첫 레코드 키: {sorted(first.keys())[:20]}")
        except Exception as e:
            print(f"[경고] KOSIS {tbl['tblId']} 수집 실패: {e}")

    if not all_rows:
        print("[경고] KOSIS CPI 적재 0건 — 위 테이블별 진단(응답 본문·레코드 키) 확인")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["ingested_at"] = pd.Timestamp.utcnow()
    print(f"[완료] KOSIS CPI 총 {len(df)}건 ({start_yyyymm}~{end_yyyymm})")
    return df


def run(start_date: str | None = None, end_date: str | None = None) -> None:
    # 2010.01 기준선(조정자): HISTORICAL_START_YEAR 환경변수 우선, 기본 2010
    if start_date is None:
        start_date = f"{os.environ.get('HISTORICAL_START_YEAR', '2010')}-01-01"
    end   = end_date or date.today().isoformat()
    start = start_date
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")

    def _safe(fn: Callable, *args: Any, label: str = "", **kwargs: Any) -> pd.DataFrame:
        """개별 커넥터 실패를 격리 — 단일 실패가 전체 파이프라인을 중단시키지 않음."""
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[경고] {label or fn.__name__} 수집 실패: {e}")
            return pd.DataFrame()

    frames = [
        # ── 금리·물가 ──────────────────────────────────────────────────────────
        _safe(fetch_fred_series, "FEDFUNDS", start, end, label="FRED FEDFUNDS"),
        _safe(fetch_fred_series, "CPIAUCSL", start, end, label="FRED CPIAUCSL"),
        # ── 유가 ───────────────────────────────────────────────────────────────
        _safe(fetch_eia_brent,   start, end, label="EIA Brent"),
        # ── 환율 (원산지·결제통화) ─────────────────────────────────────────────
        _safe(fetch_bok_krw_usd, start, end, label="BOK ECOS KRW/USD"),
        # A-129: BOK ECOS ERROR-100이 반복되는 동안 KRW/USD가 통째로 비는 것을 막는다.
        #   FRED DEXKOUS(원/달러, 뉴욕 정오 매입환율)는 같은 방향·일별 계열로 ALFRED
        #   실측 게시일까지 제공한다. BOK가 정상화돼도 교차검증 지표로 계속 수집한다.
        _safe(fetch_fred_series, "DEXKOUS", start, end, label="FRED DEXKOUS (KRW/USD 폴백)"),
        _safe(fetch_fred_series, "DEXBZUS", start, end, label="FRED DEXBZUS (BRL/USD)"),
        # DEXARUE(아르헨티나 페소): FRED 미제공 — 다중 환율제도로 공식 시리즈 없음
        # 추후 BCRA(아르헨티나 중앙은행) API 또는 IMF IFS API로 대체 예정 (MEMORY D-002)
        _safe(fetch_fred_series, "DEXCHUS", start, end, label="FRED DEXCHUS (CNY/USD)"),
        _safe(fetch_fred_series, "DEXMAUS", start, end, label="FRED DEXMAUS (MYR/USD)"),
        # ── 시장 리스크 ────────────────────────────────────────────────────────
        _safe(fetch_fred_series, "VIXCLS",  start, end, label="FRED VIXCLS"),
        # ── 한국 수입 통계 (KOSIS — 연결 확인만; 실 데이터는 data.go.kr 전환 예정) ──
        _safe(fetch_kosis_cpi_korea, label="KOSIS CPI_KOREA (DT_1J22003)"),
    ]

    frames = [f for f in frames if not f.empty]
    if not frames:
        print("[경고] 경제 지표: 모든 소스 응답 없음 — API 키 및 네트워크 확인 필요")
        return

    combined = pd.concat(frames, ignore_index=True)
    combined["ingested_at"] = pd.Timestamp.utcnow()
    combined["unit"] = ""

    out = f"{OUTPUT_DIR}/economic_indicators_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="ECONOMIC")
    combined.to_parquet(out, index=False)
    print(f"[완료] 경제 지표 {len(combined)}건 저장 → {out}")


if __name__ == "__main__":
    run()
