"""
지정학 리스크 지수 커넥터 — WBS 1.1.6
수집 대상: Caldara & Iacoviello GPR Index (공개) · Perplexity 실시간 지정학 뉴스
실행 환경: 로컬 Docker(n8n → runner 컨테이너) 또는 GitHub Actions
"""

from __future__ import annotations

import io
import os
import re
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
# A-138: 구 policyuncertainty.com 미러 404 — GPR(Caldara-Iacoviello)의 원 호스트는
#        matteoiacoviello.com이며 policyuncertainty.com은 EPU 사이트라 미러가 사라짐.
#        → 원 호스트 우선 후보 체인으로 교체 + 성공 URL 명시 로깅.
GPR_URL_CANDIDATES: list[tuple[str, str]] = [
    # (URL, 지표코드) — 순서대로 시도. daily 파일은 GPR_DAILY로 별도 적재.
    ("https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls",       "GPR"),
    ("https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls", "GPR_DAILY"),
    ("https://www.policyuncertainty.com/media/GPR_Web_latest.xlsx",          "GPR"),  # 최후 폴백
]
PERPLEXITY_MODEL = "sonar-pro"  # MEMORY L-006/L-007


def _read_gpr_excel(content: bytes, url: str) -> pd.DataFrame | None:
    """GPR 엑셀 바이트 판독 — .xls는 xlrd가 필요할 수 있어 실패 시 명시 오류 (A-138)."""
    try:
        # engine 미지정: pandas가 콘텐츠·확장자로 추론 (.xlsx=openpyxl, .xls=xlrd)
        return pd.read_excel(io.BytesIO(content))
    except ImportError as e:
        print(f"[오류] GPR 엑셀 판독 실패 — .xls 엔진(xlrd) 미설치 추정: {e} "
              f"(pip install xlrd 필요, URL: {url})")
        return None
    except Exception as e:
        print(f"[경고] GPR 엑셀 판독 실패 ({url}): {e}")
        return None


def _parse_gpr_frame(df_raw: pd.DataFrame, indicator: str, url: str) -> pd.DataFrame:
    """GPR 원본 프레임 → 표준 롱포맷. 컬럼명은 소스별로 달라 유연 탐지 (A-138).

    날짜: Year+Month 조합 또는 date/day/month 단일 날짜 컬럼 모두 지원.
    값:   'GPR' 포함 컬럼 자동 탐지(대소문자 무시) — 정확 일치(GPR/GPRD) 우선.
    """
    df_raw = df_raw.copy()
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    cols = list(df_raw.columns)

    # ── 값 컬럼: 정확 일치 우선 → 'GPR' 포함(파생 GPRT/GPRA/GPRH 제외 우선) ──
    gpr_col = next((c for c in cols if c.upper() in ("GPR", "GPRD")), None)
    if gpr_col is None:
        gpr_col = next((c for c in cols if "GPR" in c.upper()), None)
    if gpr_col is None:
        print(f"[경고] GPR 값 컬럼 탐지 실패 ({url}). 실제 컬럼: {cols}")
        return pd.DataFrame()

    # ── 날짜: Year+Month 조합 우선, 없으면 단일 날짜형 컬럼 ──
    year_col  = next((c for c in cols if "year"  in c.lower()), None)
    month_col = next((c for c in cols if "month" in c.lower()), None)
    if year_col and month_col and pd.api.types.is_numeric_dtype(df_raw[month_col]):
        df = df_raw[[year_col, month_col, gpr_col]].dropna()
        price_date = pd.to_datetime(
            df[year_col].astype(int).astype(str) + "-" +
            df[month_col].astype(int).astype(str).str.zfill(2) + "-01",
            errors="coerce",
        )
    else:
        date_col = next(
            (c for c in cols
             if any(k in c.lower() for k in ("date", "day", "month"))), None)
        if date_col is None:
            print(f"[경고] GPR 날짜 컬럼 탐지 실패 ({url}). 실제 컬럼: {cols}")
            return pd.DataFrame()
        df = df_raw[[date_col, gpr_col]].dropna()
        price_date = pd.to_datetime(df[date_col], errors="coerce")

    out = pd.DataFrame({
        "price_date": price_date,
        "value":      pd.to_numeric(df[gpr_col], errors="coerce"),
    }).dropna()
    out["source_name"]    = "Caldara_Iacoviello"
    out["indicator_code"] = indicator
    out["unit"]           = "index (baseline≈100)"
    out["ingested_at"]    = pd.Timestamp.utcnow()
    # 수집 범위 표준화: 2017-01-01 이후 (다른 커넥터와 통일)
    return out[out["price_date"] >= pd.Timestamp("2017-01-01")].reset_index(drop=True)


