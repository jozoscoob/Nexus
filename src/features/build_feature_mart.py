#!/usr/bin/env python3
"""
Feature Mart — as-of 시점 정합 특징 테이블 (Phase 2 · D-033)

무엇을 만드는가:
    커넥터·파서가 만든 롱포맷 parquet 수십 개를 **거래일 달력에 정렬된 하나의 wide 테이블**로
    합친다. G1(동인분석)·G2(가격밴드)·G3(레짐)이 **같은 스냅샷**을 보게 하는 것이 목적이다.
    모델마다 CSV를 따로 만들면 같은 질문에 서로 다른 답이 나온다.

왜 단순 pivot이 아닌가 — 누수의 기본형:
    WASDE 8월호는 8월 12일에 나온다. `price_date=2026-08-01`을 그대로 pivot한 뒤 ffill하면
    모델은 8월 1~11일에 **아직 존재하지 않는 값**을 본다. 백테스트는 좋아지고 실전은 무너진다.
    그래서 join 키는 `price_date`가 아니라 **`available_at`**이다.

        모델의 t일 입력 = available_at <= t 를 만족하는 가장 최근 값   (CLAUDE.md §1)

    DuckDB `ASOF JOIN`이 이 의미를 그대로 표현한다. pandas merge_asof도 되지만 지표 470종 ×
    거래일 4,000일 규모에서 DuckDB가 메모리·속도 모두 유리하고 SQL로 의도가 드러난다.

세 가지 안전장치:
    ① 개정본(vintage) 결정성 — 같은 available_at에 여러 행이 있으면 event_time이 늦은 쪽을
       택한다. "t시점에 알 수 있었던 가장 최신 관측"이 정의다. 임의 선택을 남기지 않는다.
    ② 신선도 상한(staleness cap) — 죽은 커넥터가 마지막 값을 영원히 forward-fill 하면
       모델은 "변하지 않는 강한 변수"를 학습한다. 지표의 **고유 주기**를 추정해 상한을
       넘긴 값은 결측으로 만든다. 결측은 fold 안에서 대치하면 되지만, 굳어버린 상수는
       발견조차 되지 않는다.
    ③ 타깃 분리 — 미래를 보는 컬럼은 `target_` 접두사 하나뿐이며 피처 목록에서 원천 배제한다.

파생 피처의 fold 안전성:
    여기서 만드는 파생은 **전부 후방참조(backward-looking)**다. 수익률·롤링 z-score는 t 시점
    이전 값만 쓰므로 fold 안에서 재적합할 필요가 없다. 반면 전체표본 표준화·전체구간 분해
    (VMD/EMD)는 미래를 끌어오므로 여기서 만들지 않는다(M-010).

사용:
    python -m src.features.build_feature_mart                  # 기본
    python -m src.features.build_feature_mart --start 2010-01-01 --end 2025-12-31
    python -m src.features.build_feature_mart --self-test      # 누수 자체검증만

산출:
    data/gold/feature_mart.parquet          — wide 테이블(거래일 × 피처+타깃)
    data/gold/feature_contract.yaml         — 컬럼별 출처·주기·신선도 상한 계약
    reports/market/feature_mart_{date}.md   — 커버리지·제외 사유 리포트

의존성: duckdb · pandas · pyarrow · pyyaml
"""
from __future__ import annotations

import argparse
import glob
import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from src.pipeline.asof import revision_status

RAW_DIR = os.environ.get("NEXUS_DATA_ROOT", "data/raw")
GOLD_DIR = Path("data/gold")
REPORT_DIR = Path("reports/market")

# 분석창 — M-008 확정(추정 2010-01~2025-12, 2026은 미완결 shadow slice)
DEFAULT_START = "2010-01-01"
DEFAULT_END = "2025-12-31"

# 목표변수 후보 — 앞쪽 우선
TARGET_CANDIDATES = ["CBOT_BO_CLOSE", "CBOT_SBO_FUTURES"]
TARGET_HORIZONS = [1, 5, 20, 60]        # 거래일 — CLAUDE.md §1
TARGET_TIME_BASES = {"CME_SESSION", "EXCHANGE_SETTLEMENT"}

