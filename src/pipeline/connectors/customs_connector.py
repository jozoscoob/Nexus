"""
한국 세관 수출입 통계 커넥터 — WBS 1.1.2 보완
수집 대상: HS 1507 (대두유) 품목별·국가별 수입량·CIF 금액 (관세청 API)

==================================================================
API 1 — 관세청_품목별 수출입실적(GW)
  엔드포인트: https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList
  용도: 국가 구분 없이 HS코드 기준 전체 수출입 실적
  파라미터:
    - serviceKey: DATA_GO_KR_SERVICE_KEY (GitHub Secrets)
    - strtYymm:   YYYYMM (예: 201701)
    - endYymm:    YYYYMM (예: 201712)
    - hsSgn:      6단위 HS코드 (150710, 150790)

API 2 — 관세청_품목별 국가별 수출입실적(GW)
  엔드포인트: https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList
  용도: HS코드 × 국가별 상세 수출입 실적
  파라미터:
    - serviceKey, strtYymm, endYymm, hsSgn (위와 동일)
    - cntyCd: ISO 2자리 국가코드 (US, AR, BR, CN, ID)
==================================================================

HS 코드 — 2026-06-18 사용자 확인 (6단위 사용):
  150710: 대두유 조유 (Crude soybean oil, 식품용 포함)
  150790: 정제 대두유 및 기타 (Refined/other soybean oil)

  ※ 이전 10단위(1507101000/1507901010/1507901020) → 2026-06-18 6단위로 변경
     6단위 사용 시 해당 품목 전체를 포괄하여 누락 방지

키 형식: 평문 hex 키 (URL-인코딩 불필요)
        3단계 폴백: unquote → 원본 → URL 직삽

UN Comtrade Plus 대안:
  - 환경변수: UN_COMTRADE_API_KEY
  - 패키지: comtradeapicall (pip install comtradeapicall)
  - 무료 500건/일, 유료 10,000건/일

실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions
"""

from __future__ import annotations

import os
import time
from datetime import date, timedelta
from typing import Any
from urllib.parse import unquote

import json as _json

import httpx
import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

OUTPUT_DIR = "data/raw"

# API 1: 품목별 수출입실적 (국가 구분 없음)
ITEMTRADE_BASE   = "https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList"
# API 2: 품목별 국가별 수출입실적
NITEMTRADE_BASE  = "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"

# HS 코드 — 6단위 (2026-06-18 사용자 확인)
# 150710: 대두유 조유 / 150790: 정제 및 기타 대두유
# ── 수집 대상 HS 코드 (A-120 · C-01×C-03×P1-01~04 협의 확정) ────────────────
# 관세청 hsSgn은 **6자리**를 요구한다(A-043). 4자리를 넣으면 조회가 실패하거나
# 다른 결과가 나오므로 전 항목을 6자리로 통일한다.
#
# 대두유 본체 — 예측 대상
HS_CODES_SOYBEAN_OIL: list[str] = [
    "150710",   # 대두유 조유 (Crude soybean oil)
    "150790",   # 정제 대두유 및 기타 (Refined and other soybean oil)
]

# 대체재(Substitutes) — 한국 식용유 시장에서 대두유와 수요를 다투는 유지류.
#   선정 기준: ①한국 수입 실적이 유의미할 것 ②용도가 겹칠 것(식용·가공·바이오연료)
#   ③가격 전이 경로가 문헌·사전(entities.yaml)에 등재돼 있을 것
HS_CODES_SUBSTITUTES: dict[str, str] = {
    "151110": "팜유 조유 — 세계 최대 유지, CPO–SBO 스프레드는 G1 핵심변수(TERM-055)",
    "151190": "팜유 정제·기타 — 한국 가공식품 주력 대체재",
    "151211": "해바라기유 조유 — 흑해 지정학 충격의 대체 경로(TERM-057, P1-02)",
    "151219": "해바라기유 정제·기타",
    "151411": "유채(카놀라)유 조유 — 저에루스산, EU 바이오디젤 수요 연동(TERM-056)",
    "151419": "유채(카놀라)유 정제·기타 — 한국 가정용 식용유 주요 대체",
    "151321": "팜핵유 조유 — 라우르산 계열, 제과·유지가공 대체",
    "151329": "팜핵유 정제·기타",
    "151521": "옥수수유 조유 — 미국 에탄올 부산물, 튀김유 대체",
    "151529": "옥수수유 정제·기타",
    "151590": "기타 고정식물성 유지 — **포도씨유 포함**(바스켓 코드, 해석 주의)",
}

# 보완재(Complements) — 대두유 자체는 아니나 **공급·수요를 통해 가격을 움직이는** 품목
HS_CODES_COMPLEMENTS: dict[str, str] = {
    "120190": "대두(종자용 제외) — 압착 원료. 대두 가격이 SBO 원가를 직접 규정",
    "230400": "대두박 — **연산품(joint product)**. 대두박 수요가 압착량을 정하고 "
              "압착량이 SBO 공급을 정한다(P1-01 압착 마진 경로)",
    "382600": "바이오디젤 — SBO 수요 축. 의무혼합·45Z 세액공제가 식용 수요와 경합",
}