def _fetch_gpr_index() -> pd.DataFrame:
    """Caldara & Iacoviello GPR Index 다운로드 — 후보 URL 체인 (A-138, API 키 불필요).

    월별 지수(GPR)는 첫 성공 URL을 채택하고, 일별 파일(data_gpr_daily_recent.xls)은
    가용하면 GPR_DAILY 지표로 **추가** 적재한다.
    """
    frames: list[pd.DataFrame] = []
    monthly_done = False
    for url, indicator in GPR_URL_CANDIDATES:
        if indicator == "GPR" and monthly_done:
            continue  # 월별은 첫 성공 URL만 사용 (폴백 중복 방지)
        try:
            r = httpx.get(url, timeout=60, follow_redirects=True)
            r.raise_for_status()
        except Exception as e:
            print(f"[경고] GPR 다운로드 실패 ({url}): {e} — 다음 후보 시도")
            continue
        df_raw = _read_gpr_excel(r.content, url)
        if df_raw is None or df_raw.empty:
            continue
        parsed = _parse_gpr_frame(df_raw, indicator, url)
        if parsed.empty:
            continue
        print(f"[완료] GPR({indicator}) {len(parsed)}건 수집 — 성공 URL: {url}")
        frames.append(parsed)
        if indicator == "GPR":
            monthly_done = True

    if not frames:
        print("[경고] GPR 인덱스: 전 후보 URL 실패")
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _fetch_gpr_realtime() -> pd.DataFrame:
    """Perplexity 실시간 검색으로 GPR 최신 동향 수집."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("[경고] PERPLEXITY_API_KEY 미등록 — 지정학 실시간 수집 건너뜀.")
        return pd.DataFrame()

    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    prompt = (
        "What is the current Geopolitical Risk (GPR) index level? "
        "Also provide the latest GPR score if available. "
        "Format: GPR: [numeric value] ([source/date]). "
        "If exact GPR index is unavailable, provide qualitative assessment: HIGH/MEDIUM/LOW."
    )
    try:
        r = client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text = r.choices[0].message.content
        today = date.today().isoformat()

        rows = []
        gpr_match = re.search(r"GPR[:\s]+([0-9]+\.?[0-9]*)", text, re.IGNORECASE)
        if gpr_match:
            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/GPR",
                "indicator_code": "GPR_REALTIME",
                "value":          float(gpr_match.group(1)),
                "unit":           "index (baseline≈100)",
                "note":           "[PERPLEXITY-PROXY]",
            })

        level_match = re.search(r"\b(HIGH|MEDIUM|LOW)\b", text, re.IGNORECASE)
        if level_match and not gpr_match:
            level_map = {"HIGH": 250.0, "MEDIUM": 150.0, "LOW": 80.0}
            level = level_match.group(1).upper()
            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/GPR",
                "indicator_code": "GPR_QUALITATIVE",
                "value":          level_map[level],
                "unit":           "index (baseline≈100)",
                "note":           f"[QUALITATIVE:{level}]",
            })

        if not rows:
            print(f"[경고] GPR 실시간 파싱 실패. 원문: {text[:200]}")

        df = pd.DataFrame(rows)
        if not df.empty:
            df["price_date"] = pd.to_datetime(df["price_date"])
            df["ingested_at"] = pd.Timestamp.utcnow()
        return df
    except Exception as e:
        print(f"[경고] Perplexity GPR 수집 실패: {e}")
        return pd.DataFrame()


# A-139: Hormuz 위협 수준 파싱 실패 — Perplexity 응답이 "VALUE: **HIGH** (…SEVERE…)"처럼
#        마크다운 장식·비표준 어휘(SEVERE/ELEVATED)를 포함해 구형 regex가 미매칭.
#        → 장식 제거 후 어휘 확장 매핑 + 숫자(1~3) 직접 표기 허용.
_THREAT_LEVEL_MAP: dict[str, float] = {
    "SEVERE": 3.0, "HIGH": 3.0,
    "ELEVATED": 2.0, "MODERATE": 2.0, "MEDIUM": 2.0,
    "LOW": 1.0,
}


def _parse_threat_level(text: str) -> tuple[float, str] | None:
    """응답 텍스트에서 위협 수준 추출 (A-139). 실패 시 None — 행 미생성(결측 처리).

    ① 마크다운 장식(**, __, `) 제거
    ② SEVERE/HIGH/ELEVATED/MODERATE/MEDIUM/LOW 단어 탐지(대소문자 무시) → 3/3/2/2/2/1
    ③ 'VALUE: 2' 등 숫자 1~3 직접 표기 허용
    """
    clean = re.sub(r"(\*\*|__|`)", "", text)
    word_match = re.search(
        r"\b(SEVERE|HIGH|ELEVATED|MODERATE|MEDIUM|LOW)\b", clean, re.IGNORECASE)
    if word_match:
        label = word_match.group(1).upper()
        return _THREAT_LEVEL_MAP[label], label
    num_match = re.search(r"VALUE\s*[:=]?\s*([1-3])\b", clean, re.IGNORECASE)
    if num_match:
        val = float(num_match.group(1))
        return val, f"NUMERIC:{num_match.group(1)}"
    return None


