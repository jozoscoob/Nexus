#!/usr/bin/env python3
"""
Trading Economics 히스토리 xlsx 수집·정형화 (WBS 1.1.44 · A-061)

배경: TE API 실시간 수집이 불안정하여(요청 근거) 조정자가 9개년(2017.01.01~2026.07.01)
      히스토리 xlsx를 수동 업로드함. 본 스크립트가 이를 롱포맷 parquet로 정형화한다.

입력: data/raw/Trading Economics/Markets/Commodities/{Agricultural,Energy,Shipping Indices}/*.xlsx
      (폴백: data/raw/*.xlsx — 재정리 전 상태)
      파일명 규칙: {YYYY}~{YYYY}_{Commodity}[_{Exchange}]_{Units}.xlsx
      시트명: '{YYYY}년' (연도별) · 컬럼: Month, Day, Open, High, Low, Close

출력: data/raw/te_commodities_historical.parquet
      컬럼: price_date, indicator_code, value(=Close), open, high, low,
            commodity, category, unit, exchange, source_name, ingested_at

주의(CLAUDE.md §2): xlsx는 수동 히스토리 백필 예외(USDA 패턴과 동일). 파이프라인 상시
      소스는 아니며 1회성 정형화 용도.

의존성: pandas >= 2.0 · openpyxl(읽기 엔진)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# as-of 헬퍼 로드 — 스크립트 직접 실행 시 저장소 루트를 경로에 추가
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from src.pipeline.asof import attach_asof  # noqa: E402

TE_ROOT   = Path("data/raw/Trading Economics/Markets/Commodities")
RAW_ROOT  = Path("data/raw")
OUT_PATH  = Path("data/raw/te_commodities_historical.parquet")
CORRECTIONS_PATH = Path("config/te_price_corrections.yaml")   # A-290: 공식 정산가 대조 정정(원본 xlsx 불변)

# 품목 → 카테고리 (폴더 미존재 시 파일명 기반 분류)
_AGRI = {"canola", "palm oil", "rapeseed", "soybeans", "sunflower oil"}
_SHIP = {"bdi", "containerized freight index", "drewry world container index"}
_INDU = {"di-ammonium", "urea", "dap"}
# 그 외 에너지 (brent, wti, coal, natural gas, gasoline 등)

_YEAR_SHEET_RE = re.compile(r"(\d{4})\s*년")


def _classify(commodity: str, parent: str) -> str:
    """폴더명 우선, 없으면 품목명으로 카테고리 판정."""
    p = parent.lower()
    if "agricultural" in p:
        return "Agricultural"
    if "energy" in p:
        return "Energy"
    if "shipping" in p:
        return "Shipping Indices"
    if "industrial" in p:
        return "Industrial"
    c = commodity.lower()
    if c in _AGRI:
        return "Agricultural"
    if c in _SHIP:
        return "Shipping Indices"
    if c in _INDU:
        return "Industrial"
    return "Energy"


def _parse_filename(stem: str) -> Optional[tuple[str, str, str]]:
    """'{YYYY}~{YYYY}_{Commodity}[_{Exchange}]_{Units}' → (commodity, exchange, unit)."""
    parts = stem.split("_")
    if len(parts) < 3 or "~" not in parts[0]:
        return None
    commodity = parts[1].strip()
    unit = parts[-1].strip()
    exchange = "_".join(parts[2:-1]).strip() if len(parts) > 3 else ""
    return (commodity, exchange, unit)


def _indicator_code(commodity: str) -> str:
    """품목명 → TE_ 접두 스네이크 대문자 지표코드."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", commodity).strip("_").upper()
    return f"TE_{slug}"


def _iter_te_files() -> list[Path]:
    """TE 폴더 우선, 없으면 루트의 YYYY~YYYY_ xlsx."""
    if TE_ROOT.exists():
        files = sorted(TE_ROOT.rglob("*.xlsx"))
        if files:
            return files
    return sorted(p for p in RAW_ROOT.glob("*.xlsx")
                  if re.match(r"\d{4}~\d{4}_", p.name))