# 전체 수집 대상 (대두유 + 대체재 + 보완재)
HS_CODES_ALL: list[str] = (
    HS_CODES_SOYBEAN_OIL
    + list(HS_CODES_SUBSTITUTES)
    + list(HS_CODES_COMPLEMENTS)
)
HS_NOTES: dict[str, str] = {**HS_CODES_SUBSTITUTES, **HS_CODES_COMPLEMENTS}

# 한국 대두유 주요 수입 국가 (2026-06-18 사용자 확인)
COUNTRY_CODES: list[str] = ["US", "AR", "BR", "CN", "ID"]

# 시간 예산 — 잡 timeout-minutes 강제종료(수집분 전량 유실) 이전에 스스로 중단·저장한다.
# 0 또는 미설정이면 무제한 (A-167: 런 31812867920에서 90분 kill로 HS1507 유실된 사후 조치)
_BUDGET_S = float(os.environ.get("CUSTOMS_TIME_BUDGET_S", "0") or 0)
_START_MONO = time.monotonic()


def _budget_exceeded() -> bool:
    return _BUDGET_S > 0 and (time.monotonic() - _START_MONO) > _BUDGET_S


# ── 월 단위 증분 (A-253 — 승인자 지시 9/9): 업로드본이 덮는 월은 조회하지 않는다 ──
GW_UPLOAD_ROOT = _Path("data/raw/관세청/Import Export Performance by Commodity and Country(GW)")
RELEASE_DAY = 15                      # 관세청 월간 통계 공개일(익월 15일 — asof.py CUSTOMS_ 규칙과 동일)
_CONSECUTIVE_FAILS = 0                # 연속 실패 카운터(서버 장애 조기 중단용)
CIRCUIT_BREAK_AFTER = 5


def _ym_add(ym: str, months: int) -> str:
    y, m = int(ym[:4]), int(ym[4:])
    t = y * 12 + (m - 1) + months
    return f"{t // 12:04d}{t % 12 + 1:02d}"


def _last_released_month(today: date | None = None) -> str:
    """오늘 기준 공개가 끝난 마지막 통계 월(YYYYMM). 익월 15일 공개 → 16일부터 전월 조회 가능."""
    today = today or date.today()
    this_ym = f"{today.year:04d}{today.month:02d}"
    return _ym_add(this_ym, -1) if today.day > RELEASE_DAY else _ym_add(this_ym, -2)


def _upload_coverage_month(root: _Path | None = None) -> str | None:
    """수동 업로드 GW xlsx가 값을 가진 마지막 월(YYYYMM). 환경변수 CUSTOMS_UPLOAD_COVERAGE_YYYYMM 우선.

    수동 업로드본 판독 목적의 xlsx 읽기(파이프라인 데이터 I/O가 아님 — 관세청 업로드 파서와 동일 예외).
    대두유 폴더의 최신 연도 시트만 훑어 비용을 낮춘다. 판독 불가 시 None(→ 당년 1월부터 조회).
    """
    env = os.environ.get("CUSTOMS_UPLOAD_COVERAGE_YYYYMM", "").strip()
    if env and env.isdigit() and len(env) == 6:
        return env
    root = root or GW_UPLOAD_ROOT
    if not root.exists():
        return None
    best: str | None = None
    try:
        files = [f for f in root.rglob("*.xlsx")
                 if "Soybean Oil" in str(f) and "_API" not in f.name and ".partial" not in f.name]
        for f in files[:60]:
            try:
                sheets = pd.read_excel(f, sheet_name=None, header=None, engine="openpyxl")
            except Exception:                                       # noqa: BLE001 — DRM·손상 파일
                continue
            for name, sh in sheets.items():
                if not str(name)[:4].isdigit():
                    continue
                year = int(str(name)[:4])
                for _, row in sh.iterrows():
                    label = str(row.iloc[0]) if len(row) else ""
                    m = None
                    if label.strip().endswith("월") and label.strip()[:-1].isdigit():
                        m = int(label.strip()[:-1])
                    if m is None or not (1 <= m <= 12):
                        continue
                    vals = pd.to_numeric(row.iloc[1:], errors="coerce")
                    if vals.notna().any() and (vals.fillna(0) != 0).any():
                        ym = f"{year:04d}{m:02d}"
                        if best is None or ym > best:
                            best = ym
    except Exception as e:                                          # noqa: BLE001
        print(f"[경고] 업로드본 커버리지 판독 실패(비치명): {e}")
        return None
    return best