# ── 중복 적재 방지 ───────────────────────────────────────────────────────────
# 같은 indicator_code를 담은 파일이 둘 이상이면 롱 테이블이 2배가 되고 ASOF 동점이 생긴다.
# 자동 판정(행 수 많은 쪽 등)은 조용히 틀리므로 **명시적으로** 우선순위를 적는다.
SUPERSEDES: dict[str, tuple[str, str]] = {
    # 대체될 파일 : (상위집합 파일, 사유)
    "te_commodities_historical.parquet": (
        "te_commodities_usd_mt.parquet",
        "단위정규화(value_usd_mt)를 더한 검증된 상위집합 (D8)",
    ),
}
# 단위정규화 파일에서 원 value 대신 쓸 컬럼(converted=True인 행만)
NORMALIZED_VALUE_COL = "value_usd_mt"

REQUIRED_COLS = ["indicator_code", "value", "event_time", "available_at"]
TARGET_METADATA_COLS = ["target_eligible", "time_basis", "unit"]


# ── 신선도 상한 ──────────────────────────────────────────────────────────────
def staleness_cap_days(median_gap: float) -> int:
    """지표 고유 주기로부터 forward-fill 허용 상한을 정한다.

    근거: 정상 운영이라면 다음 관측이 주기 내에 도착한다. 주기의 몇 배를 넘겨도
    새 값이 없다는 것은 **수집 실패이지 값의 지속이 아니다**. 여유(+15일)는 발표
    지연·연휴를 흡수하되, 상한 800일로 잘라 연간 자료가 2주기를 끌지 못하게 한다.

    일별(주말 포함 median≈1) → 19일 · 주별(7) → 43일 · 월별(30) → 135일 · 연간(365) → 800일
    """
    if not median_gap or pd.isna(median_gap):
        return 30
    return int(min(max(4 * float(median_gap) + 15, 15), 800))


@dataclass
class Loaded:
    long: pd.DataFrame
    freq: dict[str, float]                       # indicator_code → median gap(일)
    origin: dict[str, str] = field(default_factory=dict)   # indicator_code → 파일명
    skipped: list[str] = field(default_factory=list)


# A-271(2026-09-14): 예보 층(climate_forecast_*.parquet — price_date=발행일·lead별 다중 값)은 마트 미등재(A-263 설계).
#   재귀 글로브가 이를 적재하면 (지표, event_time) 값충돌 게이트가 정당 차단해 readiness 잡이 죽는다.
EXCLUDE_PREFIXES: tuple[str, ...] = ("climate_forecast",)
SNAPSHOT_RE = re.compile(r"^(.*)_(\d{8})$")   # <계열>_<YYYYMMDD>.parquet 일자 스냅샷


