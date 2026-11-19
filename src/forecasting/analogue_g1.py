"""G1 과거 유사국면 참조 — Stage 1: 단변량 분위 슬라이스 (D-051 · W1).

조정자 재정립(2026-08-28): G1의 본질 = "특정 변수 기준으로 과거 연도들의 수급/가격이
어떻게 변했는지 분석해 유사 상황의 참조로 제공". 본 모듈은 그 계산 전담층이다.

원리 — 누수 없는 조건부 과거 실측 분포:
  mart(2010~)의 `{X}__z90`(후방참조 z)이 현재와 같은 분위 버킷이었던 과거 거래일을
  찾고, 그 날들의 `target_ret{h}`(mart가 이미 보유한 미래 h거래일 실측 수익률)를
  집계한다. 유사일 검색은 과거만 보고, 전방 수익률은 mart 빌더의 유일한 전방참조
  컬럼을 그대로 쓰므로 새 누수 경로가 없다.

규율 (계획 승인분):
  - A-191: 산출은 "과거 관측의 요약"까지 — 전망·확률 주장 금지(서술 계약 문자열 검증)
  - 직전 EXCLUDE_RECENT_TRADING_DAYS 거래일은 이웃 후보 제외(전방 창 겹침 누수 가드)
  - 에피소드화(유사일 간 최소 간격 = horizon) 후 MIN_ANALOGUE_EPISODES 미만이면
    "표본 부족 — 산출 보류" 정직 강등. 완화는 십분위→오분위 사전 등록 1단만(표기 의무)
  - 수익률 집계는 원시값(IQR 캡은 z 경로 전용 — D6)
  - Stage 1은 통계 검정을 하지 않는다(기술 서술만 — 다중검정 문제 원천 차단)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

ANALOGUE_HORIZONS: tuple[int, ...] = (5, 20, 60)   # ≈1주 · 1개월 · 3개월 (거래일)
ANALOGUE_QUANTILE_BINS = 10                        # Stage 1 십분위
RELAX_BINS = 5                                     # 사전 등록 완화 사다리 1단(오분위)
MIN_ANALOGUE_EPISODES = 8
EXCLUDE_RECENT_TRADING_DAYS = 60                   # 전방 창 겹침 누수 가드
MAX_ANALOGUE_VARS = 3                              # 브리프 렌더 상한(경보 우선)

# 위기 사례 프로파일 — docs/research_desk/_reference/soybean_oil_historical_crisis_analysis.md
# (수치는 corrections 문서 병독 전제 — 배지는 정성 연결일 뿐 처치 정의가 아님)
# 서사 계약(A-191): 과거 사실 기술 + 구조 비교까지만 — 방향 주장·전망 문구 금지.
@dataclass(frozen=True)
class CaseProfile:
    start: str
    end: str
    trigger: str        # 원인 사건(과거 사실)
    channel: str        # 전달 경로(수급·물류·정책)
    price_fact: str     # 가격 반응 실측
    similarity: str     # 현재 국면과의 구조 유사점
    difference: str     # 현재 국면과의 구조 차이점
    # A-284(검증 3): 사례와 인과적으로 연결되는 변수 접두 — 배지는 날짜 농축 AND 변수 관련성일 때만.
    #   빈 튜플은 '연결 근거 미등재'(어떤 변수에도 배지를 주지 않음 — 정직 강등).
    related: tuple[str, ...] = ()


def case_related_to(name: str, var_code: str) -> bool:
    """변수 코드가 사례의 관련 변수(접두·정확 일치)에 속하는가 — 인과 필터(검증 3)."""
    p = CASE_PROFILES.get(name)
    if p is None or not p.related:
        return False
    up = str(var_code).upper().split("__")[0]
    if up.startswith("FEAT_"):
        up = up[5:]
    for r in p.related:
        k = r.upper()
        if up == k or up.startswith(k + "_") or up.startswith(k) and k.endswith("_") or f"_{k}_" in f"_{up}_":
            return True
    return False


CASE_PROFILES: dict[str, CaseProfile] = {
    "사례 ① · 2010-11 라니냐·러 수출금지": CaseProfile(
        "2010-06-01", "2011-09-30",
        "라니냐 최고조(ONI −1.4)로 남미 작황 취약성이 누적된 상태에서, 러시아가 폭염·"
        "가뭄으로 밀 수출을 금지함(2010-08).",
        "곡물 전반 급등 → 유지류로 대체 수요 집중 → 대두유 수급 압박.",
        "저점 38.0 → 고점 57.4 센트/파운드, 약 9개월 +51% 실측. ONI 전환이 가격에 "
        "2~3개월 선행함.",
        "기후 취약성이 깔린 상태에서 단일 정책 이벤트가 추가 충격으로 얹히는 중첩 구조.",
        "당시 파급은 곡물發 대체 수요 경로였고, 물류(운임·해협) 요인의 비중은 크지 않았음.",
        related=('ENSO', 'ONI', 'TE_WHEAT', 'TE_CORN', 'TE_SOYBEANS', 'WASDE', 'PSD', 'TE_SUNFLOWER_OIL', 'UKRAINE', 'RUSSIA', 'TE_BDI', 'BDI')),
    "사례 ② · 2012 미국 대가뭄": CaseProfile(
        "2012-05-01", "2013-08-31",
        "미국 중서부 대가뭄(예외적 가뭄 등급 면적 35%) — 7월 WASDE가 미국 대두 생산 "
        "전망을 −14.4% 하향함.",
        "생산 전망 하향 → 공급 우려 선반영 → 실제 수확 발표(우려 대비 양호)로 급반전.",
        "8개월 +13.6% 뒤 9월 한 달 만에 되돌림 실측 — 단일 공급 충격의 가역성 사례.",
        "발표 이벤트(WASDE) 전후로 가격이 빠르게 재평가되는 패턴.",
        "당시는 운임(BDI) 저수준·수입 수요 부진의 삼중 부정 구조 — 고점이 지속되지 "
        "못한 조건이 겹쳐 있었음.",
        related=('ENSO', 'ONI', 'T2M', 'PRECTOTCORR', 'PRECIPITATION', 'GWET', 'GWETROOT', 'GWETTOP', 'SOIL_', 'USDM', 'DROUGHT', 'CROP_CONDITION', 'SOYBEAN_PROD', 'WASDE', 'PSD_SOY', 'WASDE_CONSENSUS', 'FCST_')),
    "사례 ③ · 2021-22 복합 위기": CaseProfile(
        "2020-08-01", "2022-06-30",
        "2년 연속 라니냐(아르헨 감산) + 러시아-우크라이나 전쟁(해바라기유 공급 45~50% "
        "붕괴) + 인도네시아 팜유 수출 금지 + 인도 수입 관세 인하.",
        "기후·지정학·정책 3중 충격이 동시 발생 — 대체 수요 집중에 물류 차질(운임 지수 "
        "+387%)이 도착 원가를 증폭함. COVID기 항만·항로 봉쇄로 선박이 우회하며 운임·"
        "보험료가 도착가에 얹히는 경로가 형성됨.",
        "저점 28.9 → 고점 82.5 센트/파운드, 23개월 +185% 실측(당시 사상 최고가). 운임 급등이 "
        "가격 고점에 6~18개월 선행함.",
        "'요충 경로 불안 → 우회·보험료 → 도착가 상방'의 물류 증폭 구조가 현재 호르무즈 "
        "국면과 동형임(당시는 COVID·흑해發 경로 차질).",
        "당시는 수요 측 충격(바이오디젤·인도 수입)이 동반됨 — 재평가 기록에서 "
        "유사도 7/10로 하향(우크라이나 요인 제외), 2024-25 미·중 관세 사례가 "
        "9/10로 더 유사 판정.",
        related=('TE_BDI', 'BDI', 'BDI_ZSCORE', 'GPR', 'HORMUZ', 'SUEZ', 'AIS_', 'BCAA', 'BCTI', 'TE_BRENT_CRUDE_OIL', 'TE_WTI_CRUDE_OIL', 'TE_HEATING_OIL', 'TE_GASOLINE', 'TE_NATURAL_GAS', 'INDIA', 'BIODIESEL', 'UKRAINE', 'TE_SUNFLOWER_OIL', 'TE_PALM_OIL', 'CPO', 'US_IRAN', 'RUSSIA_EU', 'GEOINTEL', 'SBO_STRAIT', 'VIXCLS')),
    "사례 ④ · 2022-23 아르헨 가뭄": CaseProfile(
        "2022-12-01", "2023-04-30",
        "3년 연속 라니냐로 아르헨티나 대두 생산 −42%(4,340만→2,500만 톤), "
        "로사리오 압착 허브 가동률 45%로 급락.",
        "단일 원산지 공급 급감 — 그러나 브라질 기록 풍작(1억 5,300만 톤)이 물량을 완전 상쇄함.",
        "+11.4% 상승에 그친 뒤 되돌림 실측 — 대체 공급국의 완충 여부가 "
        "충격 크기를 결정함.",
        "주요 원산지 한 곳의 충격이 발생해도 대체 원산지 물량이 완충하는 구조 — 현재도 "
        "브라질 생산이 역대 최고 수준이라는 점이 같은 완충 요인임.",
        "당시는 기후 단일 요인 — 물류·정책 충격이 결합하지 않았음.",
        related=('ENSO', 'ONI', 'ARG', 'ARS_USD', 'DEXBZUS', 'FX_BRL', 'PSD_SOY', 'PSD_', 'SOYBEAN_PROD', 'WASDE_SBO', 'T2M', 'PRECTOTCORR', 'GWET', 'GWETROOT', 'GWETTOP', 'KCS', 'CROP_CONDITION')),
    # R-046(2026-11-19 승인): 2018 사례 2건 — 원곡 수치는 대두유 반응으로 옮기지 않음(서사 계약 A-191)
    "사례 ⑤ · 2018 미·중 관세": CaseProfile(
        "2018-04-01", "2019-01-31",
        "중국이 미국산 대두에 25% 보복관세를 발표(2018-04)하고 시행(2018-07-06)함 — 중국 대두 "
        "수입에서 미국산 비중이 18.9%로 사상 최저(2018, Wang 외 2023 p.12).",
        "미국 원곡 수출 재배치(총수출 −16.2%, 대중 −72.7%, Liu 외 2025 p.16) → 남미산 원곡 "
        "프리미엄 확대. 대두유(HS1507)의 관세 포함 여부는 미확인(DATA GAP).",
        "CBOT 대두유 정산가 32.04(2018-04-02) → 저점 26.96(2018-11-26) 센트/파운드, 저점까지 "
        "−15.9%·창 전체 −5.8% 실측.",
        "정책 충격이 원곡 무역 흐름을 재배치하고 대두유는 간접 경로로 반응하는 구조 — "
        "2024-25 미·중 관세 국면과 동형.",
        "당시 무역 수치는 원곡(대두) 기준이라 대두유 반응으로 직접 옮길 수 없음 — 바이오연료 "
        "수요 비중이 지금보다 작았음.",
        related=('US_CN', 'US_CHINA', 'TARIFF', 'ESR', 'GATS', 'TE_SOYBEANS', 'PSD_SOY', 'DEXCHUS', 'FX_CNY')),
    "사례 ⑥ · 2018 브라질 트럭 파업": CaseProfile(
        "2018-05-21", "2018-06-15",
        "브라질 화물차 운전자 파업(2018-05-21~05-31) — 운임표 분쟁으로 내륙 운송이 마비되어 "
        "대두 수출 흐름이 크게 지연됨(Cordeiro Junior 외 2025 p.11).",
        "내륙 물류 차질 → 항만 선적 지연 → 수입국의 브라질 공급 신뢰 저하(기상이 아닌 공급 충격).",
        "CBOT 대두유 정산가 31.12(2018-05-14) → 고점 31.71(2018-05-24) → 29.50(2018-06-15) "
        "센트/파운드 — 창 전체 −5.2% 실측(같은 시기 미·중 관세 긴장이 겹침).",
        "기상이 아닌 물류 요인으로 브라질 공급이 일시 차질을 빚는 구조.",
        "충격 기간이 약 10일로 짧고 해상이 아닌 브라질 내륙 문제였음 — 같은 시기 관세 "
        "이슈와 효과를 분리할 수 없음.",
        related=('DEXBZUS', 'FX_BRL', 'LOGISTICS_DISRUPTION', 'BRAZIL_HARVEST')),
}

# 하위 호환: 창(window)만 쓰는 기존 경로용 파생 뷰
CASE_WINDOWS: dict[str, tuple[str, str]] = {
    name: (p.start, p.end) for name, p in CASE_PROFILES.items()
}


def case_narrative_lines(name: str) -> list[str]:
    """사례 배지 → 메커니즘 서사(원인→경로→가격 실측→유사점/차이점). 미등재 시 빈 목록."""
    p = CASE_PROFILES.get(name)
    if p is None:
        return []
    return [f"원인 사건: {p.trigger}",
            f"전달 경로: {p.channel}",
            f"가격 반응(실측): {p.price_fact}",
            f"현재와의 유사점: {p.similarity}",
            f"현재와의 차이점: {p.difference}"]

# 경보 변수 코드 → mart 파생 z-컬럼 후보 (경보 코드는 mart 컬럼명과 다른 별칭 체계)
_ALERT_Z_ALIASES: dict[str, list[str]] = {
    "BDI_ZSCORE": ["TE_BDI__z90", "BDI__z90"],
    "GPR_NORMALIZED": ["GPR__z90", "GPR_NORMALIZED__z90", "GPR__z252"],
    "ENSO_ONI": ["ONI__z252", "ONI__z90", "ENSO_ONI__z252"],
    "CPO_SBO_SPREAD": ["TE_PALM_OIL__z90", "CPO_SBO_SPREAD__z90"],
    "WASDE_STU": ["WASDE_SBO_STU__z252", "WASDE_SBO_STU__z90"],
}

_REQUIRED_CAPTION = "과거 관측의 요약이며 향후 전망·확률 주장이 아님"
_FORBIDDEN_WORDS = ("예상", "전망 확률", "매수 유리", "대기 유리", "상승할 것", "하락할 것")


@dataclass
class AnalogueResult:
    var_code: str                     # 기반 변수 코드(표시용)
    z_col: str                        # 실제 사용한 mart 컬럼
    current_z: float
    method: str                       # "quantile_slice"
    horizon: int
    n_days: int
    n_episodes: int
    n_up: int
    n_down: int
    ret_p10: float                    # % (원시 로그수익률 → 백분율 변환)
    ret_p50: float
    ret_p90: float
    years: list[int] = field(default_factory=list)
    case_badges: list[str] = field(default_factory=list)
    relax_step: int = 0               # 0=십분위 · 1=오분위(완화 사용 표기)
    guard_note: str = ""              # ""=정상 · 그 외 = 산출 보류 사유
    date_only_badges: list[str] = field(default_factory=list)   # A-284: 날짜만 겹친 사례(연결 근거 없음)


def _resolve_z_column(columns: pd.Index, code: str) -> str | None:
    """변수 코드 → mart z-컬럼 해석. 실패 시 None(정직 강등)."""
    base = code.split("__")[0]
    candidates = [f"{base}__z90", f"{base}__z252"]
    candidates = _ALERT_Z_ALIASES.get(code, []) + _ALERT_Z_ALIASES.get(base, []) + candidates
    for c in candidates:
        if c in columns:
            return c
    # 마지막 수단: 코드 부분일치 z-컬럼(유일할 때만 — 오매칭 방지)
    hits = [c for c in columns if c.startswith(base) and ("__z" in c)]
    return hits[0] if len(hits) == 1 else None


def find_analogue_days_quantile(
    z_series: pd.Series, bins: int = ANALOGUE_QUANTILE_BINS,
    exclude_recent: int = EXCLUDE_RECENT_TRADING_DAYS,
    current: float | None = None,
) -> tuple[pd.DatetimeIndex, float]:
    """현재 z와 동일 분위 버킷의 과거 거래일 반환 (직전 exclude_recent 거래일 제외).

    A-284: `current`를 주면 그 값을 현재 편차로 쓴다 — 분석창(2025-12 종료) 마지막 행이 아니라
    **원시 계열의 오늘 기준** 편차로 버킷을 고른다(표시·버킷 선택의 시점 분리 해소). 미지정은 종전 동작.
    """
    z = z_series.dropna()
    if len(z) < bins * 3:
        return pd.DatetimeIndex([]), float("nan")
    current = float(z.iloc[-1]) if (current is None or current != current) else float(current)
    # 버킷 경계는 전체 관측 분포 기준(현재 포함 — 순위 판정일 뿐 전방 정보 아님)
    edges = np.quantile(z.values, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    cur_bin = int(np.searchsorted(edges, current, side="right")) - 1
    in_bin = z[(z >= edges[cur_bin]) & (z < edges[cur_bin + 1])]
    # 전방 창 겹침 가드: 최근 exclude_recent 거래일(z 관측 기준) 제외
    cutoff_pos = max(0, len(z) - exclude_recent)
    allowed = z.index[:cutoff_pos]
    days = in_bin.index.intersection(allowed)
    return pd.DatetimeIndex(days).sort_values(), current


def dedup_episodes(days: pd.DatetimeIndex, calendar: pd.DatetimeIndex,
                   gap_trading_days: int) -> pd.DatetimeIndex:
    """연속 유사일을 에피소드화 — 직전 채택일로부터 거래일 간격 gap 미만이면 건너뜀."""
    if len(days) == 0:
        return days
    pos = {d: i for i, d in enumerate(calendar)}
    kept: list[pd.Timestamp] = []
    last_pos = -10**9
    for d in days:
        p = pos.get(d)
        if p is None:
            continue
        if p - last_pos >= gap_trading_days:
            kept.append(d)
            last_pos = p
    return pd.DatetimeIndex(kept)


MIN_BADGE_EPISODES = 3        # 창 안 에피소드 최소 건수
BADGE_ENRICHMENT = 1.5         # 창 안 비중이 표본 기준 비중(창 길이/전체 창)의 이 배수 이상일 때만 부여


def case_badges_for(days: pd.DatetimeIndex,
                    sample_index: pd.DatetimeIndex | None = None,
                    var_code: str | None = None) -> list[str]:
    """위기 사례 배지 — A-270: 존재 검사(창 안 1일)에서 **밀도 검사**로 교체.

    구 규칙은 2010~2025에 고르게 퍼진 에피소드면 4사례 창(전체의 ~34%)에 전부 걸려 배지가 정보량 0이었다.
    신 규칙: 창 안 에피소드 ≥ MIN_BADGE_EPISODES **그리고** 창 안 비중이 창의 표본 비중 × BADGE_ENRICHMENT 이상.
    반환 형식 '이름 (n회)' — 서사 조회는 `badge_name()`으로 이름만 추출.
    A-284(검증 3): `var_code`를 주면 **날짜 농축 AND 변수–사례 인과 관련(`CaseProfile.related`)**일 때만 부여 —
    난방유가 '아르헨 가뭄' 사례에 붙던 오연결 차단. 날짜만 겹친 사례는 `date_only_case_badges()`로 별도 조회.
    """
    if len(days) == 0:
        return []
    badges = []
    total = len(days)
    if sample_index is None or len(sample_index) == 0:
        sample_index = days
    span = (sample_index.max() - sample_index.min()).days or 1
    for name, (s, e) in CASE_WINDOWS.items():
        s_ts, e_ts = pd.Timestamp(s), pd.Timestamp(e)
        inside = int(((days >= s_ts) & (days <= e_ts)).sum())
        base_share = max((min(e_ts, sample_index.max()) - max(s_ts, sample_index.min())).days, 0) / span
        share = inside / total
        if inside >= MIN_BADGE_EPISODES and base_share > 0 and share >= base_share * BADGE_ENRICHMENT:
            if var_code is not None and not case_related_to(name, var_code):
                continue
            badges.append(f"{name} ({inside}회)")
    return badges


def date_only_case_badges(days: pd.DatetimeIndex, sample_index: pd.DatetimeIndex | None,
                          var_code: str) -> list[str]:
    """날짜 농축은 통과했으나 변수–사례 연결 근거가 없어 **제외된** 사례 — 화면에 '연결 근거 없음'으로 정직 표기."""
    all_b = case_badges_for(days, sample_index, var_code=None)
    kept = set(case_badges_for(days, sample_index, var_code=var_code))
    return [b for b in all_b if b not in kept]


def badge_name(badge: str) -> str:
    """'사례 ③ … (7회)' → '사례 ③ …' (서사 조회 키)."""
    return badge.rsplit(" (", 1)[0] if badge.endswith("회)") else badge


def summarize_forward(analysis: pd.DataFrame, episodes: pd.DatetimeIndex,
                      horizon: int) -> tuple[int, int, int, float, float, float, list[int]]:
    """에피소드 일들의 target_ret{h} 실측 집계 — 원시 로그수익률(캡핑 없음 — D6)."""
    col = f"target_ret{horizon}"
    if col not in analysis.columns:
        raise KeyError(f"[오류] mart에 {col} 없음 — build_feature_mart TARGET_HORIZONS 확인")
    rets = analysis.loc[analysis.index.intersection(episodes), col].dropna()
    pct = (np.expm1(rets) * 100.0)
    n_up = int((pct > 0).sum())
    n_down = int((pct < 0).sum())
    years = sorted({d.year for d in rets.index})
    if len(pct) == 0:
        return 0, n_up, n_down, math.nan, math.nan, math.nan, years
    return (len(pct), n_up, n_down,
            float(pct.quantile(0.10)), float(pct.quantile(0.50)), float(pct.quantile(0.90)),
            years)


def _z90_from_level(level: pd.Series) -> pd.Series:
    """마트 `__z90` 정의와 동일 — IQR 캡 없는 90일 롤링 표준화(관측≥30)."""
    v = pd.to_numeric(level, errors="coerce")
    m = v.rolling(90, min_periods=30).mean()
    sd = v.rolling(90, min_periods=30).std(ddof=1)
    return (v - m) / sd


def _analogue_for_var(analysis: pd.DataFrame, code: str,
                      horizons: tuple[int, ...],
                      levels_all: pd.DataFrame | None = None,
                      current_z: float | None = None) -> list[AnalogueResult]:
    z_col = _resolve_z_column(analysis.columns, code)
    base = code.split("__")[0]
    if z_col is None and levels_all is not None and not levels_all.empty:
        # A-270: 모델 경로의 개정 미보존 필터가 ONI·GPR 등을 분석 프레임에서 제거하던 결함 —
        #   참조 경로는 비필터 레벨에서 z90을 직접 만든다(원시 계열 기준 · 모델 투입 아님).
        alias = [c for c in _ALERT_Z_ALIASES.get(code, []) + _ALERT_Z_ALIASES.get(base, [])]
        lvl_candidates = [base] + [c.split("__")[0] for c in alias]
        lvl = next((c for c in lvl_candidates if c in levels_all.columns), None)
        if lvl is not None:
            zc = f"{lvl}__z90"
            z = _z90_from_level(levels_all[lvl]).reindex(analysis.index)
            analysis = analysis.copy()
            analysis[zc] = z
            z_col = zc
    if z_col is None:
        return [AnalogueResult(base, "?", math.nan, "quantile_slice", h, 0, 0, 0, 0,
                               math.nan, math.nan, math.nan,
                               guard_note="분석 데이터에 해당 계열 없음 — 산출 보류")
                for h in horizons]
    out: list[AnalogueResult] = []
    for h in horizons:
        res = None
        for step, bins in enumerate((ANALOGUE_QUANTILE_BINS, RELAX_BINS)):
            days, cur_z = find_analogue_days_quantile(analysis[z_col], bins=bins, current=current_z)
            episodes = dedup_episodes(days, analysis.index, gap_trading_days=h)
            n, n_up, n_down, p10, p50, p90, years = summarize_forward(analysis, episodes, h)
            if n >= MIN_ANALOGUE_EPISODES:
                res = AnalogueResult(base, z_col, cur_z, "quantile_slice", h,
                                     int(len(days)), n, n_up, n_down, p10, p50, p90,
                                     years, case_badges_for(episodes, analysis.index, var_code=base),
                                     relax_step=step,
                                     date_only_badges=date_only_case_badges(episodes, analysis.index, base))
                break
        if res is None:
            days, cur_z = find_analogue_days_quantile(analysis[z_col], current=current_z)
            res = AnalogueResult(base, z_col,
                                 cur_z if cur_z == cur_z else math.nan,
                                 "quantile_slice", h, int(len(days)), 0, 0, 0,
                                 math.nan, math.nan, math.nan,
                                 guard_note=f"유사 시기 {MIN_ANALOGUE_EPISODES}회 미만"
                                            " — 산출 보류")
        out.append(res)
    return out


def build_analogue_context(
    alert_codes: list[str], top_codes: list[str],
    horizons: tuple[int, ...] = ANALOGUE_HORIZONS,
    analysis: pd.DataFrame | None = None,
    current_z_map: dict[str, float] | None = None,
) -> list[AnalogueResult]:
    """경보 변수 우선 + 중요도 상위로 보충한 변수 집합의 유사국면 실측 집계.

    analysis 미지정 시 mart 로더 사용(실패 시 빈 목록 — 호출측 정직 강등).
    current_z_map: {변수 코드(base): 오늘 기준 편차} — 있으면 버킷 선택의 '현재'로 사용(A-284).
    """
    levels_all: pd.DataFrame | None = None
    if analysis is None:
        try:
            from src.forecasting.variable_importance_g1 import (_load_g1_feature_mart,
                                                                 _load_levels_all)
            analysis, _levels, _t = _load_g1_feature_mart()
            try:
                levels_all = _load_levels_all()
            except Exception:                                    # noqa: BLE001
                levels_all = None
        except Exception as e:                                   # noqa: BLE001 — 비치명
            print(f"[정보] 유사국면 — mart 로드 불가(산출 보류): {type(e).__name__}: {e}")
            return []
    seen: set[str] = set()
    codes: list[str] = []
    for c in list(alert_codes) + list(top_codes):
        base = str(c).split("__")[0]
        if base not in seen:
            seen.add(base)
            codes.append(str(c))
        if len(codes) >= MAX_ANALOGUE_VARS:
            break
    results: list[AnalogueResult] = []
    cz = current_z_map or {}
    for c in codes:
        base = str(c).split("__")[0]
        results.extend(_analogue_for_var(analysis, c, horizons, levels_all,
                                         current_z=cz.get(c, cz.get(base))))
    return results


_H_LABEL = {5: "약 1주", 20: "약 1개월", 60: "약 3개월"}


def variable_link_line(var_code: str) -> str:
    """변수→대두유 연결 설명 한 줄(검증 3) — 온톨로지 인과 경로 기반(daily_brief 파생표 재사용). 실패 시 정직 문구."""
    try:
        from src.reporting.daily_brief import _driver_link_line
        return _driver_link_line(var_code).replace("연결 근거:", "이 변수가 대두유에 닿는 경로:", 1)
    except Exception:                                        # noqa: BLE001
        return "이 변수가 대두유에 닿는 경로: 온톨로지 조회 불가 — 상관 기반 참고"


def no_badge_line(rs: list[AnalogueResult]) -> str:
    """배지가 없을 때의 정직 문구 — 날짜만 겹친 사례가 있으면 그 사실을 밝힌다(검증 3)."""
    by_h = {r.horizon: r for r in rs}
    r = by_h.get(20) or (rs[0] if rs else None)
    if r is not None and r.date_only_badges:
        names = " · ".join(badge_name(b) for b in r.date_only_badges)
        return f"겹치는 위기 사례 없음 — 날짜상 겹친 사례({names})는 있으나 변수–사례 연결 근거가 없어 표시하지 않음"
    return "겹치는 위기 사례 없음(변수–사례 연결 근거 없음)"


def representative_badges(rs: list[AnalogueResult]) -> list[str]:
    """A-270: 지평별 배지를 합집합하지 않고 **20일 지평(대표)**의 배지만 쓴다(없으면 가장 짧은 지평)."""
    by_h = {r.horizon: r for r in rs}
    r = by_h.get(20) or (rs[0] if rs else None)
    return sorted(r.case_badges) if r else []


def format_result_line(r: AnalogueResult) -> str:
    """A-191 서술 계약 — 렌더 공용 문장(필수 문구 포함·금지어 없음)."""
    if r.guard_note:
        return f"{_H_LABEL.get(r.horizon, r.horizon)}: {r.guard_note}"
    years = ", ".join(str(y) for y in r.years[:6]) + ("…" if len(r.years) > 6 else "")
    relax = " · 비교 구간을 넓혀 산출(오분위)" if r.relax_step else ""
    return (f"{_H_LABEL.get(r.horizon, r.horizon)} 후 실측: 유사 시기 {r.n_episodes}회"
            f"({years}) 중 상승 {r.n_up}회·하락 {r.n_down}회 — 변화율 중앙 {r.ret_p50:+.1f}% · "
            f"하위~상위 10% [{r.ret_p10:+.1f}%, {r.ret_p90:+.1f}%]{relax}")


def render_analogue_md(results: list[AnalogueResult]) -> list[str]:
    """월별 심층판 md 섹션 (Stage 1 — 통계 검정 없음 명기)."""
    if not results:
        return ["## 과거 유사 시기 실측 참조", "",
                "- 분석 데이터 미가용 또는 대상 변수 부재 — 산출 보류.", ""]
    lines = ["## 과거 유사 시기 실측 참조", "",
             f"변수의 평소 대비 편차가 현재와 같은 구간이었던 과거 거래일들의 이후 실측 분포. "
             f"**{_REQUIRED_CAPTION}** (통계 검정 없음 — 기술 서술).", ""]
    by_var: dict[str, list[AnalogueResult]] = {}
    for r in results:
        by_var.setdefault(r.var_code, []).append(r)
    for var, rs in by_var.items():
        z_txt = f"{rs[0].current_z:+.1f}" if rs[0].current_z == rs[0].current_z else "?"
        try:
            from src.reporting.daily_brief import _label_ko
            var_label = _label_ko(var)
        except Exception:                                        # noqa: BLE001
            var_label = var
        lines.append(f"### {var_label} (현재 편차 {z_txt})")
        lines.append(f"- {variable_link_line(var)}")
        for r in sorted(rs, key=lambda x: x.horizon):
            lines.append(f"- {format_result_line(r)}")
        badges = representative_badges(rs)
        if not badges:
            lines.append(f"- {no_badge_line(rs)}")
        if badges:
            lines.append(f"- 겹치는 위기 사례(1개월 기준·충분히 겹친 경우만): {' · '.join(badges)} "
                         f"(→ `_reference/soybean_oil_historical_crisis_analysis.md` — "
                         f"재평가 기록 병독)")
            for b in badges:
                narr = case_narrative_lines(badge_name(b))
                if narr:
                    lines.append(f"  - **{b} — 왜 유사한가**")
                    lines.extend(f"    - {t}" for t in narr)
        lines.append("")
    return lines


def self_test() -> list[str]:
    """합성 데이터로 계약 검증 — 문제 목록 반환(비면 통과)."""
    problems: list[str] = []
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2015-01-01", periods=1500)
    z = pd.Series(np.sin(np.arange(1500) / 40) + rng.normal(0, .3, 1500), index=idx)
    ret20 = pd.Series(rng.normal(0.01, 0.05, 1500), index=idx)
    analysis = pd.DataFrame({"TESTVAR__z90": z, "target_ret5": ret20,
                             "target_ret20": ret20, "target_ret60": ret20})
    res = build_analogue_context(["TESTVAR"], [], analysis=analysis)
    if len(res) != 3:
        problems.append(f"horizon 3종 기대, {len(res)}개 산출")
    for r in res:
        if not r.guard_note:
            # 누수 가드: 에피소드가 마지막 60거래일 안에 있으면 실패
            line = format_result_line(r)
            for w in _FORBIDDEN_WORDS:
                if w in line:
                    problems.append(f"금지어 '{w}' 발견: {line}")
    md = "\n".join(render_analogue_md(res))
    if _REQUIRED_CAPTION not in md:
        problems.append("필수 캡션 부재 (A-191)")
    # 누수 가드 직접 검증
    days, _ = find_analogue_days_quantile(analysis["TESTVAR__z90"])
    if len(days) and days.max() > idx[-EXCLUDE_RECENT_TRADING_DAYS - 1]:
        problems.append("전방 창 겹침 누수 가드 위반")
    # 표본 부족 강등 검증
    tiny = analysis.iloc[:40]
    res2 = build_analogue_context(["TESTVAR"], [], analysis=tiny)
    if not all(r.guard_note for r in res2):
        problems.append("표본 부족 시 산출 보류 미작동")
    # 사례 서사 계약 검증(A-191) — 전 프로파일 금지어·필드 완전성
    for name in CASE_PROFILES:
        narr = "\n".join(case_narrative_lines(name))
        if len(case_narrative_lines(name)) != 5:
            problems.append(f"사례 서사 필드 불완전: {name}")
        for w in _FORBIDDEN_WORDS:
            if w in narr:
                problems.append(f"사례 서사 금지어 '{w}': {name}")
    return problems


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        probs = self_test()
        if probs:
            print("[오류] 유사국면 self-test 실패:")
            for p in probs:
                print(f"  - {p}")
            sys.exit(1)
        print("[완료] 유사국면 self-test 통과")
        sys.exit(0)
    for line in render_analogue_md(build_analogue_context([], [])):
        print(line)