def _incremental_window(today: date | None = None) -> tuple[str, str, str | None]:
    """(조회 시작 YYYYMM, 조회 끝 YYYYMM, 업로드 커버리지) — 시작 > 끝이면 조회할 월이 없다."""
    today = today or date.today()
    cov = _upload_coverage_month()
    end = _last_released_month(today)
    start = _ym_add(cov, 1) if cov else f"{today.year:04d}01"
    return start, end, cov

COMTRADE_REPORTER_KOREA = "410"


def _parse_xml_response(text: str) -> dict:
    """관세청 XML 응답 → JSON 유사 dict 변환 (A-152a).

    1,360건 호출 0건 성공의 진짜 원인: API는 정상 데이터를 **XML**로 반환하는데
    구 코드는 r.json()만 시도 → 파싱 실패 → 빈 dict → 3차 폴백(URL직삽) 401 연쇄.
    resultCode/resultMsg/items·item 태그를 중첩 위치와 무관하게 탐색해
    {response: {header: {resultCode, resultMsg}, body: {items: [{...}]}}} 구조로
    변환한다(item의 자식 태그 → dict 키). resultCode '00' 외면 resultMsg를 로그.
    """
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        print(f"[경고] XML 파싱 실패: {e} — 응답 미리보기: {text[:200]}")
        return {}

    result_code = (root.findtext(".//resultCode") or "").strip()
    result_msg  = (root.findtext(".//resultMsg") or "").strip()

    items: list[dict] = []
    for item_el in root.iter("item"):
        row = {child.tag: (child.text or "").strip() for child in item_el}
        if row:
            items.append(row)

    if result_code and result_code != "00":
        print(f"[경고] 관세청 API 비정상 응답 코드 {result_code}: {result_msg}")

    return {
        "response": {
            "header": {"resultCode": result_code, "resultMsg": result_msg},
            "body":   {"items": items},
        }
    }


def _fetch(url: str, params: dict[str, Any], max_retries: int = 4) -> dict:
    """외부 API 호출 — 지수 백오프 재시도.

    A-133: 마지막 재시도 실패 시 **예외를 올리지 않는다**. 이전에는 RuntimeError가
    run()까지 전파돼 첫 timeout 하나가 잡 전체를 죽였고, 그 뒤에 있던 nitemtrade
    수집과 UN Comtrade 폴백은 **시도조차 되지 않았다**(connector=all 2회 연속 실패의
    직접 원인). 관세청 GW는 연 단위 조회에 30초를 넘기는 일이 잦아 timeout도 90초로
    올린다. 빈 dict 반환 → 호출부는 그 구간만 결측 처리하고 다음으로 진행한다.
    A-152: JSON 파싱 실패 시 XML 파싱 폴백(_parse_xml_response) — 관세청은 정상
    데이터를 XML로 반환한다.
    """
    delay = 2
    for attempt in range(max_retries):
        try:
            r = httpx.get(url, params=params, timeout=90)
            if r.status_code == 401:
                key_hint = str(params.get("serviceKey", ""))
                if not key_hint and "serviceKey=" in url:
                    # A-152(b): URL직삽 경로에서는 serviceKey가 params가 아니라 URL에 있어
                    #           구 코드가 '?'로 표시하던 로그 버그 — URL에서 앞 8자 추출.
                    key_hint = url.split("serviceKey=", 1)[1].split("&", 1)[0]
                key_hint = (key_hint[:8] + "...") if len(key_hint) > 8 else (key_hint or "?")
                print(
                    f"[오류] 관세청 API 401 인증 실패 — 서비스키 만료·미승인 가능성\n"
                    f"       사용 키 앞 8자리: {key_hint}\n"
                    f"       확인: data.go.kr → 마이페이지 → 활용현황 → 관세청_품목별국가별수출입실적(GW)\n"
                    f"       조치: 재발급 또는 승인 연장 → GitHub Secrets DATA_GO_KR_SERVICE_KEY 갱신"
                )
                return {}
            if r.status_code in (400, 403, 404):
                snippet = r.text[:300].replace("\n", " ")
                print(f"[경고] API {r.status_code} ({url.split('?')[0]}): {snippet}")
                return {}
            r.raise_for_status()
            try:
                return r.json()
            except (_json.JSONDecodeError, ValueError):
                # A-152(a): 관세청은 정상 응답을 XML로 반환 — JSON 실패 시 XML 파싱 시도
                if r.text.lstrip().startswith("<"):
                    parsed = _parse_xml_response(r.text)
                    if parsed:
                        return parsed
                snippet = r.text[:300].replace("\n", " ")
                print(f"[경고] JSON/XML 파싱 실패 (응답 미리보기): {snippet}")
                return {}
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                global _CONSECUTIVE_FAILS
                _CONSECUTIVE_FAILS += 1
                print(f"[경고] API 호출 최종 실패 ({url.split('?')[0]}): {type(e).__name__}: {e} "
                      f"— 해당 구간 결측 처리 후 계속 진행 (A-133)")
                return {}
            time.sleep(delay)
            delay *= 2
    return {}