def _fetch_hormuz_realtime() -> pd.DataFrame:
    """Perplexity 실시간 호르무즈 해협 모니터링.

    Inspired by Globot early-warning methodology (github.com/Vector897/Globot):
    AIS 선박 이상 · AWRP 보험료 급등 · 이란-미국 긴장 신호
    SBO 관련성: 호르무즈 봉쇄 → 유가 급등 → 벙커유 비용 → CFR 운임 프리미엄 + 3~8%
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("[경고] PERPLEXITY_API_KEY 미등록 — 호르무즈 모니터링 건너뜀.")
        return pd.DataFrame()

    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    prompt = (
        "Provide the latest risk assessment for the Strait of Hormuz for tanker shipping. "
        "Include: "
        "(1) Current threat level for tanker traffic: HIGH / MEDIUM / LOW, "
        "(2) Any IRGC or Houthi vessel incidents in the past 7 days (Yes/No + brief), "
        "(3) War risk premium surcharge multiplier vs baseline (e.g. 2x, 3x, 5x), "
        "(4) Any tanker re-routing to Cape of Good Hope reported this week (count or None). "
        "Format each item as: METRIC: [name] | VALUE: [value] | SOURCE: [source] | DATE: [date]"
    )
    today = date.today().isoformat()
    try:
        r = client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text = r.choices[0].message.content
        rows = []

        # A-139: Threat level — 마크다운 장식 제거 + 어휘 확장(SEVERE/ELEVATED) + 숫자 허용.
        # 위협 수준 항목(threat/level 언급 줄) 우선, 없으면 전문에서 탐지.
        clean_text = re.sub(r"(\*\*|__|`)", "", text)
        threat_scope = clean_text
        scope_match = re.search(
            r"(?:threat|level)[^\n]*", clean_text, re.IGNORECASE)
        if scope_match:
            threat_scope = scope_match.group(0)
        parsed_level = _parse_threat_level(threat_scope) or _parse_threat_level(clean_text)
        if parsed_level:
            level_value, level_label = parsed_level
            narrative = re.sub(r"\s+", " ", clean_text).strip()[:600]
            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/Hormuz",
                "indicator_code": "HORMUZ_THREAT_LEVEL",
                "value":          level_value,
                "unit":           "1=Low/2=Med/3=High",
                # A-273: 답변 본문(사건·통항·보험료 서사)을 보존 — 종전엔 라벨만 남겨 서사가 소실됐다
                "note":           f"[QUALITATIVE:{level_label}] {narrative}",
            })
        else:
            # 파싱 실패 → 원문 로그 + 결측 처리(행 미생성)
            print(f"[경고] Hormuz 위협 수준 파싱 실패 — 결측 처리. 원문: {text[:200]}")

        # AWRP multiplier (장식 제거된 텍스트 기준)
        awrp_match = re.search(
            r"METRIC:[^|]*(?:premium|AWRP|war risk)[^|]*\|[^|]*VALUE:\s*([0-9]+\.?[0-9]*)\s*[xX×]?",
            clean_text, re.IGNORECASE
        )
        if awrp_match:
            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/Hormuz",
                "indicator_code": "HORMUZ_AWRP_MULTIPLIER",
                "value":          float(awrp_match.group(1)),
                "unit":           "× baseline AWRP",
                "note":           "[PERPLEXITY-PROXY]",
            })

        if not rows:
            print(f"[경고] Hormuz 파싱 실패. 원문: {text[:200]}")
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["price_date"] = pd.to_datetime(df["price_date"])
        df["ingested_at"] = pd.Timestamp.utcnow()
        return df
    except Exception as e:
        print(f"[경고] Hormuz 실시간 수집 실패: {e}")
        return pd.DataFrame()


# A-269(2026-09-14): 프록시 응답을 단일 행으로 강제하고, 수치는 선언 키 값에서 먼저 뽑는다.
_ONE_LINE_SYSTEM = ("You are a data extraction service. Respond with ONLY the single formatted line requested. "
                    "No preamble, no citations, no markdown, no explanation. If a field is unknown write 'unknown'.")
_ONE_LINE_SUFFIX = " Respond with ONLY that single line."


_DATE_SEGMENT_RE = re.compile(r"\b(?:REPORT_)?DATE\s*:[^|]*|\bSOURCE\s*:[^|]*", re.IGNORECASE)
_DATE_TOKEN_RE = re.compile(r"\b(?:19|20)\d{2}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}\b",
                            re.IGNORECASE)


def _extract_value(text: str, preferred_keys: tuple[str, ...]) -> float:
    """선언 키(예: RATE:) 세그먼트 안의 첫 숫자를 우선, 없으면 날짜·출처 세그먼트를 제거한 본문의 첫 숫자.

    A-271: 구 정규식은 콜론 뒤 글자 1개만 허용해 'ACTUAL: Global … 3.2 MMT'를 못 잡고, 폴백이 'September 11'의
    11이나 연도 2026을 값으로 저장했다(아카이브 9/13 WASDE_CONSENSUS_SCORE=11.0 실증). 선언 키가 있는데 값이
    없으면(응답 'unknown') NaN — 값 위장 금지.
    """
    clean = str(text or "").replace("**", "").replace("`", "").replace("[", "").replace("]", "")
    for k in preferred_keys:
        m = re.search(rf"\b{k}\s*:([^|]{{0,160}}?)(-?\d+(?:\.\d+)?)", clean, re.IGNORECASE)
        if m and not _DATE_TOKEN_RE.fullmatch(m.group(2)):
            return float(m.group(2))
    if preferred_keys:
        return float("nan")
    rest = _DATE_TOKEN_RE.sub(" ", _DATE_SEGMENT_RE.sub(" ", clean))
    m = re.search(r"(-?\d+(?:\.\d+)?)", rest)
    return float(m.group(1)) if m else float("nan")


# A-284: WASDE 발표일(2026) — daily_brief.WASDE_SCHEDULE와 동일 원천. 환경변수 WASDE_RELEASE_DATES(콤마 ISO)로 교정 가능.
_WASDE_RELEASE_DATES_2026 = (
    date(2026, 1, 12), date(2026, 2, 10), date(2026, 3, 10), date(2026, 4, 9), date(2026, 5, 12), date(2026, 6, 11),
    date(2026, 7, 10), date(2026, 8, 12), date(2026, 9, 11), date(2026, 10, 9), date(2026, 11, 10), date(2026, 12, 10),
)
WASDE_QUERY_WINDOW_BDAYS = 3


def _wasde_release_dates() -> tuple[date, ...]:
    raw = os.environ.get("WASDE_RELEASE_DATES", "").strip()
    if not raw:
        return _WASDE_RELEASE_DATES_2026
    out = []
    for tok in raw.split(","):
        try:
            out.append(date.fromisoformat(tok.strip()))
        except ValueError:
            print(f"[경고] WASDE_RELEASE_DATES 형식 오류 무시: {tok!r}")
    return tuple(sorted(out)) or _WASDE_RELEASE_DATES_2026


def _last_wasde_release(today: date | None = None) -> tuple[date | None, bool]:
    """(직전 발표일, 근사 여부). 표(2026)가 소진되면 관행(매월 10일경)으로 근사해 프록시가 영구 중단되지 않게 한다.
    근사값은 실제 발표일(9~12일)과 다를 수 있어 호출측이 창을 보수적으로 잡는다(교차검증 지적)."""
    t = today or date.today()
    past = [d for d in _wasde_release_dates() if d <= t]
    last = past[-1] if past else None
    if last is not None and (t - last).days <= 45:
        return last, False
    approx = date(t.year, t.month, 10)
    if approx > t:
        approx = (approx.replace(day=1) - timedelta(days=1)).replace(day=10)
    if last is None or approx > last:
        print(f"[정보] WASDE 발표일표 소진 — 관행(매월 10일경)으로 근사 {approx} · WASDE_RELEASE_DATES로 교정 가능")
        return approx, True
    return last, False


def _wasde_query_window(today: date | None = None) -> bool:
    """발표일 당일부터 3영업일 이내에만 True — 그 밖은 질의하지 않는다(카드 자동 숨김·비용 절감).
    발표일이 근사값이면 [+2, +5]영업일로 창을 늦춰 발표 전(사전 컨센서스만 있는 시점) 질의를 피한다."""
    import numpy as _np
    t = today or date.today()
    last, approx = _last_wasde_release(t)
    if last is None:
        return False
    n = int(_np.busday_count(last, t))
    return (2 <= n <= WASDE_QUERY_WINDOW_BDAYS + 2) if approx else (0 <= n <= WASDE_QUERY_WINDOW_BDAYS)


def _fetch_policy_news_proxy() -> pd.DataFrame:
    """Perplexity 실시간 검색 — 대두유 가격 주요 정책·수급 뉴스 4종.

    ARG_EXPORT_TAX_NEWS:   아르헨티나 대두유 수출세 동향
    INDIA_DUTY_NEWS:       인도 식용유 수입관세 변동
    BIODIESEL_MANDATE_NEWS: 인도네시아·말레이시아 바이오디젤 의무혼합 정책
    WASDE_CONSENSUS_SCORE: USDA WASDE 발표 전 컨센서스 및 시장 서프라이즈 스코어
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("[경고] PERPLEXITY_API_KEY 미등록 — 정책 뉴스 프록시 수집 건너뜀.")
        return pd.DataFrame()

    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    today = date.today().isoformat()

    queries: list[tuple[str, str, str, str]] = [
        (
            "ARG_EXPORT_TAX_NEWS",
            (
                "What is the current Argentina soybean oil export tax rate (retenciones)? "
                "Has there been any change or announcement in the past 30 days? "
                "Format: RATE: [percentage]% | CHANGE: [increase/decrease/unchanged] | "
                "DATE: [date of latest change or news] | SOURCE: [source name]"
            ),
            "% retenciones",
            "아르헨티나 대두유 수출세",
        ),
        (
            "INDIA_DUTY_NEWS",
            (
                "What is the current India import duty rate on refined soybean oil (HS 1507.90)? "
                "Has there been any change in the past 60 days? Include basic customs duty + AIDC + GST if available. "
                "Format: DUTY_RATE: [total %] | CHANGE: [increase/decrease/unchanged] | "
                "DATE: [latest change date] | SOURCE: [source name]"
            ),
            "% import duty",
            "인도 식용유 수입관세",
        ),
        (
            "BIODIESEL_MANDATE_NEWS",
            (
                "What are the current biodiesel blending mandates for Indonesia and Malaysia? "
                "Any policy change or announcement in the past 60 days? "
                "Format: INDONESIA: B[number]% mandate | MALAYSIA: B[number]% mandate | "
                "CHANGE: [yes/no + brief description] | DATE: [latest news date] | SOURCE: [source]"
            ),
            "B% mandate",
            "인도네시아·말레이시아 바이오디젤 의무",
        ),
        (
            "WASDE_CONSENSUS_SCORE",
            (
                # A-284(검증 4·WASDE 카드 정정): 대상을 '세계 대두유 기말재고(컨센서스 조사 부재 → unknown 반복)'에서
                #   '미국 대두유 수급표 vs 사전 애널리스트 조사(Reuters/Bloomberg 설문)'로 정정. 발표 후 3영업일에만 질의.
                f"USDA WASDE report released {(_last_wasde_release()[0].isoformat() if _last_wasde_release()[0] else 'most recently')}: "
                "compare the U.S. soybean oil balance sheet (ending stocks, million lbs; biofuel use) and U.S. soybean ending stocks "
                "(million bushels) against the pre-report analyst survey average (Reuters or Bloomberg poll). "
                "Format: REPORT_DATE: [date] | ITEM: [US soybean oil ending stocks or US soybean ending stocks] | "
                "CONSENSUS: [survey average + unit] | ACTUAL: [USDA value + unit] | "
                "SURPRISE: [bullish/bearish/neutral for soybean oil prices] | SURPRISE_SCORE: [number from -1 bearish to +1 bullish, 0 neutral] | SOURCE: [source]"
            ),
            "surprise score",
            "USDA WASDE 컨센서스",
        ),
    ]
    # A-289: 미국 바이오연료 정책·압착 — 런 #115 감사에서 8/17(NOPA)·8/21~31(SRE·RFS) 대두유 고유 변동의 원인이
    #   수집 대상에 없었음(DATA GAP) → 일별 1회 질의 추가(Perplexity 1건/일)
    queries.append((
        "US_BIOFUEL_POLICY_NEWS",
        (
            "Latest U.S. biofuel policy news affecting soybean oil in the past 3 days: EPA RFS volumes (RVO), small refinery "
            "exemptions (SRE) and reallocation, 45Z clean fuel credit guidance, D4 RIN price, and the latest NOPA monthly crush "
            "(soybean oil stocks). Format: EVENT: [one dated sentence ≤30 words or none] | D4_RIN: [$ value or unknown] | "
            "NOPA_SBO_STOCKS: [million lbs + month or unknown] | DIRECTION: [bullish/bearish/neutral for soybean oil] | DATE: [date] | SOURCE: [source]"
        ),
        "D4 RIN $",
        "미국 바이오연료 정책·압착",
    ))
    if not _wasde_query_window():
        queries = [q for q in queries if q[0] != "WASDE_CONSENSUS_SCORE"]
        print("[정보] WASDE 컨센서스 프록시 건너뜀 — 발표 후 3영업일 창 밖(다음 발표일 이후 재질의)")

    rows: list[dict] = []
    for indicator_code, prompt, unit_hint, label_kr in queries:
        try:
            r = client.chat.completions.create(
                model=PERPLEXITY_MODEL,
                messages=[{"role": "system", "content": _ONE_LINE_SYSTEM},
                          {"role": "user", "content": prompt + _ONE_LINE_SUFFIX}],
            )
            text = r.choices[0].message.content

            # A-269: 선언 키 값 우선 추출(구 코드는 본문 첫 숫자 — 'September 11'의 11을 점수로 오독)
            pref = {"ARG_EXPORT_TAX_NEWS": ("RATE",), "INDIA_DUTY_NEWS": ("DUTY_RATE", "RATE"),
                    "BIODIESEL_MANDATE_NEWS": ("INDONESIA",), "WASDE_CONSENSUS_SCORE": ("SURPRISE_SCORE", "SCORE", "ACTUAL", "CONSENSUS"),
                    "US_BIOFUEL_POLICY_NEWS": ("D4_RIN",)}
            value = _extract_value(text, pref.get(indicator_code, ()))
            _clean_txt = str(text or "").replace("**", "").replace("[", "").replace("]", "")   # _extract_value와 동일 정규화
            if indicator_code == "WASDE_CONSENSUS_SCORE" and re.search(
                    r"CONSENSUS\s*:\s*(unknown|n/?a|not available|none)", _clean_txt, re.IGNORECASE):
                value = float("nan")                          # A-284: 컨센서스 미확인이면 점수 0으로 위장하지 않음

            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/PolicyProxy",
                "indicator_code": indicator_code,
                "value":          value,
                "unit":           unit_hint,
                "note":           f"[PERPLEXITY-PROXY: {label_kr}] {text[:600]}",
            })
        except Exception as e:
            print(f"[경고] {indicator_code} 수집 실패: {e}")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