def _longest_monotonic_run(days: list[int]) -> set[int]:
    """일(day) 수열에서 가장 긴 단조 구간의 인덱스 집합.

    시트가 오름차순인지 내림차순인지 **가정하지 않는다** — 둘 다 계산해 긴 쪽을 택한다.
    (TE 파일은 대부분 오름차순이지만 Urea 시트는 내림차순이다. 방향을 가정한 초판
    구현은 정상인 Urea 855행을 이물로 오판해 삭제했다.)
    """
    best: tuple[int, int] = (0, 0)                     # (start, length)
    for sign in (1, -1):
        run_start = 0
        for i in range(1, len(days) + 1):
            if i < len(days) and (days[i] - days[i - 1]) * sign > 0:
                continue
            if i - run_start > best[1]:
                best = (run_start, i - run_start)
            run_start = i
    return set(range(best[0], best[0] + best[1]))


def _fix_sheet_ordering(sub: pd.DataFrame, label: str) -> pd.DataFrame:
    """연도 시트의 날짜 오류 두 종류를 구분해 처리한다 (A-127).

    시트는 일별 시계열이므로 날짜가 **단조 증가**해야 한다. 실측된 위반은 두 가지다.

    ① 월 오타 — Month 칸이 1 커진 채 Day가 직전 행에서 이어진다.
       BDI 2021년 시트: `2/23 → 2/24 → **3/25** → **3/26** → 3/1 → 3/2 …`
       진짜 3월은 3/1부터 다시 시작하므로 앞의 두 행은 **2/25·2/26의 오타**다.
       실제 관측값이므로 버리지 않고 월을 되돌린다(가격도 1709→1700→1675로 연속).
       판정 근거: 새 달의 첫 행은 1~3일에서 시작하지 실측 25일에서 시작하지 않는다.

    ② 타 구간 혼입 — 이미 지나간 날짜가 값 수준까지 어긋난 채 다시 나온다.
       Canola 2010년 시트: 4/23~4/30 진행 후 4/27·4/28이 383원대가 아닌 **529원대**로
       재등장. 복원할 근거가 없으므로 제거한다.

    ①을 ②로 묶어 지우면 **정상 관측을 버리고 오타 행을 남기는** 정반대 결과가 난다
    (`duplicated(keep='first')`는 나중에 나온 진짜 행을 중복으로 표시한다).
    """
    if len(sub) < 3:
        return sub
    dates = pd.to_datetime(sub["price_date"]).tolist()
    n = len(dates)

    # 판정 기준은 정렬 방향이 아니라 **월 블록의 연속성**이다.
    #   시트가 오름차순이든 내림차순이든(Urea 시트는 내림차순이다) 한 달의 행들은
    #   파일 순서상 **한 덩어리**로 모여 있다. 어떤 달이 두 덩어리로 쪼개져 있으면
    #   작은 쪽이 이물질이다. 이 기준은 정렬 방향 가정을 하지 않는다.
    blocks: list[tuple[int, int, int]] = []            # (month, start, end)
    s = 0
    for i in range(1, n + 1):
        if i == n or dates[i].month != dates[s].month:
            blocks.append((dates[s].month, s, i))
            s = i
    existing = set(dates)
    fixed: list[tuple] = []
    drop_idx: set[int] = set()

    for month, st, en in blocks:
        days = [d.day for d in dates[st:en]]
        keep = _longest_monotonic_run(days)            # 그 달의 정상 본문
        odd = [i for i in range(len(days)) if i not in keep]
        if not odd or len(odd) > 3:
            # 이상행이 없거나 너무 많으면 판정 근거가 약하다 — 손대지 않는다.
            # (내림차순 시트를 오름차순으로 오판해 대량 삭제하는 사고를 막는다)
            continue
        is_prefix = all(i < min(keep) for i in odd)
        prev_month = dates[st - 1].month if st > 0 else None
        for k in odd:
            i = st + k
            # ① 월 오타: 블록 **앞머리**에 붙어 있고 직전 행이 한 달 전이면 그 달의 오타다
            cand = None
            if is_prefix and prev_month is not None and month == (prev_month % 12) + 1:
                try:
                    cand = dates[i].replace(month=prev_month)
                except ValueError:
                    cand = None
            if cand is not None and cand not in existing:
                existing.discard(dates[i]); existing.add(cand)
                fixed.append((dates[i].date(), cand.date()))
                dates[i] = cand
            else:
                drop_idx.add(i)                        # ② 복원 근거 없음 — 제거

    out = sub.copy()
    out["price_date"] = pd.Series(dates, index=out.index)
    if fixed:
        s_ = ', '.join(f"{a}→{b}" for a, b in fixed[:4])
        print(f"    [보정] {label}: 월 오타 {len(fixed)}건 복원 ({s_}"
              f"{' …' if len(fixed) > 4 else ''})")
    if drop_idx:
        pos = sorted(drop_idx)
        bad = [dates[i].date() for i in pos[:4]]
        print(f"    [제외] {label}: 복원 불가 이물 {len(pos)}건 "
              f"({', '.join(str(x) for x in bad)}{' …' if len(pos) > 4 else ''})")
        out = out.iloc[[i for i in range(n) if i not in drop_idx]]
    return out