def load_long(raw_dir: str = RAW_DIR) -> Loaded:
    """전 parquet → 단일 롱 테이블. as-of 필드 없는 파일은 제외한다."""
    frames: list[pd.DataFrame] = []
    origin: dict[str, str] = {}
    skipped: list[str] = []
    files = sorted(glob.glob(os.path.join(raw_dir, "**", "*.parquet"), recursive=True))
    available_names = {os.path.basename(path) for path in files}
    target_metadata_missing: list[str] = []

    for f in files:
        name = os.path.basename(f)
        if name.startswith(EXCLUDE_PREFIXES):
            skipped.append(f"{name} — 예보 층: 마트 미등재(A-263 · 발행일 축 vintage는 별도 층)")
            continue
        if name in SUPERSEDES:
            replacement, reason = SUPERSEDES[name]
            if replacement in available_names:
                skipped.append(f"{name} — 중복 제외: {replacement} {reason}")
                continue
        try:
            df = pd.read_parquet(f)
        except Exception as e:                        # 손상 파일이 전체를 막지 않게
            skipped.append(f"{name} — 읽기 실패 {type(e).__name__}")
            continue

        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            # as-of 필드가 없으면 **모델 투입 금지**(CLAUDE.md §1). 조용히 넘기지 않고 남긴다.
            skipped.append(f"{name} — 필수 컬럼 없음 {missing}")
            continue

        codes = set(df["indicator_code"].dropna().astype(str).unique())
        if codes.intersection(TARGET_CANDIDATES):
            missing_target_meta = [c for c in TARGET_METADATA_COLS if c not in df.columns]
            if missing_target_meta:
                target_metadata_missing.append(
                    f"{name}: {sorted(codes.intersection(TARGET_CANDIDATES))} "
                    f"메타데이터 누락 {missing_target_meta}")

        val = df["value"]
        if NORMALIZED_VALUE_COL in df.columns and "converted" in df.columns:
            # 미변환 현지통화를 USD/MT 계열에 섞지 않는다. 별도 raw 코드가 없으면 모델에서 제외.
            val = df[NORMALIZED_VALUE_COL].where(df["converted"].fillna(False))

        eligible_raw = df.get("target_eligible", pd.Series(False, index=df.index))
        if not pd.api.types.is_bool_dtype(eligible_raw):
            eligible_raw = eligible_raw.astype("string").str.lower().isin({"true", "1", "yes"})
        sub = pd.DataFrame({
            "indicator_code": df["indicator_code"].astype(str),
            "value": pd.to_numeric(val, errors="coerce"),
            "event_time": pd.to_datetime(df["event_time"], errors="coerce"),
            "available_at": pd.to_datetime(df["available_at"], errors="coerce"),
            "source_vintage": df.get("source_vintage", pd.Series([None] * len(df))).astype("string"),
            "unit": df.get("unit", pd.Series("UNSPECIFIED", index=df.index)).astype("string"),
            "target_eligible": eligible_raw.fillna(False).astype(bool),
            "time_basis": df.get(
                "time_basis", pd.Series("UNSPECIFIED", index=df.index)
            ).astype("string"),
        })
        sub = sub.dropna(subset=["value", "event_time", "available_at"])
        # 일자 스냅샷 계열(예: commodity_data_20261117 / _20261119) 식별 — 같은 계열의 겹치는 관측은
        # 아래에서 최신 스냅샷 값으로 정리(앞선 스냅샷은 장중 미완성 봉일 수 있음)
        m = SNAPSHOT_RE.match(os.path.splitext(name)[0])
        sub["_family"] = m.group(1) if m else name
        sub["_snap"] = m.group(2) if m else ""
        if sub.empty:
            skipped.append(f"{name} — 유효 관측 0건")
            continue
        for c in sub["indicator_code"].unique():
            origin.setdefault(str(c), name)
        frames.append(sub)

    if not frames:
        raise RuntimeError(f"[오류] {raw_dir} 에서 as-of 필드를 갖춘 parquet을 찾지 못했습니다. "
                           f"커넥터·파서를 먼저 실행하세요.")
    if target_metadata_missing:
        raise RuntimeError(
            "[오류] canonical target 코드가 계약 메타데이터 없이 적재되었습니다: "
            + "; ".join(target_metadata_missing)
            + ". 기존 CBOT 코드를 UTC 버킷에서 재사용하지 말고 명시적 세션/정산 원천만 발행하세요.")

    long = pd.concat(frames, ignore_index=True)
    for col in ("event_time", "available_at"):
        if getattr(long[col].dtype, "tz", None) is not None:
            long[col] = long[col].dt.tz_localize(None)
        long[col] = long[col].dt.normalize()

    # ① 결정적 dedup — 같은 (지표, available_at)에서 event_time이 늦은 관측을 남긴다.
    #    "t에 알 수 있었던 가장 최신 관측"이라는 정의를 코드로 못박는 지점.
    #
    #    ⚠️ 여기서 자동 해소해도 되는 것은 **event_time이 다른** 중복뿐이다.
    #    event_time까지 같은데 값이 다르면 그것은 순서 문제가 아니라 **지표코드 설계 오류**다
    #    (A-126: WASDE가 세계표 1.44 백만MT와 미국표 3,176 백만파운드를 한 코드에 담고 있었다).
    #    ASOF JOIN은 동점을 물리적 행 순서로 조용히 해소하므로 실행마다 값이 바뀐다.
    #    자동 선택으로 덮지 말고 **실패시킨다**.
    unit_clash = long.groupby("indicator_code")["unit"].nunique()
    unit_clash = unit_clash[unit_clash > 1]
    if len(unit_clash):
        sample = ", ".join(f"{code}({int(count)}단위)"
                           for code, count in unit_clash.head(5).items())
        raise RuntimeError(
            f"[오류] 동일 indicator_code에 단위가 여러 개인 지표 {len(unit_clash):,}종: {sample}. "
            "단위별 지표코드로 분리하세요.")

    # ⓪ 같은 커넥터의 일자 스냅샷끼리 겹치는 (지표, event_time)은 최신 스냅샷만 남긴다(2026-11-19).
    #    예: commodity_data_20261117의 11-17 봉은 수집 시점 장중 값, _20261119의 같은 봉은 확정 값.
    #    서로 다른 파일 계열·같은 파일 안의 충돌은 그대로 아래 게이트에서 실패한다(지표코드 설계 오류).
    snap = long["_snap"] != ""
    if snap.any():
        newest = long[snap].groupby(["_family", "indicator_code", "event_time"])["_snap"].transform("max")
        stale = long.index[snap][long.loc[snap, "_snap"].to_numpy() != newest.to_numpy()]
        if len(stale):
            print(f"[정리] 같은 계열 일자 스냅샷 중복 {len(stale):,}행 → 최신 스냅샷 값 채택")
            long = long.drop(index=stale)
    long = long.drop(columns=["_family", "_snap"])

    key = ["indicator_code", "event_time"]
    clash = long.groupby(key)["value"].nunique()
    clash = clash[clash > 1]
    if len(clash):
        top = clash.sort_values(ascending=False).head(5)
        detail = "; ".join(f"{i[0]}@{pd.Timestamp(i[1]).date()}({int(n)}개 값)"
                           for i, n in top.items())
        raise RuntimeError(
            f"[오류] 동일 (지표, event_time)에 값이 여러 개인 조합 {len(clash):,}건 — "
            f"지표코드가 서로 다른 계열을 뭉개고 있습니다. 예: {detail}. "
            f"파서에서 축(단위·상품군·지역)을 코드에 반영해 분리하세요.")

    before = len(long)
    long = (long.sort_values(["indicator_code", "available_at", "event_time", "source_vintage"])
                .drop_duplicates(["indicator_code", "available_at"], keep="last")
                .reset_index(drop=True))
    if before != len(long):
        print(f"[정리] 동일 (지표, available_at) 중복 {before - len(long):,}건 → 최신 event_time 채택")

    # 고유 주기 추정 — event_time 간격의 중앙값
    freq = (long.sort_values(["indicator_code", "event_time"])
                .groupby("indicator_code")["event_time"]
                .apply(lambda s: s.drop_duplicates().diff().dt.days.median()))
    return Loaded(long=long, freq=freq.to_dict(), origin=origin, skipped=skipped)