def _mark_success() -> None:
    global _CONSECUTIVE_FAILS
    _CONSECUTIVE_FAILS = 0


def _circuit_open() -> bool:
    """연속 실패가 임계를 넘으면 서버 측 장애로 보고 남은 호출을 중단한다(A-253)."""
    return _CONSECUTIVE_FAILS >= CIRCUIT_BREAK_AFTER


def _parse_items(data: dict) -> list[dict]:
    """관세청 API 응답에서 items 추출. 단일 항목(dict)·리스트·items.item 구조 모두 대응."""
    body = data.get("response", {}).get("body", {})
    raw = body.get("items", [])
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        inner = raw.get("item", [])
        return [inner] if isinstance(inner, dict) else (inner or [])
    return []


def _fetch_customs_range(
    service_key: str,
    strt_yymm: str,
    end_yymm: str,
    hs_sgn: str,
    cnty_cd: str | None = None,
    use_nitemtrade: bool = True,
) -> list[dict]:
    """관세청 API 기간·국가 조회. 디코딩/인코딩/직삽 키 3단계 폴백.

    strt_yymm, end_yymm: YYYYMM 형식 (예: '202001', '202012')
    hs_sgn: 6단위 HS 코드 (예: '150710', '150790')
    cnty_cd: ISO 2자리 국가코드 (예: 'US', 'AR') — None이면 Itemtrade(전국가 합계) 사용
    use_nitemtrade: True=nitemtrade(국가별), False=Itemtrade(전체)
    """
    base_url = NITEMTRADE_BASE if use_nitemtrade else ITEMTRADE_BASE
    base_params: dict[str, Any] = {
        "strtYymm": strt_yymm,
        "endYymm":  end_yymm,
        "hsSgn":    hs_sgn,
    }
    if cnty_cd and use_nitemtrade:
        base_params["cntyCd"] = cnty_cd

    # 1차: 디코딩 키 → httpx params (포털 URL-인코딩 키 이중 인코딩 방지)
    decoded_key = unquote(service_key)
    data = _fetch(base_url, {"serviceKey": decoded_key, **base_params})
    items = _parse_items(data)
    if items:
        return items
    # 정상 응답(resultCode 00)인데 item이 0건이면 '해당 월 무역 없음/미공개'다 — 키 형식 폴백을 돌리면
    #   URL 직삽 경로가 401을 내며 '인증 실패'로 오진된다(2026-11-19 실측). 여기서 종료한다.
    header = ((data or {}).get("response") or {}).get("header") or {}
    if str(header.get("resultCode", "")).strip() == "00":
        return []

    # 2차: 원본 키 그대로 params (일반 hex 서비스키인 경우 decoded = original)
    if decoded_key != service_key:
        data2 = _fetch(base_url, {"serviceKey": service_key, **base_params})
        items2 = _parse_items(data2)
        if items2:
            return items2

    # 3차: 원본 인코딩 키를 URL에 직접 삽입 (httpx 인코딩 완전 우회)
    direct_url = f"{base_url}?serviceKey={service_key}"
    fb_data = _fetch(direct_url, base_params)
    return _parse_items(fb_data)