def _fetch_geopolitical_event_proxy() -> pd.DataFrame:
    """Perplexity 실시간 검색 — SBO 공급망 영향 지정학 이벤트 4종.

    SUEZ_RED_SEA_RISK:       수에즈·홍해 후티 공격·탱커 우회 위험
    UKRAINE_GRAIN_CORRIDOR:  우크라이나 흑해 곡물 회랑·해바라기유 수출 현황
    US_CHINA_TARIFF_STATUS:  미·중 관세 에스컬레이션 수준
    BRAZIL_HARVEST_PROGRESS: 브라질 대두 수확 진척률 (1~3월)
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("[경고] PERPLEXITY_API_KEY 미등록 — 지정학 이벤트 프록시 수집 건너뜀.")
        return pd.DataFrame()

    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    today = date.today().isoformat()

    queries: list[tuple[str, str, str, str]] = [
        (
            "SUEZ_RED_SEA_RISK",
            (
                "What is the current risk level for tanker shipping through the Red Sea and Suez Canal? "
                "Are Houthi attacks ongoing? How many tankers have diverted via Cape of Good Hope this week? "
                "Format: RISK: [HIGH/MEDIUM/LOW] | DIVERSIONS: [number or none] | "
                "FREIGHT_IMPACT: [% increase vs normal] | SOURCE: [source] | DATE: [date]"
            ),
            "1=Low/2=Med/3=High",
            "수에즈·홍해 탱커 위험 수준",
        ),
        (
            "UKRAINE_GRAIN_CORRIDOR",
            (
                "What is the current status of Ukraine grain and sunflower oil exports via Black Sea? "
                "Is the Black Sea Grain Initiative or equivalent agreement active? "
                "Any recent incidents blocking exports in the past 30 days? "
                "Format: STATUS: [open/restricted/blocked] | SUNFLOWER_OIL_EXPORTS: [normal/reduced/suspended] | "
                "RISK: [HIGH/MEDIUM/LOW] | SOURCE: [source] | DATE: [date]"
            ),
            "1=open/2=restricted/3=blocked",
            "우크라이나 흑해 수출 현황",
        ),
        (
            "US_CHINA_TARIFF_STATUS",
            (
                "What is the current status of US-China trade tariffs on agricultural products, "
                "specifically soybean oil and soybeans? Any tariff changes or negotiations in past 60 days? "
                "Format: TARIFF_LEVEL: [HIGH/MEDIUM/LOW escalation] | "
                "SOYBEAN_OIL_TARIFF: [China tariff % on US SBO] | "
                "CHANGE: [increase/decrease/unchanged] | SOURCE: [source] | DATE: [date]"
            ),
            "1=Low/2=Med/3=High",
            "미·중 관세 에스컬레이션 수준",
        ),
        (
            "BRAZIL_HARVEST_PROGRESS",
            (
                "What is the current Brazil soybean harvest progress for this season? "
                "Provide the percentage harvested vs same time last year if available. "
                "Any weather delays or quality issues this harvest season? "
                "Format: PROGRESS: [% harvested] | VS_LAST_YEAR: [ahead/behind/on-track by X%] | "
                "WEATHER_RISK: [HIGH/MEDIUM/LOW] | SOURCE: [source] | DATE: [date]"
            ),
            "% harvested",
            "브라질 대두 수확 진척률",
        ),
        # A-273(2026-09-25 승인자 지시): 미국–이란 분쟁·러시아–EU 관계 — 호르무즈·흑해·에너지 채널 서사
        (
            "US_IRAN_CONFLICT_STATUS",
            (
                "What is the latest status of the US-Iran conflict as it affects Strait of Hormuz tanker "
                "traffic (past 7 days)? Format: LEVEL: [HIGH/MEDIUM/LOW] | "
                "KEY_EVENT: [one dated sentence, max 25 words] | "
                "HORMUZ_IMPACT: [closure threat/attacks on tankers/transits reduced/normal] | "
                "SOURCE: [source] | DATE: [date]"
            ),
            "1=Low/2=Med/3=High",
            "미국–이란 분쟁 상태",
        ),
        (
            "RUSSIA_EU_RELATIONS_STATUS",
            (
                "What are the latest official or intelligence statements (past 48 hours, including CIA, EU "
                "or Russian officials) on Russia-EU relations, sanctions or energy? Format: "
                "TENSION: [HIGH/MEDIUM/LOW] | KEY_STATEMENT: [who said what, dated, max 25 words] | "
                "SANCTIONS_ENERGY: [new measure or none] | "
                "BLACK_SEA_IMPACT: [shipping or grain corridor effect, or none] | "
                "SOURCE: [source] | DATE: [date]"
            ),
            "1=Low/2=Med/3=High",
            "러시아–EU 관계 상태",
        ),
    ]

    rows: list[dict] = []
    for indicator_code, prompt, unit_hint, label_kr in queries:
        try:
            r = client.chat.completions.create(
                model=PERPLEXITY_MODEL,
                messages=[{"role": "system", "content": _ONE_LINE_SYSTEM},
                          {"role": "user", "content": prompt + _ONE_LINE_SUFFIX}],
            )
            text = r.choices[0].message.content

            # 위험 수준(HIGH/MEDIUM/LOW) → 숫자 인코딩 우선 시도
            level_match = re.search(r"\b(HIGH|MEDIUM|LOW)\b", text, re.IGNORECASE)

            if level_match and indicator_code in ("SUEZ_RED_SEA_RISK", "UKRAINE_GRAIN_CORRIDOR", "US_CHINA_TARIFF_STATUS",
                                                  "US_IRAN_CONFLICT_STATUS", "RUSSIA_EU_RELATIONS_STATUS"):
                level_map = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}
                value = level_map[level_match.group(1).upper()]
            elif "PROGRESS" in text and "%" in text:
                value = _extract_value(text, ("PROGRESS",))
            else:
                value = _extract_value(text, ("DIVERSIONS", "FREIGHT_IMPACT", "TARIFF_LEVEL"))

            rows.append({
                "price_date":     today,
                "source_name":    "Perplexity/GeoEventProxy",
                "indicator_code": indicator_code,
                "value":          value,
                "unit":           unit_hint,
                "note":           f"[PERPLEXITY-PROXY: {label_kr}] {text[:600]}",
            })
        except Exception as e:
            print(f"[경고] {indicator_code} 수집 실패: {e}")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


def run() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y%m%d")

    # BACKFILL_MODE=true: Perplexity 실시간 함수(오늘 날짜만 반환) 건너뜀
    # 과거 데이터 수집에는 C&I 공개 xlsx 히스토리만 사용
    backfill_mode = os.environ.get("BACKFILL_MODE", "").lower() == "true"

    if backfill_mode:
        print("[정보] BACKFILL_MODE 활성화 — Perplexity 실시간 수집 건너뜀 (역사 데이터만 수집)")
        frames = [_fetch_gpr_index()]
    else:
        frames = [
            _fetch_gpr_index(),
            _fetch_gpr_realtime(),
            _fetch_hormuz_realtime(),
            _fetch_policy_news_proxy(),
            _fetch_geopolitical_event_proxy(),
        ]

    frames = [f for f in frames if not f.empty]
    if not frames:
        print("[경고] GPR 데이터: 수집된 항목 없음")
        return

    combined = pd.concat(frames, ignore_index=True)
    out = f"{OUTPUT_DIR}/geopolitical_indices_{today}.parquet"
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="GPR")
    combined.to_parquet(out, index=False)
    print(f"[완료] 지정학 리스크 데이터 {len(combined)}건 저장 → {out}")


if __name__ == "__main__":
    run()