def _validate_target_rows(long: pd.DataFrame, target: str) -> pd.DatetimeIndex:
    """타깃 계열이 거래 세션 의미 계약을 충족하는지 검증한다."""
    rows = long.loc[long["indicator_code"] == target].copy()
    if rows.empty:
        raise RuntimeError(f"[오류] 목표변수 {target} 관측이 없습니다.")
    if not rows["target_eligible"].fillna(False).all():
        raise RuntimeError(
            f"[오류] {target}에 target_eligible=true가 아닌 행이 있습니다. "
            "UTC 일봉·검증 전 가격은 G1/G2 타깃으로 사용할 수 없습니다.")
    bases = set(rows["time_basis"].dropna().astype(str).unique())
    if not bases or not bases.issubset(TARGET_TIME_BASES):
        raise RuntimeError(
            f"[오류] {target} time_basis={sorted(bases) or ['UNSPECIFIED']} — "
            f"허용값은 {sorted(TARGET_TIME_BASES)}입니다.")
    units = set(rows["unit"].dropna().astype(str).unique())
    if units != {"USc/lb"}:
        raise RuntimeError(
            f"[오류] {target} 단위={sorted(units)} — 모델 타깃은 USc/lb 단일 단위여야 합니다.")

    dates = pd.to_datetime(rows["event_time"], errors="coerce").dropna().dt.normalize()
    available = pd.to_datetime(rows["available_at"], errors="coerce")
    event = pd.to_datetime(rows["event_time"], errors="coerce")
    if event.isna().any() or available.isna().any():
        raise RuntimeError(f"[오류] {target}의 event_time/available_at에 결측이 있습니다.")
    if (available < event).any():
        raise RuntimeError(f"[오류] {target}의 available_at이 event_time보다 이른 행이 있습니다.")
    values = pd.to_numeric(rows["value"], errors="coerce")
    if values.isna().any() or (values <= 0).any():
        raise RuntimeError(f"[오류] {target}에 결측·0·음수 가격이 있습니다.")
    weekends = dates[dates.dt.dayofweek >= 5]
    if not weekends.empty:
        sample = ", ".join(str(d.date()) for d in weekends.head(3))
        raise RuntimeError(
            f"[오류] {target}에 주말 거래일 {weekends.nunique():,}개가 있습니다(예: {sample}). "
            "UTC 버킷을 거래소 세션 날짜로 오인했을 가능성이 있습니다.")
    duplicated = dates.duplicated(keep=False)
    if duplicated.any():
        raise RuntimeError(
            f"[오류] {target}에 세션당 2개 이상 관측 {dates[duplicated].nunique():,}일이 있습니다.")
    return pd.DatetimeIndex(dates.drop_duplicates().sort_values())


