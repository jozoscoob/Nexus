#!/usr/bin/env python3
"""
as-of 시점 정합성 필드 부여 — 미래 정보 누수 차단의 단일 진실원천 (D-023)

핵심 규칙(CLAUDE.md §1 · .claude/rules/modeling.md):
    모델의 t일 입력값 = available_at <= t 를 만족하는 가장 최근 값

왜 필요한가 — 누수의 실제 형태:
    WASDE 2026년 8월호는 **8월 12일에 발표**된다. 그런데 `price_date=2026-08-01`로
    저장한 뒤 일별로 forward-fill 하면, 모델은 **8월 1일부터 11일까지** 아직 세상에
    존재하지 않는 값을 보게 된다. 백테스트 성능이 부풀고 실전에서 무너진다.
    관세청 확정치·PSD 연간값·GPR 월간지수 모두 같은 함정을 가진다.

5필드 정의:
    event_time     : 측정 대상 현상이 발생한 시점(관측일). 기존 price_date와 동일한 경우가 많음
    period_end     : 집계 기간의 종료일. 월간·연간 자료에만 존재(일별은 NULL)
    release_time   : 원천이 실제로 공표한 시점
    available_at   : **우리가 최초로 사용 가능했던 시점** — 모델 필터의 기준
    source_vintage : 개정본 식별자. 덮어쓰지 않고 vintage별로 적재

available_at vs release_time:
    보통 같다. 다르는 경우 — 수집 파이프라인이 일 1회만 도는데 발표가 그 이후면
    실제 사용 가능 시점은 다음 수집분이다. 보수적으로 **늦은 쪽**을 택한다.

설계 원칙:
    ① 누수보다 지연이 안전하다 — 불확실하면 available_at을 **늦게** 잡는다.
    ② 규칙은 여기 한 곳에만 둔다 — 커넥터가 각자 추정하면 정합성이 깨진다.
    ③ 원천이 발표일을 제공하면 항상 그것을 우선한다(추정 규칙은 폴백).

사용:
    from src.pipeline.asof import attach_asof
    df = attach_asof(df, source="FRED")                     # 지표별 규칙 자동 적용
    df = attach_asof(df, source="USDA_WASDE", vintage="2026-08")

의존성: pandas
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd

# 5필드 정식 명칭 — 스키마·검증·적재가 이 목록을 공유한다
ASOF_FIELDS: list[str] = [
    "event_time", "period_end", "release_time", "available_at", "source_vintage",
]
# 모델 진입 게이트에서 NOT NULL을 강제하는 필드
ASOF_REQUIRED: list[str] = ["event_time", "available_at"]

ReleaseKind = Literal["immediate", "lag_days", "monthly_on_day", "annual_on", "explicit"]


@dataclass(frozen=True)
class ReleaseRule:
    """소스별 발표 규칙.

    kind:
      immediate      — 관측 즉시 공개(일별 시장가격). available_at = event_time (+lag_days)
      lag_days       — 관측 후 N일 뒤 공개(재분석·주간 집계)
      monthly_on_day — 대상월 종료 후 익월 `day`일 공개(월간 통계)
      annual_on      — 대상연도 종료 후 `month`월 `day`일 공개(연간 통계)
      explicit       — 원천이 발표일을 제공 → 호출부가 release_series로 전달
    """
    kind: ReleaseKind
    lag_days: int = 0
    day: int = 1
    month: int = 1
    revises: bool = False          # 개정이 발생하는가(vintage 관리 필요)
    same_month: bool = False       # ← 아래 설명 참조
    note: str = ""

    # same_month가 필요한 이유 — 월간 자료에는 서로 다른 두 의미가 섞여 있다:
    #
    #   ① 보고서-기준(report-dated): price_date = **보고서 자체의 월**
    #      예) WASDE 2026년 8월호는 **8월 12일에 발표**된다.
    #          price_date=2026-08-01 → release=2026-08-12  (같은 달)
    #
    #   ② 기간-기준(period-dated): price_date = **측정 대상 기간**
    #      예) 2026년 8월 CPI는 **9월 중순에 발표**된다.
    #          price_date=2026-08-01 → release=2026-09-13  (익월)
    #
    # 둘을 구분하지 않으면 ①에서 발표일이 한 달 밀려 **모델이 실제로 알 수 있었던 정보를
    # 못 보게 된다**(누수의 반대 방향 오류 — 성능을 부당하게 깎는다).
    # same_month=True가 ①이다.



# ── 장중 확정 시각 원리 (M-012 ③) ────────────────────────────────────────────
# G2의 예측 대상은 **CBOT ZL 일봉 종가**이며, 정규장 마감은 **14:20 ET**다.
# 어떤 지표가 그보다 **늦게 확정**되면, 같은 price_date로 join하는 순간
# "t일 종가를 예측하는 데 t일 종가보다 늦게 정해진 값"을 쓰게 된다 — 장중 누수다.
# 일 단위 as-of(available_at <= t)로는 같은 날짜끼리 통과하므로 **잡히지 않는다**.
# 따라서 마감 이후 확정 지표에는 lag_days=1을 명시해 하루 뒤부터 보이게 한다.
#
#   지표            확정 시각(ET)   ZL 마감(14:20) 대비   조치
#   VIXCLS          16:15          늦음                  lag_days=1
#   DEX* (H.10)     16:15 공표     늦음                  lag_days=1 (기적용)
#   GDELT/USGS/기타 수집 시점 의존  늦음(아래 참조)       lag_days=1
#   BDI             ~08:00         이름                  즉시 유지
#   CPO(Bursa)      ~06:00         이름                  즉시 유지
#
# 실시간 수집물(GDELT·USGS·FIRMS·NOAA 경보)이 늦은 이유: 파이프라인이 KST 05:30에 도는데
# 이는 UTC 20:30 = ET 15:30으로 **직전 거래일 마감 이후**다. 즉 `date.today()`로 찍힌
# price_date의 스냅샷은 그날 마감 뒤 정보를 포함한다.
TARGET_MARKET_CLOSE_ET = "14:20"   # CBOT ZL 정규장 마감 — 위 판정의 기준선

# ── 소스·지표별 발표 규칙 레지스트리 ─────────────────────────────────────────
# 키는 indicator_code **접두사**(긴 것 우선 매칭) 또는 source_name.
# ⚠️ 확인되지 않은 값은 보수적(늦은) 추정이며 note에 근거·검증 필요 여부를 남긴다.
RELEASE_RULES: dict[str, ReleaseRule] = {
    # ── 일별 시장가격: 관측일 장 마감 후 즉시 이용 가능 ──────────────────────
    "CBOT_BO_UTC_": ReleaseRule(
        "immediate", lag_days=1,
        note="Databento ohlcv-1d UTC 버킷 — 모델 타깃 아님. UTC 일자 종료 후 이용 가능",
    ),
    "CBOT_BO_":  ReleaseRule("immediate", note="검증된 CME 세션/정산 계열만 사용"),

    # ── TE: 거래소 정산 시각이 ZL 마감(14:20 ET)보다 늦은 계열은 1일 지연 ───────
    # M-014: `"TE_": immediate` 일괄 적용은 **에너지 계열에서 장중 누수**를 만든다.
    #   ICE Brent 정산 19:30 London(=14:30 ET) · NYMEX WTI/난방유/휘발유/천연가스 14:30 ET ·
    #   ICE EU 가스·탄소배출권은 런던 마감(=ET 오후) — 전부 ZL 마감 이후다.
    #   VIXCLS에는 같은 논리로 이미 lag_days=1을 걸어 두고(아래) TE만 빠져 있었다.
    #   에너지→바이오디젤→대두유 수요는 G1 핵심 인과체인이라 영향이 크다.
    "TE_BRENT_":     ReleaseRule("immediate", lag_days=1, note="ICE Brent 정산 14:30 ET > ZL 14:20"),
    "TE_WTI_":       ReleaseRule("immediate", lag_days=1, note="NYMEX 정산 14:30 ET"),
    "TE_HEATING_":   ReleaseRule("immediate", lag_days=1, note="NYMEX 정산 14:30 ET"),
    "TE_GASOLINE":   ReleaseRule("immediate", lag_days=1, note="NYMEX 정산 14:30 ET"),
    "TE_NATURAL_":   ReleaseRule("immediate", lag_days=1, note="NYMEX Henry Hub 정산 14:30 ET"),
    "TE_EU_NATURAL_":ReleaseRule("immediate", lag_days=1, note="ICE TTF — 런던 마감"),
    "TE_UK_NATURAL_":ReleaseRule("immediate", lag_days=1, note="ICE NBP — 런던 마감"),
    "TE_EU_CARBON_": ReleaseRule("immediate", lag_days=1, note="ICE EUA — 런던 마감"),
    "TE_ETHANOL":    ReleaseRule("immediate", lag_days=1, note="CME 에탄올 — 마감 후 정산"),
    "TE_NAPHTHA":    ReleaseRule("immediate", lag_days=1, note="유럽 평가가격 — 런던 종가 기준"),
    "TE_COAL":       ReleaseRule("immediate", lag_days=1, note="ICE Newcastle — 런던 마감"),
    "TE_CRB_":       ReleaseRule("immediate", lag_days=1, note="지수 산출이 미국 장 마감 후"),
    "TE_GSCI":       ReleaseRule("immediate", lag_days=1, note="지수 산출이 미국 장 마감 후"),
    # 아래는 ZL 마감 이전에 확정 — 지연 불필요
    #   CBOT 농산물(대두·옥수수·밀) 14:20 ET 동시 · ICE Canada 캐놀라 14:15 ET ·
    #   Bursa 팜유 06:00 ET · Baltic/Drewry 지수 런던 오전
    "TE_":       ReleaseRule("immediate", note="Trading Economics 시장 시세 — ZL 마감 이전 확정 계열"),
    "BDI":       ReleaseRule("immediate", note="Baltic Exchange 일별 발표(런던 시간)"),
    "COT_":      ReleaseRule("lag_days", lag_days=7,
                             note="CFTC COT: 화요일 기준·금 15:30 ET 공개(ZL 마감 후) — 연휴 월요일 공개 포함 보수 적용(R-043)"),
    "PW_":       ReleaseRule("lag_days", lag_days=9,
                             note="IMF PortWatch 해협 통과 척수: 주 1회 배치 갱신·4~7일 지연(실측 2026-11-19 최신 11-15) "
                                  "— 주 초 관측분이 다음 배치까지 밀리는 최악 지연 보수 적용"),
    "BCAA":      ReleaseRule("immediate"),
    "CPO":       ReleaseRule("immediate"),
    "VIXCLS":    ReleaseRule("immediate", lag_days=1,
                             note="**마감 이후 확정**: VIX 산출 종료 16:15 ET > ZL 마감 14:20 ET. "
                                  "같은 날짜로 join하면 장중 누수 → 1일 지연 필수(M-012 ③)"),

    # ── FRED 계열: 시리즈별로 지연이 다르다 ────────────────────────────────
    "DEX":       ReleaseRule("immediate", lag_days=1,
                             note="FRED 일별 환율 — 익영업일 공개. T+2 결제 규약은 별개(M-002)"),
    # A-266(2026-09-14): 승인자 업로드 15개년 환율(투자 포털 원본, BRL per USD로 역수 통일).
    #   현물 환율은 개정이 없으므로 revises=False — 개정 이력 미보존 필터(D-034)에 걸리지 않는다.
    "FX_BRL_":   ReleaseRule("immediate", lag_days=1, revises=False,
                             note="업로드 BRL/USD 일별 — 당일 확정·익영업일 공개(FRED와 동일 규약)"),
    "FEDFUNDS":  ReleaseRule("monthly_on_day", day=8,
                             note="월평균 실효연방기금금리 — H.15 익월 초 16:15 ET. "
                                  "보수적으로 익월 8일(월말+5영업일)"),
    "CPIAUCSL":  ReleaseRule("monthly_on_day", day=16, revises=True,
                             note="美 CPI — BLS는 익월 10~15일 08:30 ET 발표. 보수적으로 16일 채택. "
                                  "매년 2월 계절조정계수 재산정으로 최근 5년 소급개정 → vintage 필수"),
    "CPI_KOREA": ReleaseRule("monthly_on_day", day=10, revises=True,
                             note="통계청 소비자물가동향 — 익월 초 08:00 KST 발표 + KOSIS DB "
                                  "반영 1~2영업일 → 익월 10일. 5년 주기 기준연도 개편 시 소급 재계산"),
    "PPOILUSDM": ReleaseRule("monthly_on_day", day=15,
                             note="World Bank Pink Sheet 계열 — 익월 중순"),

    # ── 에너지 ─────────────────────────────────────────────────────────────
    "BRENT":     ReleaseRule("immediate", lag_days=1, note="EIA 일별 현물 — 익영업일 반영"),

    # ── USDA: 발표일이 명확히 정해진 대표적 케이스 ──────────────────────────
    "WASDE_":    ReleaseRule("monthly_on_day", day=12, revises=True, same_month=True,
                             note="**보고서-기준**: WASDE 8월호는 8월 9~12일경 12:00 ET 발표. "
                                  "보수적으로 12일. 다음 호에서 직전 추정치가 개정됨 → vintage 필수"),
    "PSD_":      ReleaseRule("monthly_on_day", day=12, revises=True, same_month=True,
                             note="**보고서-기준**: PS&D는 WASDE와 동시 갱신"),
    "NASS_":     ReleaseRule("annual_on", month=1, day=12, revises=True,
                             note="Crop Production Annual Summary(1월) 기준. 품목별 상이 — 검증 필요"),
    "GATS_":     ReleaseRule("monthly_on_day", day=8, revises=True,
                             note="FAS GATS 월간 무역통계 — 익월 초순. 확정치 개정 있음"),
    "ESR_":      ReleaseRule("lag_days", lag_days=7,
                             note="FAS ESR 주간 수출판매 — 대상주 다음 목요일 08:30 ET"),
    "FAOSTAT_":  ReleaseRule("annual_on", month=7, day=1, revises=True,
                             note="FAOSTAT 연간 — 이듬해 중반 공개. 보수적 추정"),

    # ── 무역통계 ───────────────────────────────────────────────────────────
    "CUSTOMS_":  ReleaseRule("monthly_on_day", day=15, revises=True,
                             note="관세청 월간 수출입 — 익월 15일경 잠정치. **확정치 개정 있음** → vintage 필수"),
    "COMTRADE_": ReleaseRule(
        "lag_days", lag_days=45,
        note="UN Comtrade — 관측 기간 종료 후 보수적으로 45일 지연. 중복 지연 금지",
    ),

    # ── 기후: 재분석 자료는 지연이 본질 ────────────────────────────────────
    "ONI":       ReleaseRule("monthly_on_day", day=10, revises=True,
                             note="NOAA CPC ONI — 익월 초 갱신. 3개월 이동평균이라 후속 개정 있음"),
    # A-266: 승인자 업로드 PSL ONI 1950~(코드 분리). 업로드본은 재산출 시 전량 재적재(vintage 단일)라
    #   revises=False — 개정 이력 미보존 필터에 걸려 분석·유사 시기에서 제외되던 결함(A-270) 회피.
    "ENSO_ONI":  ReleaseRule("monthly_on_day", day=10, revises=False,
                             note="NOAA PSL ONI 업로드본(2026-07 vintage) — 익월 10일 가용 가정"),
    "temperature_2m":  ReleaseRule("lag_days", lag_days=6,
                                   note="ERA5-Land 재분석 — 통상 5일 지연. 보수적 6일"),
    "precipitation_":  ReleaseRule("lag_days", lag_days=6, note="동일(ERA5-Land)"),
    "soil_":           ReleaseRule("lag_days", lag_days=6, note="동일(ERA5-Land)"),
    "shortwave_":      ReleaseRule("lag_days", lag_days=6, note="동일(ERA5-Land)"),
    "et0_":            ReleaseRule("lag_days", lag_days=6, note="동일(ERA5-Land)"),
    "sunshine_":       ReleaseRule("lag_days", lag_days=6, note="동일(ERA5-Land)"),
    "NASA_POWER_":     ReleaseRule("lag_days", lag_days=7,
                                   note="NASA POWER — 위성 처리 지연 약 1주"),
    "USDM_":           ReleaseRule("lag_days", lag_days=5,
                                   note="US Drought Monitor — 화요일 관측, 목요일 08:30 ET 공개"),
    # 2026-09-13: 산지 예보 층(Open-Meteo forecast, FCST_{var}_{region}). event_time=유효일(미래)
    "FCST_":           ReleaseRule("immediate", lag_days=0, revises=True,
                                   note="예보 — 발행 주기마다 동일 유효일 재예보; "
                                        "available_at=수집 시각(A-195 분기), vintage=발행일"),

    # ── 지정학 ─────────────────────────────────────────────────────────────
    "GPR":       ReleaseRule("monthly_on_day", day=5, revises=True,
                             note="Caldara & Iacoviello 월간 지수 — 익월 초 갱신"),
    "GDELT_":    ReleaseRule("immediate", lag_days=1,
                             note="15분 단위 갱신이나 수집이 KST 05:30(=ET 15:30, 마감 후)이라 "
                                  "당일 스냅샷에 마감 뒤 정보가 섞인다 → 1일 지연"),
    "SEISMIC_":  ReleaseRule("immediate", lag_days=1,
                             note="USGS 실시간 — GDELT와 동일 사유(마감 후 수집) → 1일 지연"),
    "GEOINTEL_": ReleaseRule("immediate", lag_days=1,
                             note="복합 위험 지수(USGS·NOAA·GDELT·FIRMS 합성) — 구성 요소가 "
                                  "마감 후 수집분을 포함 → 1일 지연"),
    "FIRMS_":    ReleaseRule("immediate", lag_days=1, note="NASA FIRMS — 동일 사유"),

    # ── 비정형 파생: 문서 발행일이 곧 이용 가능 시점 ────────────────────────
    "UNSTR_":    ReleaseRule("monthly_on_day", day=20,
                             note="GAIN·FAO 월간 문서를 집계한 파생 지표. 해당 월 문서가 모두 "
                                  "나온 뒤라야 월 집계가 확정되므로 보수적으로 익월 20일"),

    # ── 시장 유동성 ────────────────────────────────────────────────────────
    "ICE_":      ReleaseRule("monthly_on_day", day=5,
                             note="ICE 월별 거래량 리포트 — 익월 초"),
}

# 원천이 발표일을 직접 제공하는 소스(그 필드를 우선 사용)
EXPLICIT_RELEASE_SOURCES: set[str] = {"USDA_WASDE_XLSX", "USDA_FAS_GAIN_PDF", "FAO_AMIS_PDF"}

_DEFAULT_RULE = ReleaseRule(
    "lag_days", lag_days=1,
    note="규칙 미등록 — 보수적 1일 지연 적용. RELEASE_RULES 등재 필요")


# ── 개정 이력 보유 여부 (D-034) ──────────────────────────────────────────────
# `revises=True`는 "그 소스가 값을 고친다"는 사실이고, 아래는 "**우리가 그 이력을
# 갖고 있는가**"라는 별개의 질문이다. 둘을 구분하지 않으면 백테스트가 조용히
# 개정 후 확정치를 과거에 사용한다.
#
#   full — 발표 회차마다 별도 행이 쌓여 available_at이 곧 vintage 역할을 한다.
#          예) WASDE: 매월 보고서가 같은 마케팅연도를 다시 싣고, 우리는 그 회차별
#              행을 모두 보관한다(2010-04~2026-07). 반면 PSD는 같은 성격의 소스인데도
#              **최신 스냅샷만** 내려받아 왔으므로 none이다 — 소스가 아니라 수집 방식의 문제.
#   none — 최신 스냅샷 하나만 있다. 과거 시점의 값을 복원할 수 없다.
#          → 해당 피처는 **개정 오염(revision-contaminated)** 상태이며,
#            모델 성능이 실전에서 재현되지 않을 수 있다. 반드시 표기하고
#            민감도 검증(해당 피처 제외 비교)을 함께 보고한다.
REVISION_HISTORY: dict[str, str] = {
    "WASDE_":    "full",   # 월간 보고서별 행 보유 확인(2010-04~2026-07, 193회차)
    "PSD_":      "none",   # 마케팅연도당 1행 — 개정 전 값 없음
    "GATS_":     "none",   # 월별 최종치만 — 잠정→확정 이력 없음
    "CUSTOMS_":  "none",   # 관세청 잠정→확정 개정 이력 없음
    "CPIAUCSL":  "none",   # FRED ALFRED 사용 시 full로 승격 가능
    "CPI_KOREA": "none",
    "ONI":       "none",   # NOAA CPC는 3개월 이동평균 후속 개정
    "GPR":       "none",
    "NASS_":     "none",
    "FAOSTAT_":  "none",
    "COMTRADE_": "none",
    "FCST_":     "full",   # 발행 회차별 행 보존(같은 유효일이 매일 재예보) — 2026-09-13
}


def revision_status(indicator_code: str) -> str:
    """개정 이력 보유 상태 — 'full' · 'none' · 'n/a'(개정 없는 소스)."""
    rule = rule_for(indicator_code)
    if not rule.revises:
        return "n/a"
    for key in sorted(REVISION_HISTORY, key=len, reverse=True):
        if indicator_code.startswith(key):
            return REVISION_HISTORY[key]
    return "none"


def rule_for(indicator_code: str, source_name: str = "") -> ReleaseRule:
    """지표코드(우선) → 소스명 순으로 가장 긴 접두사 규칙을 찾는다."""
    for key in sorted(RELEASE_RULES, key=len, reverse=True):
        if indicator_code.startswith(key) or (source_name and source_name.startswith(key)):
            return RELEASE_RULES[key]
    return _DEFAULT_RULE


def _release_for(ev: pd.Timestamp, rule: ReleaseRule) -> pd.Timestamp:
    """단일 관측의 발표 시점 산출."""
    if pd.isna(ev):
        return pd.NaT
    if rule.kind == "immediate":
        return ev + pd.Timedelta(days=rule.lag_days)
    if rule.kind == "lag_days":
        return ev + pd.Timedelta(days=rule.lag_days)
    if rule.kind == "monthly_on_day":
        if rule.same_month:
            # 보고서-기준: 그 달 `day`일에 발표 (WASDE 8월호 → 8/12)
            base = ev.normalize().replace(day=1)
        else:
            # 기간-기준: 대상월 종료 후 익월 `day`일 발표 (8월 CPI → 9/13)
            base = (ev + pd.offsets.MonthBegin(1)).normalize()
        rel = base + pd.Timedelta(days=min(rule.day, 28) - 1)
        return rel + pd.Timedelta(days=rule.lag_days)
    if rule.kind == "annual_on":
        # 대상연도 종료 후 이듬해 `month`월 `day`일
        return pd.Timestamp(year=ev.year + 1, month=rule.month,
                            day=min(rule.day, 28)) + pd.Timedelta(days=rule.lag_days)
    return ev  # explicit — 호출부가 덮어씀


def _period_end_for(ev: pd.Timestamp, rule: ReleaseRule) -> pd.Timestamp:
    """집계 기간 종료일. 일별 자료는 NaT."""
    if pd.isna(ev):
        return pd.NaT
    if rule.kind == "monthly_on_day":
        return (ev + pd.offsets.MonthEnd(0)).normalize()
    if rule.kind == "annual_on":
        return pd.Timestamp(year=ev.year, month=12, day=31)
    return pd.NaT


def attach_asof(
    df: pd.DataFrame,
    source: str = "",
    *,
    event_col: str = "price_date",
    release_series: pd.Series | None = None,
    vintage: str | None = None,
    ingest_lag_days: int = 0,
) -> pd.DataFrame:
    """DataFrame에 as-of 5필드를 부여한다.

    Args:
        df: `event_col`과 `indicator_code`를 가진 롱포맷 프레임
        source: source_name (규칙 매칭 보조)
        event_col: 관측 시점 컬럼(기본 price_date — **보존되며 삭제하지 않음**)
        release_series: 원천이 발표일을 제공할 때 그 시리즈(최우선 적용)
        vintage: 개정본 식별자. 미지정 시 개정 소스는 수집일(YYYY-MM-DD)로 대체
        ingest_lag_days: 수집 파이프라인 지연(발표를 그날 못 받는 경우)

    Returns:
        5필드가 추가된 사본. 원본은 변경하지 않는다.
    """
    if df is None or df.empty:
        return df
    out = df.copy()
    if event_col not in out.columns:
        raise ValueError(f"[오류] as-of 부여 실패: '{event_col}' 컬럼 없음 "
                         f"(보유 컬럼: {list(out.columns)[:8]})")

    ev = pd.to_datetime(out[event_col], errors="coerce")
    if hasattr(ev.dtype, "tz") and ev.dt.tz is not None:
        ev = ev.dt.tz_localize(None)
    out["event_time"] = ev

    codes = out.get("indicator_code", pd.Series([""] * len(out), index=out.index)).astype(str)
    src = str(source or "")

    # 지표코드가 소수 종류뿐이므로 코드 단위로 규칙을 한 번만 조회한다(행별 조회는 낭비)
    rules = {c: rule_for(c, src) for c in codes.unique()}

    out["period_end"] = [
        _period_end_for(e, rules[c]) for e, c in zip(ev, codes)
    ]
    # 우선순위: ①명시 전달 release_series ②**원천이 이미 제공한 release_time**(FRED ALFRED
    # 등 실측 게시일 — 추정 규칙보다 항상 우선) ③접두사 규칙 추정
    estimated = pd.Series([_release_for(e, rules[c]) for e, c in zip(ev, codes)], index=out.index)
    if release_series is not None:
        rel = pd.to_datetime(release_series, errors="coerce")
        if hasattr(rel.dtype, "tz") and rel.dt.tz is not None:
            rel = rel.dt.tz_localize(None)
        out["release_time"] = pd.Series(rel.values, index=out.index).fillna(estimated)
    elif "release_time" in df.columns:
        existing = pd.to_datetime(out["release_time"], errors="coerce")
        if hasattr(existing.dtype, "tz") and existing.dt.tz is not None:
            existing = existing.dt.tz_localize(None)
        n_kept = int(existing.notna().sum())
        if n_kept:
            print(f"[as-of] 원천 제공 발표일 {n_kept:,}건 보존(추정 규칙 미적용)")
        out["release_time"] = existing.fillna(estimated)
    else:
        out["release_time"] = estimated

    # available_at = release_time + 수집 지연. 누수 방지를 위해 event_time보다 이르지 않게 강제
    avail = pd.to_datetime(out["release_time"]) + pd.Timedelta(days=ingest_lag_days)
    avail = avail.where(avail >= out["event_time"], out["event_time"])   # 관측형 floor 유지
    # A-195: 미래 기간 라벨(마케팅연도 **전망** 행: event_time > ingested_at)은 규칙이
    # 기간에서 발표일을 앞으로 파생해 **미래 available_at**을 만든다(pytest 게이트 871건의
    # 원인). 이미 보유한 데이터의 available_at은 수집 시점보다 늦을 수 없다 — 전망 행만
    # ingested_at으로 캡한다. 조건부이므로 일별 관측 행(VIXCLS 등 lag_days=1 장중누수
    # 방지 — M-012③)은 절대 건드리지 않는다.
    if "ingested_at" in out.columns:
        # A-263: leak_inversions()와 동일하게 UTC로 정규화한 뒤 tz를 뗀다. 구 코드는 utc=True 없이
        #   파싱해 오프셋 문자열(예: +09:00)이 저장된 ingested_at을 벽시계 그대로 읽어 캡 기준이
        #   최대 9시간 어긋날 수 있었다(현재 커넥터는 전부 UTC라 실해는 없었음 — 예방 정합).
        ing = pd.to_datetime(out["ingested_at"], utc=True, errors="coerce").dt.tz_localize(None)
        forecast = ing.notna() & (out["event_time"] > ing)
        avail = avail.mask(forecast, ing)          # 타임스탬프 그대로(normalize 금지)
        # A-242: 관측 행(전망 아님)에서도 규칙 추정 발표일이 수집 시점을 1일 초과해
        # 미래이면 추정 오류다 — API가 값을 반환했다는 것 자체가 이미 공표됐다는 뜻
        # (ESR '최근 주' 행: 기준일+7일 추정이 실제 발표 이후에도 미래를 가리킴 —
        # 런 #84 pytest 4건의 원인). ingested_at으로 캡한다. 1일 여유는 장중 확정
        # 시각 설계(lag_days=1 — M-012③·M-013)를 보존하기 위한 것으로, VIXCLS류의
        # 의도된 +1일 지연은 절대 건드리지 않는다.
        # A-254: 허용폭을 고정 +1일이 아니라 **규칙의 설계 지연**으로 — immediate+lag_days≥1
        #        (VIXCLS·TE 에너지·GeoIntel, M-013 장중 확정 시각)만 +1일을 보존하고, 발표
        #        지연 '추정'(lag_days 종류: ESR·ERA5·USDM)은 수집 시점으로 캡한다. 고정 +1일은
        #        오전 발사 런(05:52 UTC)에서 ESR 행을 '내일' 날짜로 남겨 품질 테스트를 깨뜨렸다.
        allow = pd.Series(
            [pd.Timedelta(days=1) if (rules[c].kind == "immediate" and rules[c].lag_days >= 1)
             else pd.Timedelta(0) for c in codes], index=out.index)
        overshoot = ing.notna() & ~forecast & (avail > ing + allow)
        avail = avail.mask(overshoot, ing)
    out["available_at"] = avail

    # ── vintage: "모른다"를 "안다"로 위장하지 않는다 (D-034) ────────────────────
    # 구 코드는 개정 소스에 **수집일을 일괄 스탬프**했다. 그 결과 2010년 WASDE 값도
    # source_vintage=2026-08-12가 되어, 파일 전체의 vintage 고유값이 **1개**뿐이었다.
    # 그러면 "available_at ≤ t 중 최신 vintage" 규칙은 고를 대상이 없어 항상 **개정 후
    # 확정치**를 과거에 쓰게 된다. 더 나쁜 것은 validate_asof의 non-null 검사를
    # 100% 통과해 **게이트가 아무것도 막지 못한다**는 점이다.
    #   → 원천이 vintage를 주지 않으면 NULL로 두고, 안다/모른다를 별도 컬럼으로 남긴다.
    #     (WASDE처럼 발표회차마다 행이 쌓이는 소스는 available_at 자체가 vintage 역할을 한다.)
    if vintage is not None:
        out["source_vintage"] = str(vintage)
        out["vintage_known"] = True
    elif "source_vintage" in df.columns and out["source_vintage"].notna().any():
        out["vintage_known"] = out["source_vintage"].notna()   # 원천 제공분(ALFRED 등)
    else:
        out["source_vintage"] = None
        out["vintage_known"] = False

    return out


def drop_future_observations(df: pd.DataFrame, label: str,
                             today: date | None = None) -> pd.DataFrame:
    """관측(observation) 계열에서 price_date > 수집일 행을 제거하고 지표별 건수를 로그로 남긴다.

    A-246(런 #88~#93 pytest 실측): shipping_indices·commodity_data에 미래 price_date가
    19→21건으로 **날마다 늘어남** — 진짜 미래 일자라면 줄어야 하므로 수집일 기준 전방 창을
    매일 생성하는 원천이 섞여 있다는 뜻. BDI·CPO·환율·가뭄은 전부 관측값이라 미래 일자는
    정의상 존재할 수 없으니 저장 전에 잘라내고, 어느 지표에서 나왔는지 로그로 드러내
    다음 런에서 원천을 확정한다(전망 행은 관측 계열에 섞지 않음 — D-023 원칙).
    """
    if df.empty or "price_date" not in df.columns:
        return df
    cutoff = pd.Timestamp(today or date.today())
    df = df.reset_index(drop=True)          # concat 잔여 중복 인덱스 방어
    pdates = pd.to_datetime(df["price_date"], errors="coerce")
    future = (pdates > cutoff).fillna(False)
    n = int(future.sum())
    if n:
        codes = df["indicator_code"] if "indicator_code" in df.columns else pd.Series("?", index=df.index)
        by_code = codes[future].value_counts()
        detail = " · ".join(f"{k} {v}건" for k, v in by_code.head(8).items())
        print(f"[경고] {label}: 수집일({cutoff.date()}) 이후 price_date {n}건 제거 — {detail}")
    return df.loc[~future].reset_index(drop=True)


def leak_inversions(df: pd.DataFrame) -> "pd.Series":
    """누수 의심 역전(available_at < event_time) 행 마스크 — 게이트 공용 판정 (A-195).

    **전망 라벨 행은 예외**: 마케팅연도 전망(event_time > ingested_at)은 기간보다
    발표가 앞서는 것이 정상이므로 역전이 누수가 아니다. 이 판정을 게이트 3곳
    (validate_asof · missing_asof · data_readiness)이 공유한다 — 복제 금지(A-103 교훈).
    """
    ev = pd.to_datetime(df["event_time"], errors="coerce")
    if hasattr(ev.dtype, "tz") and ev.dt.tz is not None:
        ev = ev.dt.tz_localize(None)
    av = pd.to_datetime(df["available_at"], errors="coerce")
    if hasattr(av.dtype, "tz") and av.dt.tz is not None:
        av = av.dt.tz_localize(None)
    inv = av < ev
    if "ingested_at" in df.columns:
        ing = pd.to_datetime(df["ingested_at"], utc=True, errors="coerce").dt.tz_localize(None)
        inv &= ~(ev > ing)   # 전망 라벨: 역전이 정상 — 누수 판정에서 제외
    return inv.fillna(False)


def missing_asof(df: pd.DataFrame) -> list[str]:
    """모델 게이트 위반 항목을 반환한다(빈 리스트 = 통과)."""
    problems: list[str] = []
    for f in ASOF_REQUIRED:
        if f not in df.columns:
            problems.append(f"필수 필드 없음: {f}")
        elif df[f].isna().any():
            problems.append(f"{f} 결측 {int(df[f].isna().sum()):,}건")
    if {"available_at", "event_time"} <= set(df.columns):
        inverted = int(leak_inversions(df).sum())
        if inverted:
            problems.append(f"available_at < event_time 역전 {int(inverted):,}건")
    return problems