def _normalize_customs_df(all_rows: list[dict], source_tag: str) -> pd.DataFrame:
    """관세청 API rows → 정규화 DataFrame."""
    df = pd.DataFrame(all_rows)
    df["ingested_at"] = pd.Timestamp.utcnow()
    df["source_name"] = source_tag

    col_map = {
        "strtYymm":  "period_start",
        "endYymm":   "period_end",
        "cntyCd":    "country_code",
        "cntyNm":    "country_name",
        "imAmt":     "import_cif_usd",
        "impAmt":    "import_cif_usd",
        "imWgt":     "import_weight_kg",
        "wgt":       "import_weight_kg",
        "exAmt":     "export_fob_usd",
        "expAmt":    "export_fob_usd",
        "hsSgn":     "hs_code",
        # A-158: XML 응답의 실제 태그 — A-152로 파싱은 성공했으나(11,165행 수집) 여기서
        #   유실됨. 구 JSON 필드명만 매핑해 price_date 파생 불가 → attach_asof ValueError
        #   → 통합 런 관세청 잡 exit 1의 직접 원인.
        "year":        "stat_year",
        "statKor":     "country_name",
        "hsCode":      "hs_code",
        "impDlr":      "import_cif_usd",
        "impWgt":      "import_weight_kg",
        "expDlr":      "export_fob_usd",
        "expWgt":      "export_weight_kg",
        "balPayments": "trade_balance_usd",
    }
    # A-158(b): hsCode(XML)·hsSgn(요청키)이 둘 다 있으면 rename이 hs_code **중복 컬럼**을
    # 만들어 이후 df["hs_code"]가 DataFrame이 되며 .str에서 크래시(로컬 재현). 요청키
    # hsSgn을 정본으로 두고 응답 echo(hsCode)는 원명 유지.
    if "hsCode" in df.columns and "hsSgn" in df.columns:
        col_map = {k: v for k, v in col_map.items() if k != "hsCode"}
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    # A-158(b'): JSON·XML 혼재 프레임은 금액·중량도 중복 표준명을 만든다
    # (impDlr·impAmt→import_cif_usd 등) → 중복 라벨을 행 단위 첫 비결측으로 병합.
    if not df.columns.is_unique:
        dup_names = sorted({c for c in df.columns[df.columns.duplicated()]})
        merged: dict[str, pd.Series] = {}
        for col in dict.fromkeys(df.columns):        # 등장 순서 보존
            sub = df.loc[:, df.columns == col]
            merged[col] = sub.iloc[:, 0] if sub.shape[1] == 1 else sub.bfill(axis=1).iloc[:, 0]
        df = pd.DataFrame(merged)
        print(f"[정보] 혼재 응답 중복 컬럼 병합: {dup_names}")

    # A-158(c): 구 배타 분기(if/elif)는 JSON·XML 행이 **한 프레임에 섞이면** 뒤 분기가
    # 영원히 실행되지 않아 한쪽 전량이 price_date NaT로 남았다(13차 런 10,966행 전량
    # as-of 결측의 유력 경로). 행 단위 coalesce로 교체.
    pd_parts = []
    for col, fmt in (("period_start", "%Y%m"), ("strtYymm", "%Y%m"), ("stat_year", "%Y")):
        if col in df.columns:
            pd_parts.append(pd.to_datetime(df[col].astype(str).str.strip(),
                                           format=fmt, errors="coerce"))
    # A-182: 런 32068230640 실증 — 이번 XML 응답의 year 태그가 "2023.02" **연.월 형식**으로
    # 와 %Y 파싱이 7,143건 전량 실패(fail-loud가 정상 차단). 연월 형식 폴백 추가.
    if "stat_year" in df.columns:
        pd_parts.append(pd.to_datetime(df["stat_year"].astype(str).str.strip(),
                                       format="%Y.%m", errors="coerce"))
    if pd_parts:
        price_date = pd_parts[0]
        for part in pd_parts[1:]:
            price_date = price_date.fillna(part)
        df["price_date"] = price_date
        if "stat_year" in df.columns:
            # A-182: 연간 라벨은 stat_year가 순수 연도(YYYY)인 행에만 — 연.월 형식은 월 단위
            annual_mask = (df["price_date"].notna()
                           & df["stat_year"].astype(str).str.strip().str.fullmatch(r"\d{4}"))
            if "note" not in df.columns:
                df["note"] = ""
            df.loc[annual_mask & df["note"].astype(str).eq(""), "note"] = "연간 집계(XML 응답)"
    n_nat = int(df["price_date"].isna().sum()) if "price_date" in df.columns else len(df)
    if n_nat:
        print(f"[경고] price_date 파생 실패 {n_nat}건 — 원본 기간 필드 확인 필요 "
              f"(보유 컬럼: {sorted(set(df.columns) & {'period_start','strtYymm','stat_year'})})")

    # A-152(c): XML items에는 hsCd='-'인 집계 행(HS코드 합계)이 올 수 있다.
    #           삭제하지 않고 유지하되 note에 '집계행'을 표기해 상세 행과 구분한다.
    agg_mask = pd.Series(False, index=df.index)
    for hs_col in ("hsCd", "hs_code"):
        if hs_col in df.columns:
            agg_mask |= df[hs_col].astype(str).str.strip() == "-"
    if agg_mask.any():
        if "note" not in df.columns:
            df["note"] = ""
        df.loc[agg_mask, "note"] = (
            df.loc[agg_mask, "note"].fillna("").astype(str)
            .apply(lambda s: f"{s} 집계행".strip() if s else "집계행")
        )
        print(f"[정보] 집계행(hsCd='-') {int(agg_mask.sum())}건 — note='집계행'으로 표기 후 유지")

    return df