def parse_te_file(path: Path) -> pd.DataFrame:
    """단일 TE xlsx → 롱포맷 DataFrame (연도 시트 전체)."""
    parsed = _parse_filename(path.stem)
    if parsed is None:
        print(f"  [건너뜀] 파일명 규칙 불일치: {path.name}")
        return pd.DataFrame()
    commodity, exchange, unit = parsed
    category = _classify(commodity, path.parent.name)
    code = _indicator_code(commodity)

    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        print(f"  [오류] 엑셀 열기 실패 {path.name}: {e}")
        return pd.DataFrame()

    rows: list[pd.DataFrame] = []
    for sheet in xl.sheet_names:
        m = _YEAR_SHEET_RE.search(str(sheet))
        if not m:
            continue
        year = int(m.group(1))
        try:
            df = xl.parse(sheet)
        except Exception as e:
            print(f"    [경고] 시트 파싱 실패 {path.name}:{sheet}: {e}")
            continue
        if df.empty or not {"Month", "Day"}.issubset(df.columns):
            continue
        close_col = next((c for c in ("Close", "close", "Price", "value") if c in df.columns), None)
        if close_col is None:
            continue
        sub = df[["Month", "Day"]].copy()
        sub["year"] = year
        sub["price_date"] = pd.to_datetime(
            dict(year=sub["year"], month=sub["Month"], day=sub["Day"]),
            errors="coerce",
        )
        sub["value"] = pd.to_numeric(df[close_col], errors="coerce")
        for col in ("Open", "High", "Low"):
            sub[col.lower()] = pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.NA
        sub = sub.dropna(subset=["price_date", "value"])
        sub = _fix_sheet_ordering(sub, f"{path.stem} {sheet}")
        rows.append(sub[["price_date", "value", "open", "high", "low"]])

    if not rows:
        print(f"  [경고] 유효 데이터 없음: {path.name}")
        return pd.DataFrame()

    out = pd.concat(rows, ignore_index=True)
    out["indicator_code"] = code
    out["commodity"]      = commodity
    out["category"]       = category
    out["unit"]           = unit
    out["exchange"]       = exchange or "N/A"
    out["source_name"]    = "TradingEconomics_history_xlsx"
    out["ingested_at"]    = pd.Timestamp.now("UTC")
    return out.sort_values("price_date").reset_index(drop=True)