def build_calendar(long: pd.DataFrame, start: str, end: str) -> tuple[pd.DatetimeIndex, str]:
    """검증된 목표변수의 실제 거래일만 달력으로 쓴다."""
    target = next((c for c in TARGET_CANDIDATES if c in set(long["indicator_code"])), None)
    lo, hi = pd.Timestamp(start), pd.Timestamp(end)
    if target is None:
        raise RuntimeError(
            "[오류] 검증된 목표변수가 없습니다. feature mart를 생성하지 않습니다. "
            "CBOT 거래 세션 또는 공식 settlement 계열을 먼저 적재하세요.")
    dates = _validate_target_rows(long, target)
    calendar = pd.DatetimeIndex(dates[(dates >= lo) & (dates <= hi)])
    if len(calendar) < 100:
        raise RuntimeError(
            f"[오류] 목표변수 {target} 관측 {len(calendar):,}일 — 거래 달력으로 쓰기 부족합니다.")
    return calendar, target


def asof_align(long: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """DuckDB ASOF JOIN — 거래일 × 지표 격자에 available_at <= d 인 최근값을 붙인다."""
    cal = pd.DataFrame({"d": calendar})
    con = duckdb.connect()
    con.register("cal", cal)
    con.register("feat", long[["indicator_code", "value", "event_time", "available_at"]])
    # ASOF JOIN은 등가조건 + 부등호 1개를 받는다. 여기서 부등호가 곧 as-of 규칙이다.
    out = con.execute("""
        WITH inds AS (SELECT DISTINCT indicator_code FROM feat),
             grid AS (SELECT c.d, i.indicator_code FROM cal c CROSS JOIN inds i)
        SELECT g.d, g.indicator_code, f.value, f.event_time, f.available_at
        FROM grid g
        ASOF LEFT JOIN feat f
          ON g.indicator_code = f.indicator_code
         AND g.d >= f.available_at
        ORDER BY g.indicator_code, g.d
    """).df()
    con.close()
    return out


def apply_staleness(aligned: pd.DataFrame, freq: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """신선도 상한 초과 값을 결측 처리하고 제외 내역을 돌려준다."""
    caps = {c: staleness_cap_days(freq.get(c)) for c in aligned["indicator_code"].unique()}
    cap_s = aligned["indicator_code"].map(caps)
    age = (aligned["d"] - aligned["available_at"]).dt.days
    stale = age.notna() & (age > cap_s)
    detail = (aligned.assign(stale=stale, cap=cap_s, age=age)
                     .loc[stale]
                     .groupby("indicator_code")
                     .agg(제외일수=("d", "size"), 상한일=("cap", "max"),
                          최대경과일=("age", "max"))
                     .reset_index())
    out = aligned.copy()
    out.loc[stale, "value"] = pd.NA
    return out, detail


def pivot_wide(aligned: pd.DataFrame, values: str = "value") -> pd.DataFrame:
    w = aligned.pivot(index="d", columns="indicator_code", values=values)
    w.index.name = "price_date"
    return w.astype("float64").sort_index()


def build_freshness(aligned: pd.DataFrame) -> pd.DataFrame:
    """지표별 `발표 후 경과일`.

    왜 필요한가: 일별 달력에 월간 지표를 ASOF로 붙이면 한 값이 평균 21거래일 이월된다.
    결측률만 보면 커버리지가 100%로 보이지만 **새 정보가 들어온 날은 12일뿐**이다.
    경과일 컬럼이 없으면 모델도 사람도 '이월'과 '신규 발표'를 구분하지 못한다.
    (트리 모델은 상수 구간을 시점 식별자로 악용하기도 한다.)
    """
    age = aligned.assign(age=(aligned["d"] - aligned["available_at"]).dt.days)
    return pivot_wide(age, values="age")


def derive_features(wide: pd.DataFrame, freq: dict[str, float],
                    min_coverage: float = 0.60) -> pd.DataFrame:
    """후방참조 파생만 생성한다 — 전부 t 이전 값만 사용하므로 fold 안전.

    일별 계열: 1·5·20·60거래일 로그수익률 + 90일 롤링 z-score
    저빈도 계열: 12개월 변화율 + 12개월 롤링 z-score
    """
    import numpy as np

    cols: dict[str, pd.Series] = {}
    n = max(len(wide), 1)
    for code in wide.columns:
        s = wide[code]
        if s.notna().sum() / n < min_coverage:
            continue                                   # 성긴 계열의 파생은 잡음만 늘린다
        gap = freq.get(code)
        gap = 999.0 if gap is None or pd.isna(gap) else float(gap)

        if gap <= 4:                                   # 일별 시장계열 — 모멘텀·변동성이 의미
            pos = s.where(s > 0)                       # 로그수익률은 양수 계열에만 정의된다
            for h in (1, 5, 20, 60):
                cols[f"{code}__ret{h}"] = np.log(pos / pos.shift(h))
            win = 90
        else:                                          # 월·연간 계열 — 전년동기 대비가 의미
            # A-291: 0을 지나는 계열(가격 차이·도착 단가 차이)은 변화율이 무의미 — 12개월 차이로 대체
            cols[f"{code}__chg12m"] = (s.diff(252) if (s <= 0).any()
                                       else s.pct_change(252, fill_method=None))
            win = 252

        # 롤링 z — 전체표본 표준화와 달리 t 이전 창만 쓰므로 fold 재적합이 필요 없다
        mp = max(int(win * 0.5), 10)
        m = s.rolling(win, min_periods=mp).mean()
        sd = s.rolling(win, min_periods=mp).std()
        cols[f"{code}__z{win}"] = (s - m) / sd.where(sd > 0)

    out = pd.DataFrame(cols, index=wide.index)
    return out.replace([np.inf, -np.inf], np.nan)


def build_targets(wide: pd.DataFrame, target: str | None) -> pd.DataFrame:
    """미래를 보는 컬럼은 여기서만 만든다 — 전부 `target_` 접두사."""
    idx = wide.index
    if not target or target not in wide.columns:
        nan = float("nan")
        cols = {f"target_ret{h}": pd.Series(nan, index=idx, dtype="float64")
                for h in TARGET_HORIZONS}
        cols["target_close"] = pd.Series(nan, index=idx, dtype="float64")
        return pd.DataFrame(cols, index=idx)

    import numpy as np
    close = wide[target].where(wide[target] > 0)
    cols = {"target_close": close}
    for h in TARGET_HORIZONS:
        cols[f"target_ret{h}"] = np.log(close.shift(-h) / close)     # ← 유일한 전방참조
    return pd.DataFrame(cols, index=idx)


# ── 자체검증 ─────────────────────────────────────────────────────────────────
def self_test(long: pd.DataFrame, aligned: pd.DataFrame, sample: int = 400) -> list[str]:
    """ASOF 결과를 pandas로 독립 재계산해 대조한다.

    같은 로직을 두 번 짜는 게 아니라 **다른 엔진(DuckDB vs pandas)**으로 같은 정의를
    계산해 비교한다. SQL 오타·조인 방향 실수처럼 눈으로 안 잡히는 오류를 잡는 목적.
    """
    problems: list[str] = []
    ok = aligned.dropna(subset=["value"])
    if ok.empty:
        return ["ASOF 결과가 전부 결측 — 정렬 실패"]

    # ① 규칙 위반: available_at > d 인 값이 붙었는가(가장 치명적인 누수)
    bad = ok[ok["available_at"] > ok["d"]]
    if len(bad):
        problems.append(f"🚨 available_at > 기준일 위반 {len(bad):,}건 — 미래 정보 누수")

    # ② 표본 재계산 대조
    s = ok.sample(min(sample, len(ok)), random_state=0)
    idx = long.set_index("indicator_code").sort_index()
    mism = 0
    for _, r in s.iterrows():
        try:
            g = idx.loc[[r["indicator_code"]]]
        except KeyError:
            mism += 1
            continue
        vis = g[g["available_at"] <= r["d"]]
        if vis.empty:
            mism += 1
            continue
        exp = vis.sort_values(["available_at", "event_time"]).iloc[-1]["value"]
        if not (pd.isna(exp) and pd.isna(r["value"])) and abs(float(exp) - float(r["value"])) > 1e-9:
            mism += 1
    if mism:
        problems.append(f"🚨 pandas 재계산 불일치 {mism}/{len(s)}건 — ASOF 정의 어긋남")

    # ③ 타깃 누수 감지용 카나리아: 미래값을 그대로 넣은 가짜 지표는 절대 붙지 않아야 한다
    canary = ok[ok["indicator_code"].str.startswith("__CANARY")]
    if len(canary):
        problems.append(f"🚨 카나리아 지표가 정렬에 포함됨 {len(canary):,}건")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="as-of 정합 feature mart 생성")
    ap.add_argument("--start", default=DEFAULT_START)
    ap.add_argument("--end", default=DEFAULT_END)
    ap.add_argument("--min-coverage", type=float, default=0.60,
                    help="파생 피처를 만들 최소 커버리지(기본 0.60)")
    ap.add_argument("--self-test", action="store_true", help="검증만 수행하고 저장하지 않음")
    a = ap.parse_args()

    print(f"[feature mart] {RAW_DIR} → 분석창 {a.start} ~ {a.end}")
    L = load_long()
    print(f"  롱 테이블 {len(L.long):,}행 · 지표 {L.long['indicator_code'].nunique():,}종")
    for s in L.skipped:
        print(f"  [제외] {s}")

    cal, target = build_calendar(L.long, a.start, a.end)
    print(f"  달력 {len(cal):,}일 ({cal.min().date()} ~ {cal.max().date()}) · "
          f"목표변수 {target or '미보유'}")

    aligned = asof_align(L.long, cal)
    aligned, stale_detail = apply_staleness(aligned, L.freq)
    print(f"  ASOF 정렬 {len(aligned):,}셀 · 신선도 상한 초과로 결측화된 지표 {len(stale_detail)}종")

    problems = self_test(L.long, aligned)
    for p in problems:
        print(f"  {p}")
    if problems:
        print("[중단] 자체검증 실패 — 산출물을 쓰지 않습니다.")
        return 1
    print("  ✅ 자체검증 통과 (as-of 규칙 위반 0건 · pandas 재계산 일치)")
    if a.self_test:
        return 0

    wide = pivot_wide(aligned)
    fresh = build_freshness(aligned)
    targets = build_targets(wide, target)
    derived = derive_features(wide, L.freq, a.min_coverage)

    # 피처와 타깃을 이름으로 분리한다 — 학습 코드가 실수로 타깃을 피처에 넣지 못하게.
    feat = pd.concat([wide.add_prefix("feat_"), derived.add_prefix("feat_"),
                      fresh.add_prefix("age_")], axis=1)
    mart = pd.concat([feat, targets], axis=1).reset_index()

    # 발표 이벤트 수 — 커버리지를 '이월 포함 결측률'이 아니라 '실제 갱신 횟수'로 본다
    events = (L.long[(L.long["available_at"] >= cal.min()) & (L.long["available_at"] <= cal.max())]
                .groupby("indicator_code")["available_at"].nunique())

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = GOLD_DIR / "feature_mart.parquet"
    mart.to_parquet(out_path, index=False)

    # ── 계약 파일 — 컬럼별 출처·주기·상한을 남겨야 재현·감사 가능 ──────────────
    contract = {
        "generated": str(date.today()),
        "window": {"start": a.start, "end": a.end, "rows": int(len(mart))},
        "target": {
            "indicator": target,
            "horizons": TARGET_HORIZONS,
            "columns": sorted(targets.columns),
            "target_eligible": bool(
                L.long.loc[L.long["indicator_code"] == target, "target_eligible"].all()
            ),
            "time_basis": sorted(
                L.long.loc[L.long["indicator_code"] == target, "time_basis"]
                .dropna().astype(str).unique().tolist()
            ),
            "unit": sorted(
                L.long.loc[L.long["indicator_code"] == target, "unit"]
                .dropna().astype(str).unique().tolist()
            ),
        },
        "asof_rule": "모델의 t일 입력 = available_at <= t 인 최근값 (CLAUDE.md §1)",
        "features": {
            f"feat_{c}": {
                "source_file": L.origin.get(c, "?"),
                "median_gap_days": (None if pd.isna(L.freq.get(c))
                                    else float(L.freq.get(c) or 0)),
                "staleness_cap_days": staleness_cap_days(L.freq.get(c)),
                "coverage": round(float(wide[c].notna().mean()), 4),
                "release_events": int(events.get(c, 0)),
                # D-034: 개정 이력이 없는 소스는 **개정 후 확정치를 과거에 쓰고 있다**.
                # 백테스트 성능이 실전에서 재현되지 않을 수 있으므로 반드시 표기한다.
                "revision_history": revision_status(c),
                "revision_contaminated": revision_status(c) == "none",
            } for c in sorted(wide.columns)
        },
        "derived_rule": ("일별(중앙간격<=4일): log수익률 1/5/20/60 + 90일 롤링 z. "
                         "저빈도: 12개월 변화율 + 252일 롤링 z. 전부 후방참조."),
    }
    (GOLD_DIR / "feature_contract.yaml").write_text(
        yaml.safe_dump(contract, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # ── 리포트 ─────────────────────────────────────────────────────────────
    cov = (wide.notna().mean().sort_values(ascending=False) * 100).round(1)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Feature Mart 생성 결과 — {date.today()}", "",
        f"- 분석창: {a.start} ~ {a.end} · 거래일 **{len(cal):,}일**",
        f"- 목표변수: **{target or '🚨 미보유 — 타깃 컬럼 전량 결측'}**",
        f"- 원천 지표 {len(wide.columns):,}종 → 파생 포함 피처 **{len(feat.columns):,}열**",
        f"- 산출: `{out_path}` ({len(mart):,}행 × {len(mart.columns):,}열)", "",
        "## 커버리지 분포", "",
        "| 구간 | 지표 수 |", "|---|---|",
        f"| 90% 이상 | {int((cov >= 90).sum())} |",
        f"| 70~90% | {int(((cov >= 70) & (cov < 90)).sum())} |",
        f"| 40~70% | {int(((cov >= 40) & (cov < 70)).sum())} |",
        f"| 40% 미만 | {int((cov < 40).sum())} |", "",
    ]
    contaminated = sorted(c for c in wide.columns if revision_status(c) == "none")
    if contaminated:
        lines += ["## 개정 오염 피처 (revision-contaminated)", "",
                  "> 해당 소스는 값을 개정하는데 **우리는 개정 전 값을 갖고 있지 않다**.",
                  "> 즉 백테스트가 '당시 알 수 없었던 확정치'를 쓰고 있다. 제거가 아니라",
                  "> **표기 + 민감도 검증**(해당 피처 제외 성능 비교)이 필요하다.", "",
                  f"대상 **{len(contaminated)}종**: "
                  + ", ".join(f"`{c}`" for c in contaminated[:25])
                  + (" …" if len(contaminated) > 25 else ""), ""]

    low_event = sorted((c for c in wide.columns if int(events.get(c, 0)) < 24),
                       key=lambda c: int(events.get(c, 0)))
    if low_event:
        lines += ["## 발표 이벤트가 적은 지표 (이월값 주의)", "",
                  "> 결측률 기준 커버리지는 높아도 **실제 갱신 횟수**가 적으면 대부분이 이월값이다.",
                  "> 커버리지 게이트를 이월값으로 통과시키지 않기 위한 대조 지표.", "",
                  "| 지표 | 발표 횟수 | 결측률 기준 커버리지 |", "|---|---|---|"]
        for c in low_event[:20]:
            lines.append(f"| `{c}` | {int(events.get(c, 0))} | {cov.get(c, 0):.1f}% |")
        lines.append("")

    if len(stale_detail):
        lines += ["## 신선도 상한 초과 (수집 중단 의심)", "",
                  "> 상한을 넘긴 값은 결측 처리했다. 굳어버린 상수를 모델이 학습하는 것보다",
                  "> 결측이 안전하다.", "",
                  "| 지표 | 제외 일수 | 상한(일) | 최대 경과(일) |", "|---|---|---|---|"]
        for _, r in stale_detail.sort_values("제외일수", ascending=False).head(30).iterrows():
            lines.append(f"| `{r['indicator_code']}` | {int(r['제외일수']):,} | "
                         f"{int(r['상한일'])} | {int(r['최대경과일'])} |")
        lines.append("")
    if L.skipped:
        lines += ["## 제외된 파일", ""] + [f"- {s}" for s in L.skipped] + [""]

    rep = REPORT_DIR / f"feature_mart_{date.today()}.md"
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n[완료] {out_path} — {len(mart):,}행 × {len(mart.columns):,}열")
    print(f"       {GOLD_DIR/'feature_contract.yaml'} · {rep}")
    if not target:
        print("  🚨 목표변수 미보유 — 타깃 전량 결측. Historical(connector=databento) 실행 필요")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