def fetch_customs_total_imports(
    start_year: int = 2017,
    end_year: int | None = None,
    window: tuple[str, str] | None = None,
) -> pd.DataFrame:
    """관세청 API 1 — 대두유(HS 1507) 전체 수출입실적 (국가 구분 없음).

    엔드포인트: https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList
    수집 방식: 연도별 × HS코드별 API 호출 (cntyCd 미포함)
    """
    service_key = os.environ.get("DATA_GO_KR_SERVICE_KEY", "").strip()
    if not service_key:
        return pd.DataFrame()

    if end_year is None:
        end_year = date.today().year

    today_ym = date.today().strftime("%Y%m")
    all_rows: list[dict] = []
    total_calls = 0

    # A-253: window가 주어지면 그 월 구간 1회(증분), 아니면 연 단위(백필)
    periods = [window] if window else [
        (f"{yr:04d}01", f"{yr:04d}12" if yr < date.today().year else today_ym)
        for yr in range(start_year, end_year + 1)]
    for strt_ym, end_ym in periods:
        if _budget_exceeded():
            print(f"[경고] 시간 예산({_BUDGET_S:.0f}s) 초과 — Itemtrade {strt_ym}~ 중단, 수집분 저장 진행")
            break
        for hs_sgn in HS_CODES_ALL:
            if _budget_exceeded() or _circuit_open():
                break
            total_calls += 1
            items = _fetch_customs_range(service_key, strt_ym, end_ym, hs_sgn, use_nitemtrade=False)
            if items:
                _mark_success()
                for item in items:
                    item.setdefault("hsSgn", hs_sgn)
                all_rows.extend(items)
            time.sleep(0.3)
    if _circuit_open():
        print(f"[경고] 연속 실패 {_CONSECUTIVE_FAILS}회 — data.go.kr 응답 없음으로 판단, 남은 Itemtrade 호출 중단")

    print(f"[정보] Itemtrade: 총 {total_calls}건 호출, {len(all_rows)}건 수집")
    if not all_rows:
        return pd.DataFrame()

    df = _normalize_customs_df(all_rows, "KoreaCustoms/Itemtrade")
    print(f"[완료] 품목별 전체 수출입실적 {len(df)}건 (HS 1507, {start_year}~{end_year})")
    return df


def fetch_customs_sbo_imports(
    start_year: int = 2017,
    end_year: int | None = None,
    country_codes: list[str] | None = None,
    window: tuple[str, str] | None = None,
) -> pd.DataFrame:
    """관세청 API 2 — 대두유(HS 1507) 국가별 수입 통계 (연도별·국가별 수집).

    엔드포인트: https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList
    Args:
        start_year:    수집 시작 연도 (기본 2017)
        end_year:      수집 종료 연도 (기본 현재 연도, HISTORICAL_END_YEAR 환경변수 우선)
        country_codes: 수집 대상 국가 코드 목록 (기본 COUNTRY_CODES: US/AR/BR/CN/ID)

    수집 방식:
        - 연도별 × HS코드별 × 국가별 순서로 API 호출
        - HS코드 2개 × 국가 5개 × 연도 N개 = 총 N×10 호출
        - 각 호출 후 0.3초 대기 (레이트 리밋 준수)
    """
    service_key = os.environ.get("DATA_GO_KR_SERVICE_KEY", "").strip()
    if not service_key:
        print(
            "[경고] DATA_GO_KR_SERVICE_KEY 미등록 — 관세청 API 수집 건너뜀.\n"
            "       등록: data.go.kr → 관세청_품목별국가별수출입실적(GW) → GitHub Secrets"
        )
        return pd.DataFrame()

    if end_year is None:
        env_end = os.environ.get("HISTORICAL_END_YEAR", "").strip()
        end_year = int(env_end) if env_end else date.today().year
    if country_codes is None:
        country_codes = COUNTRY_CODES

    today_ym = date.today().strftime("%Y%m")
    all_rows: list[dict] = []
    total_calls = 0
    success_calls = 0

    periods = [window] if window else [
        (f"{yr:04d}01", f"{yr:04d}12" if yr < date.today().year else today_ym)
        for yr in range(start_year, end_year + 1)]

    def _one(strt_ym: str, end_ym: str, hs_sgn: str, cnty_cd: str) -> list[dict]:
        if _budget_exceeded() or _circuit_open():
            return []
        items = _fetch_customs_range(service_key, strt_ym, end_ym, hs_sgn, cnty_cd)
        time.sleep(0.3)
        if items:
            _mark_success()
            for item in items:
                item.setdefault("hsSgn",  hs_sgn)
                item.setdefault("cntyCd", cnty_cd)
        return items

    # A-253: (HS×국가) 쌍을 병렬 5로 처리(A-101 GW 스크립트와 동일 동시성) — 순차 96회의 대기 누적 제거
    from concurrent.futures import ThreadPoolExecutor
    for strt_ym, end_ym in periods:
        if _budget_exceeded():
            print(f"[경고] 시간 예산({_BUDGET_S:.0f}s) 초과 — nitemtrade {strt_ym}~ 중단, 수집분 저장 진행")
            break
        pairs = [(hs, cc) for hs in HS_CODES_ALL for cc in country_codes]
        with ThreadPoolExecutor(max_workers=int(os.environ.get("CUSTOMS_WORKERS", "5"))) as ex:
            for items in ex.map(lambda p: _one(strt_ym, end_ym, *p), pairs):
                total_calls += 1
                if items:
                    all_rows.extend(items)
                    success_calls += 1
        if _circuit_open():
            print(f"[경고] 연속 실패 {_CONSECUTIVE_FAILS}회 — data.go.kr 응답 없음으로 판단, 남은 nitemtrade 호출 중단")
            break

    print(f"[정보] nitemtrade: 총 {total_calls}건 호출, {success_calls}건 성공")

    if not all_rows:
        print(f"[경고] 관세청 API: HS 1507 수집 실패 ({start_year}~{end_year})")
        return pd.DataFrame()

    df = _normalize_customs_df(all_rows, "KoreaCustoms/nitemtrade")
    print(f"[완료] 국가별 수입통계 {len(df)}건 (HS 1507, {start_year}~{end_year}, {len(country_codes)}개국)")
    return df