def apply_corrections(df: pd.DataFrame, path: Path = CORRECTIONS_PATH) -> pd.DataFrame:
    """공식 정산가 대조 정정 오버레이 적용 (A-290). 원본 xlsx는 건드리지 않는다.

    replace: value 교체 + 시가·고가·저가 결측화(다른 월물의 봉이라 쓸 수 없음) · drop: 행 제거.
    원본 값이 기대(te_value)와 다르면 원본이 이미 바뀐 것이므로 적용하지 않고 경고한다.
    """
    import yaml
    if not path.exists():
        return df
    spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    df = df.copy()
    for code, items in spec.items():
        for it in items or []:
            mask = (df["indicator_code"] == code) & (df["price_date"] == pd.Timestamp(it["date"]))
            if not mask.any():
                print(f"  [경고] 정정 대상 없음: {code} {it['date']}")
                continue
            cur = float(df.loc[mask, "value"].iloc[0])
            if abs(cur - float(it["te_value"])) > 0.5:
                print(f"  [경고] 정정 보류: {code} {it['date']} 원본 {cur} ≠ 기대 {it['te_value']} — 원본 갱신 여부 확인")
                continue
            if it["action"] == "drop":
                df = df[~mask]
            else:
                df.loc[mask, "value"] = float(it["value"])
                df.loc[mask, ["open", "high", "low"]] = pd.NA
                df.loc[mask, "source_name"] = "Bursa_settlement_correction"
            print(f"  [정정] {code} {it['date']}: {cur:,.0f} → "
                  f"{'결측' if it['action'] == 'drop' else format(float(it['value']), ',.0f')} ({it['label']})")
    return df


def flag_reversal_spikes(df: pd.DataFrame, code: str = "TE_PALM_OIL",
                         days: int = 120) -> list[str]:
    """최근 구간에서 '급변 후 같은 크기로 되돌림'(월물 혼입 의심) 일자를 찾는다 — 정정 목록에 없으면 경고만(A-290)."""
    import numpy as np
    s = df[df["indicator_code"] == code].set_index("price_date")["value"].sort_index().tail(days + 60)
    r = np.log(s.astype(float)).diff()
    sd = r.rolling(60, min_periods=20).std().shift(1)
    out = [str(d.date()) for i, d in enumerate(r.index[:-1])
           if pd.notna(sd.iloc[i]) and abs(r.iloc[i]) > 3 * sd.iloc[i]
           and abs(r.iloc[i + 1]) > 2.5 * sd.iloc[i] and np.sign(r.iloc[i]) != np.sign(r.iloc[i + 1])]
    return out[-10:]


def run() -> None:
    files = _iter_te_files()
    if not files:
        print("[경고] TE xlsx 없음 (폴더/루트 모두 비어 있음).")
        return
    print(f"[C-03] Trading Economics {len(files)}개 파일 정형화 중...")
    frames = []
    for f in files:
        df = parse_te_file(f)
        if not df.empty:
            frames.append(df)
            print(f"  [OK] {f.name}: {len(df):,}행 "
                  f"({df['price_date'].min().date()}~{df['price_date'].max().date()})")

    if not frames:
        print("[경고] 정형화된 데이터 없음.")
        return

    combined = apply_corrections(pd.concat(frames, ignore_index=True))
    suspects = flag_reversal_spikes(combined)
    if suspects:
        print(f"  [경고] 팜유 급변·되돌림 의심일(공식 정산가 대조 필요 — config/te_price_corrections.yaml): {suspects}")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # D-023: 저장 직전 as-of 5필드 부여 — 규칙은 src/pipeline/asof.py 단일 관리
    combined = attach_asof(combined, source="TE_")
    combined.to_parquet(OUT_PATH, index=False)

    print(f"\n[완료] → {OUT_PATH}")
    print(f"  총 {len(combined):,}행 · 지표 {combined['indicator_code'].nunique()}종 "
          f"· 기간 {combined['price_date'].min().date()}~{combined['price_date'].max().date()}")
    by_cat = combined.groupby("category")["indicator_code"].nunique()
    for cat, n in by_cat.items():
        print(f"  - {cat}: {n}종")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 단일 파일 테스트 모드
        out = parse_te_file(Path(sys.argv[1]))
        print(out.head(10).to_string())
        print(f"... 총 {len(out)}행")
    else:
        run()