def fetch_comtrade_sbo_imports_fallback(start_year: int = 2017) -> pd.DataFrame:
    """UN Comtrade Plus — 대두유(HS 1507) 한국 수입 통계 (comtradeapicall 패키지).

    무료: previewFinalData (500건/일)
    유료: getFinalData (10,000건/일, UN_COMTRADE_API_KEY 필요)
    """
    sub_key = os.environ.get("UN_COMTRADE_API_KEY", "").strip()

    try:
        import comtradeapicall  # type: ignore
    except ImportError:
        print("[경고] comtradeapicall 미설치 — pip install comtradeapicall")
        return pd.DataFrame()

    # A-067 진단 해결: ①12개월 일괄 → 분기(3개월) 배치로 500건 상한 회피
    #   ②429 시 break(전체 중단) → 지수 백오프 재시도 후 다음 배치 계속
    #   ③무료(previewFinalData 500건) 경로 로그 명시
    print(f"[정보] UN Comtrade 경로: {'getFinalData(유료키)' if sub_key else 'previewFinalData(무료·500건/호출)'}")
    end_d = date.today().replace(day=1) - timedelta(days=1)
    quarter_batches: list[tuple[int, int, list[str]]] = []
    d = date(start_year, 1, 1)
    cur: list[str] = []
    while d.replace(day=1) <= end_d.replace(day=1):
        cur.append(d.strftime("%Y%m"))
        if d.month % 3 == 0:          # 분기 경계
            quarter_batches.append((d.year, (d.month - 1) // 3 + 1, cur))
            cur = []
        d = date(d.year + (d.month // 12), (d.month % 12) + 1, 1)
    if cur:
        quarter_batches.append((d.year, (d.month - 1) // 3 + 1, cur))

    def _call_with_backoff(period_str: str, max_retries: int = 4):
        delay = 2
        for attempt in range(max_retries):
            try:
                call_fn = comtradeapicall.getFinalData if sub_key else comtradeapicall.previewFinalData
                kwargs: dict[str, Any] = dict(
                    typeCode="C", freqCode="M", clCode="HS",
                    period=period_str, reporterCode=COMTRADE_REPORTER_KOREA,
                    cmdCode="1507", flowCode="M",
                    partnerCode=None, partner2Code=None,
                    customsCode=None, motCode=None,
                    maxRecords=10000 if sub_key else 500,
                    format_output="JSON", aggregateBy=None,
                    breakdownMode="classic", countOnly=None, includeDesc=True,
                )
                if sub_key:
                    kwargs["subscription_key"] = sub_key
                return call_fn(**kwargs)
            except Exception as e:
                if ("429" in str(e) or "rate" in str(e).lower()) and attempt < max_retries - 1:
                    print(f"[경고] Comtrade 레이트 리밋 — {delay}s 후 재시도 ({attempt+1}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2
                    continue
                print(f"[경고] Comtrade {period_str[:6]}~: {e}")
                return None

    all_frames: list[pd.DataFrame] = []
    for yr, q, periods in quarter_batches:
        df = _call_with_backoff(",".join(periods))
        if df is not None and not df.empty:
            all_frames.append(df)
            print(f"[정보] UN Comtrade {yr}Q{q}: {len(df)}건")
        time.sleep(1)

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    period_col  = next((c for c in ["period", "Period"] if c in combined.columns), None)
    val_col     = next((c for c in ["primaryValue", "tradeValue", "cifvalue"] if c in combined.columns), None)
    wgt_col     = next((c for c in ["netWgt", "netWeight"] if c in combined.columns), None)
    partner_col = next((c for c in ["partnerDesc", "partnerCode"] if c in combined.columns), None)

    result = pd.DataFrame()
    if period_col:
        result["price_date"] = pd.to_datetime(combined[period_col].astype(str), format="%Y%m", errors="coerce")
    if val_col:
        result["import_cif_usd"] = pd.to_numeric(combined[val_col], errors="coerce")
    if wgt_col:
        result["import_weight_kg"] = pd.to_numeric(combined[wgt_col], errors="coerce")
    if partner_col:
        result["country_name"] = combined[partner_col].astype(str)
    result["source_name"] = "UNComtrade/comtradeapicall"
    result["ingested_at"] = pd.Timestamp.utcnow()
    print(f"[정보] UN Comtrade 총 {len(result)}건 ({start_year}~현재)")
    return result


def run() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today_str  = date.today().strftime("%Y%m%d")

    end_year = int(os.environ.get("HISTORICAL_END_YEAR", str(date.today().year)))
    # A-216(조정자 확인 8/28): 히스토리는 수동 업로드 GW xlsx가 2010~2026.07을 커버 —
    # 일별 런이 매일 2017~전체를 재수집할 필요가 없고(잡 4~6h 지연·429의 원인),
    # 최신분 갱신만 하면 된다. 비백필은 **당년만** 수집(A-110 climate 증분화 동일 패턴).
    window: tuple[str, str] | None = None
    if os.environ.get("BACKFILL_MODE", "").lower() == "true":
        start_year = int(os.environ.get("HISTORICAL_START_YEAR", "2017"))
    else:
        # A-253(승인자 지시 9/9): 업로드본이 덮는 월은 조회하지 않고, 공개(익월 15일)가 끝난 월만 조회.
        # 조회할 월이 없으면 API를 한 번도 부르지 않고 정상 종료한다(당년 전체 재조회 폐기).
        start_year = int(os.environ.get("CUSTOMS_INCREMENTAL_START_YEAR", str(end_year)))
        w_start, w_end, cov = _incremental_window()
        print(f"[정보] 증분 모드 — 업로드본 커버리지 {cov or '미확인'} · 공개 완료 월 {w_end} "
              f"→ 조회 구간 {w_start}~{w_end}")
        if w_start > w_end:
            print("[정보] 조회할 신규 월 없음(미공개·미입력 월은 건너뜀) — API 호출 없이 정상 종료")
            return
        window = (w_start, w_end)

    print(f"[정보] 관세청 수집 범위: {start_year}년 ~ {end_year}년 · HS {len(HS_CODES_ALL)}종 "
          f"(대두유 {len(HS_CODES_SOYBEAN_OIL)} · 대체재 {len(HS_CODES_SUBSTITUTES)} · "
          f"보완재 {len(HS_CODES_COMPLEMENTS)})")

    # A-133: 소스별 격리 — Itemtrade가 죽어도 nitemtrade·Comtrade 폴백은 계속 시도한다
    def _safe(label: str, fn, **kw) -> pd.DataFrame:
        try:
            return fn(**kw)
        except Exception as e:
            print(f"[경고] {label} 수집 실패({type(e).__name__}: {e}) — 다음 소스로 진행")
            return pd.DataFrame()

    # API 1: 품목별 전체 (Itemtrade — 국가 구분 없음)
    df_total = _safe("Itemtrade", fetch_customs_total_imports,
                     start_year=start_year, end_year=end_year, window=window)

    # API 2: 품목별 국가별 (nitemtrade)
    df_by_country = _safe("nitemtrade", fetch_customs_sbo_imports,
                          start_year=start_year, end_year=end_year, window=window)

    # 두 소스 병합
    frames = [f for f in [df_total, df_by_country] if not f.empty]
    if frames:
        df = pd.concat(frames, ignore_index=True)
    else:
        df = pd.DataFrame()

    if df.empty:
        print("[정보] 관세청 미수집 — UN Comtrade 폴백 시도")
        df = _safe("UN Comtrade", fetch_comtrade_sbo_imports_fallback, start_year=start_year)

    if df.empty:
        print("[경고] 관세청·UN Comtrade 모두 실패 — API 키 확인 필요")
        print("       DATA_GO_KR_SERVICE_KEY: data.go.kr 포털 발급")
        print("       UN_COMTRADE_API_KEY: comtradeplus.un.org 발급")
        if window:
            print(f"[정보] 증분 구간 {window[0]}~{window[1]} 미수집 — 업로드본이 히스토리를 덮으므로 "
                  "비치명 종료(다음 런 재시도)")
            return
        raise SystemExit(1)   # 백필 전 소스 실패는 조용히 넘기지 않는다 — 잡 실패로 표면화

    out = f"{OUTPUT_DIR}/customs_import_{today_str}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    df = attach_asof(df, source="CUSTOMS_")
    # A-158(d): 13차 런에서 전량 as-of 결측 parquet이 조용히 저장돼 G1 게이트에서야
    # 발각됨 — 커넥터가 자체 차단한다(전량 결측 = 파생 로직 결함, 저장 무의미).
    if df["event_time"].isna().all():
        raise RuntimeError("[오류] 관세청 event_time 전량 결측 — price_date 파생 실패. "
                           "parquet을 저장하지 않습니다(기간 필드 매핑 점검 필요).")
    n_nat = int(df["event_time"].isna().sum())
    if n_nat:
        print(f"[경고] event_time 결측 {n_nat}건 제외 후 저장")
        df = df[df["event_time"].notna()]
    df.to_parquet(out, index=False)
    print(f"[완료] 대두유 수입통계 {len(df)}건 저장 → {out}")


if __name__ == "__main__":
    run()
