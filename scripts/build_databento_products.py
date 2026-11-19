#!/usr/bin/env python3
"""
Databento GLBX.MDP3 대두 복합체(ZL·ZM·ZS) 상품별 정리 — 2026-11-18 승인자 요청.

입력(승인자 포털 다운로드, parent 심볼 ZL.FUT·ZM.FUT·ZS.FUT — 개별 월물 + 스프레드 + 콤보 혼재):
  OHLCV-1d/{ZL,ZM,ZS}/          일봉(ZL은 xlsx, ZM·ZS는 csv)
  Definitions/GLBX-*/*.zst      일별 상품 정의(만기·월물·승수)
  Statistics/GLBX-*/*.zst       일별 통계(정산가·미결제약정·청산 거래량 등)

출력(원본은 수정·삭제하지 않음):
  OHLCV-1d/{X}/clean/{X}_ohlcv-1d_outright_{시작}_{끝}.csv(+.xlsx)   단일 월물만
  OHLCV-1d/{X}/clean/{X}_front_by_prior_volume.csv                   전일 거래량 순위 1~3위 월물 + 롤 플래그
  OHLCV-1d/{X}/clean/removal_log.md                                  제거 항목·사유·행 수
  Definitions/{X}/{X}_definitions_outright.csv                       월물별 정의 1행
  Statistics/{X}/{X}_statistics_daily_outright.csv                   거래일×월물 정산가·미결제약정·청산 거래량

사용: python scripts/build_databento_products.py   (러너 컨테이너, 저장소 루트)
"""
from __future__ import annotations

import glob
import io
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import zstandard

BASE = Path(os.environ.get("DATABENTO_ROOT", "data/raw/Databento/GLBX.MDP3"))
PRODUCTS = ("ZL", "ZM", "ZS")
OHLCV_INPUT = {
    "ZL": "OHLCV-1d/ZL/ZL_ohlcv-1d_2010-06-06_2026-11-15.xlsx",
    "ZM": "OHLCV-1d/ZM/ZM_ohlcv-1d_2010-06-06_2026-11-16.csv",
    "ZS": "OHLCV-1d/ZS/ZS_ohlcv-1d_2010-06-06_2026-11-16.csv",
}
MONTH_CODES = "FGHJKMNQUVXZ"
OUTRIGHT = re.compile(r"^(ZL|ZM|ZS)([FGHJKMNQUVXZ])(\d{1,2})$")
CONTINUOUS = re.compile(r"^(ZL|ZM|ZS)\.[cvn]\.\d+$")
# Databento StatType — 보존 대상만(1·2·4·5·7·8·17·18 등 장중·호가·가격제한 통계는 일별 패널에 불필요)
STAT_SETTLEMENT, STAT_CLEARED_VOLUME, STAT_OPEN_INTEREST = 3, 6, 9
SETTLEMENT_FINAL_BIT = 1        # CME stat_flags bit0 = 최종(final) 정산 — 미설정 시 잠정
DROP_COLUMNS = {
    "rtype": "전 행 35(OHLCV-1d 레코드 타입 상수) — 정보 없음",
    "publisher_id": "전 행 1(GLBX.MDP3 CME Globex 상수) — 정보 없음",
}
DEF_KEEP = ["instrument_id", "raw_symbol", "expiration", "activation", "maturity_year",
            "maturity_month", "min_price_increment", "min_price_increment_amount",
            "contract_multiplier", "unit_of_measure", "unit_of_measure_qty", "currency",
            "security_type", "instrument_class"]


def _kind(sym: str) -> str:
    """심볼 분류: outright(단일 월물) · spread(달력 스프레드, '-') · combo(':' 다리 묶음) · other."""
    if OUTRIGHT.match(sym):
        return "outright"
    if CONTINUOUS.match(sym):
        return "continuous"
    if ":" in sym or " " in sym:
        return "combo"
    if "-" in sym:
        return "spread"
    return "other"


def _contract_month(sym: pd.Series, ref_date: pd.Series) -> pd.Series:
    """월물 코드 → 인도월 YYYY-MM(연 1자리는 기준일 기준 가장 가까운 미래 10년대)."""
    m = sym.str.extract(OUTRIGHT)
    digits = m[2].astype(float)
    yr = (ref_date.dt.year // 10 * 10 + digits).where(m[2].str.len() == 1, 2000 + digits)
    yr = yr.where(yr >= ref_date.dt.year - 1, yr + 10)
    mon = m[1].map(lambda c: MONTH_CODES.index(c) + 1 if isinstance(c, str) else np.nan)
    return yr.astype("Int64").astype(str) + "-" + mon.astype("Int64").astype(str).str.zfill(2)


def _read_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, thousands=",") if path.suffix == ".csv" else pd.read_excel(path)
    df.columns = [c.lower() for c in df.columns]
    df["price_date"] = pd.to_datetime(df["ts_event"].astype(str).str[:10])
    df["symbol"] = df["symbol"].astype(str)
    return df


def clean_ohlcv(product: str) -> tuple[pd.DataFrame, list[str]]:
    """단일 월물만 남기고 제거 사유를 기록한다(원본 불변)."""
    src = BASE / OHLCV_INPUT[product]
    df = _read_ohlcv(src)
    log = [f"# {product} OHLCV-1d 정리 로그", "", f"- 원본: `{src.as_posix()}` · {len(df):,}행 · "
           f"{df.price_date.min().date()}~{df.price_date.max().date()} · 심볼 {df.symbol.nunique():,}종",
           "- 원본 파일은 수정·삭제하지 않음(이 폴더의 정리본만 생성)", "", "## 제거한 열", "",
           "| 열 | 사유 |", "|---|---|"]
    for col, why in DROP_COLUMNS.items():
        uniq = df[col].unique().tolist()
        if len(uniq) != 1:
            raise ValueError(f"[오류] {product} {col} 값이 상수가 아님({uniq[:5]}) — 제거 근거 붕괴")
        log.append(f"| `{col}` | {why} |")
    log.append("| `ts_event` | `price_date`(UTC 일자, YYYY-MM-DD)로 대체 — 시각 성분이 전 행 00:00으로 정보 없음 |")
    df["kind"] = df.symbol.map(_kind)
    log += ["", "## 제거한 행(심볼 유형별)", "", "| 유형 | 행 수 | 심볼 수 | 예시 | 사유 |", "|---|---|---|---|---|"]
    reasons = {
        "spread": "달력 스프레드 — 가격이 두 월물의 '차이'(음수 가능)라 가격 수준 계열과 혼합 불가. 필요 시 단일 월물에서 재계산",
        "combo": "다리 묶음(버터플라이·콘도르·스트립 등, 'ZL:BF …') — 다중 월물 패키지 가격이라 단일 가격 아님",
        "continuous": "연속 심볼(ZL.c.0 등, 만기 기준 롤) — 같은 날 단일 월물 행과 중복되고, 롤 직전 인도월(거래량 급감) 체결가를 담아 정본 계열 부적합. 연속 계열은 front_by_prior_volume 파일로 대체",
        "other": "분류 불가 심볼 — 단일 월물 규칙 불일치",
    }
    for k, why in reasons.items():
        sub = df[df.kind == k]
        if len(sub):
            ex = ", ".join(sub.symbol.drop_duplicates().head(3))
            log.append(f"| {k} | {len(sub):,} | {sub.symbol.nunique():,} | {ex} | {why} |")
    out = df[df.kind == "outright"].copy()
    sunday = out.price_date.dt.dayofweek == 6
    weekend_sat = out.price_date.dt.dayofweek == 5
    log.append(f"| 일요일 행(단일 월물) | {int(sunday.sum()):,} | {out[sunday].symbol.nunique():,} | "
               f"중앙 거래량 {out[sunday].volume.median() if sunday.any() else 0:.0f} vs 평일 "
               f"{out[~sunday].volume.median():.0f} | 일요일 저녁(Globex 개장) 세션 조각 — 다음 거래일 세션의 일부라 "
               f"독립 거래일로 쓰면 거래일 수·수익률 왜곡(기존 ZL 처리 A-131과 동일 규칙) |")
    if weekend_sat.any():
        log.append(f"| 토요일 행 | {int(weekend_sat.sum()):,} | - | - | 비거래일 |")
    out = out[~sunday & ~weekend_sat]
    dup = out.duplicated(["price_date", "symbol"], keep=False)
    if dup.any():
        log.append(f"| 중복(일자·심볼) | {int(dup.sum()):,} | - | - | 동일 키 중복 — 거래량 최대 행만 유지 |")
        out = out.sort_values("volume").drop_duplicates(["price_date", "symbol"], keep="last")
    bad = (out[["open", "high", "low", "close"]] <= 0).any(axis=1)
    if bad.any():
        log.append(f"| 비양수 가격(단일 월물) | {int(bad.sum()):,} | - | - | 단일 월물 가격은 양수여야 함 — 데이터 오류 |")
        out = out[~bad]
    out["contract_month"] = _contract_month(out.symbol, out.price_date)
    out = out[["price_date", "instrument_id", "symbol", "contract_month", "open", "high", "low",
               "close", "volume"]].sort_values(["price_date", "contract_month"]).reset_index(drop=True)
    log += ["", "## 결과", "", f"- 단일 월물 {len(out):,}행 · 월물 {out.symbol.nunique()}종 · 거래일 "
            f"{out.price_date.nunique():,}일 · {out.price_date.min().date()}~{out.price_date.max().date()}",
            "- ⚠️ 일봉은 UTC 일자 기준(CME 세션은 전일 저녁 개장) — 정산가는 Statistics 정리본(stat_type 3)을 사용"]
    return out, log


def front_by_prior_volume(out: pd.DataFrame) -> pd.DataFrame:
    """전일 거래량 순위로 당일 1~3위 월물 선택(당일 거래량 미사용 → 사후 정보 없음)."""
    vol = out.pivot_table(index="price_date", columns="symbol", values="volume", aggfunc="sum").sort_index()
    px = out.pivot_table(index="price_date", columns="symbol", values="close", aggfunc="last").reindex(vol.index)
    prior = vol.shift(1)
    rows = []
    for d in vol.index[1:]:
        traded = px.loc[d].dropna().index
        ranked = prior.loc[d, traded].dropna().sort_values(ascending=False)
        rec = {"price_date": d}
        for r, sym in enumerate(ranked.index[:3], start=1):
            rec[f"rank{r}_symbol"] = sym
            rec[f"rank{r}_close"] = px.at[d, sym]
            rec[f"rank{r}_volume"] = vol.at[d, sym]
            rec[f"rank{r}_prior_volume"] = ranked[sym]
        rows.append(rec)
    fr = pd.DataFrame(rows)
    fr["roll_flag"] = fr.rank1_symbol.ne(fr.rank1_symbol.shift()) & fr.rank1_symbol.shift().notna()
    # 동일 월물 수익률만 유효 — 롤일 수익률은 월물 전환 점프라 결측 처리
    same = fr.rank1_symbol.eq(fr.rank1_symbol.shift())
    prev_same = [px.at[fr.price_date.iloc[i - 1], s] if i and same.iloc[i] else np.nan
                 for i, s in enumerate(fr.rank1_symbol)]
    fr["rank1_ret_same_contract"] = fr.rank1_close / pd.Series(prev_same) - 1
    return fr


def _iter_zst(kind: str) -> list[str]:
    """배치 폴더의 일별 .csv.zst + 승인자가 풀어 둔 초기 일자 .csv(폴더 최상위)를 일자당 1개로 합친다."""
    zst = glob.glob(str(BASE / kind / "GLBX-*" / "*.csv.zst"))
    loose = glob.glob(str(BASE / kind / "glbx-mdp3-*.csv"))
    by_day: dict[str, str] = {}
    for f in sorted(loose) + sorted(zst):          # 같은 일자는 배치(zst) 우선
        by_day[Path(f).name.split(".")[0]] = f
    if not by_day:
        raise FileNotFoundError(f"[오류] {kind} 일별 파일 없음 — {BASE / kind}")
    return [by_day[k] for k in sorted(by_day)]


def _read_zst(path: str, usecols: list[str] | None = None) -> pd.DataFrame:
    if not path.endswith(".zst"):
        return pd.read_csv(path, usecols=usecols, low_memory=False)
    with open(path, "rb") as fh:
        raw = zstandard.ZstdDecompressor().stream_reader(fh).read()
    return pd.read_csv(io.BytesIO(raw), usecols=usecols, low_memory=False)


def build_statistics() -> dict[str, pd.DataFrame]:
    cols = ["ts_event", "ts_ref", "instrument_id", "price", "quantity", "stat_type",
            "update_action", "stat_flags", "symbol"]
    keep, counts = [], {p: {"outright": 0, "spread": 0, "combo": 0, "continuous": 0, "other": 0} for p in PRODUCTS}
    for f in _iter_zst("Statistics"):
        d = _read_zst(f, cols)
        d = d[d.stat_type.isin([STAT_SETTLEMENT, STAT_CLEARED_VOLUME, STAT_OPEN_INTEREST])
              & (d.update_action == 1)]
        d["symbol"] = d.symbol.astype(str)
        d["product"] = d.symbol.str[:2]
        d["kind"] = d.symbol.map(_kind)
        for (p, k), n in d.groupby(["product", "kind"]).size().items():
            if p in counts:
                counts[p][k] += int(n)
        keep.append(d[d.kind == "outright"])
    s = pd.concat(keep, ignore_index=True)
    ref = pd.to_datetime(s.ts_ref.astype(str).str[:10], errors="coerce")
    s["trade_date_imputed"] = ref.isna()
    s["trade_date"] = ref.fillna(pd.to_datetime(s.ts_event.astype(str).str[:10]))
    s["ts_event"] = pd.to_datetime(s.ts_event, utc=True)
    s["final"] = (s.stat_flags.fillna(0).astype(int) & SETTLEMENT_FINAL_BIT) > 0
    s = s.sort_values(["final", "ts_event"])  # 최종 정산 우선, 그다음 최신
    last = s.drop_duplicates(["product", "symbol", "trade_date", "stat_type"], keep="last")
    out = {}
    for p in PRODUCTS:
        z = last[last["product"] == p]
        base = z[["trade_date", "instrument_id", "symbol"]].drop_duplicates(["trade_date", "symbol"])
        def pick(t: int, col: str, name: str) -> pd.DataFrame:
            q = z[z.stat_type == t][["trade_date", "symbol", col, "stat_flags", "trade_date_imputed"]]
            return q.rename(columns={col: name, "stat_flags": f"{name}_flags",
                                     "trade_date_imputed": f"{name}_date_from_ts_event"})
        t = (base.merge(pick(STAT_SETTLEMENT, "price", "settlement"), on=["trade_date", "symbol"], how="left")
                 .merge(pick(STAT_OPEN_INTEREST, "quantity", "open_interest"), on=["trade_date", "symbol"], how="left")
                 .merge(pick(STAT_CLEARED_VOLUME, "quantity", "cleared_volume"), on=["trade_date", "symbol"], how="left"))
        t = t[t.trade_date.dt.dayofweek < 5].sort_values(["trade_date", "symbol"]).reset_index(drop=True)
        t.attrs["counts"] = counts[p]
        out[p] = t
    return out


def build_definitions() -> dict[str, pd.DataFrame]:
    parts, counts = [], {p: {} for p in PRODUCTS}
    for f in _iter_zst("Definitions"):
        d = _read_zst(f)
        d["raw_symbol"] = d.raw_symbol.astype(str)
        d["product"] = d.raw_symbol.str[:2]
        d["kind"] = d.raw_symbol.map(_kind)
        d["file_date"] = pd.to_datetime(Path(f).name.split(".")[0].split("-")[-1])
        parts.append(d[d.kind == "outright"][DEF_KEEP + ["product", "file_date"]])
        for (p, k), n in d.drop_duplicates("instrument_id").groupby(["product", "kind"]).size().items():
            if p in counts:
                counts[p][k] = counts[p].get(k, 0) + int(n)
    d = pd.concat(parts, ignore_index=True).sort_values("file_date")
    span = d.groupby("instrument_id").file_date.agg(first_seen="min", last_seen="max")
    last = d.drop_duplicates("instrument_id", keep="last").set_index("instrument_id").join(span).reset_index()
    out = {}
    for p in PRODUCTS:
        t = last[last["product"] == p].drop(columns=["product", "file_date"]).sort_values("expiration")
        t.attrs["counts"] = counts[p]
        out[p] = t.reset_index(drop=True)
    return out


def main() -> None:
    summary = []
    for p in PRODUCTS:
        out, log = clean_ohlcv(p)
        d = BASE / "OHLCV-1d" / p / "clean"
        d.mkdir(parents=True, exist_ok=True)
        stem = f"{p}_ohlcv-1d_outright_{out.price_date.min().date()}_{out.price_date.max().date()}"
        o = out.assign(price_date=out.price_date.dt.strftime("%Y-%m-%d"))
        o.to_csv(d / f"{stem}.csv", index=False)
        o.to_excel(d / f"{stem}.xlsx", index=False)   # 승인자 열람용 사본(정본은 csv)
        fr = front_by_prior_volume(out)
        fr.assign(price_date=fr.price_date.dt.strftime("%Y-%m-%d")).to_csv(d / f"{p}_front_by_prior_volume.csv", index=False)
        log += ["", "## 거래량 순위 월물(별도 파일)", "",
                f"- `{p}_front_by_prior_volume.csv`: 전일 거래량 1~3위 월물(당일 거래 있는 월물 중) · 롤 {int(fr.roll_flag.sum())}회",
                "- `rank1_ret_same_contract`: 같은 월물 전일 대비 수익률(롤일은 결측 — 월물 전환 점프 제외)"]
        (d / "removal_log.md").write_text("\n".join(log) + "\n", encoding="utf-8")
        summary.append(f"[완료] {p} 단일 월물 {len(out):,}행 · 롤 {int(fr.roll_flag.sum())}회 → {d}")
    for p, t in build_definitions().items():
        d = BASE / "Definitions" / p
        d.mkdir(parents=True, exist_ok=True)
        t.to_csv(d / f"{p}_definitions_outright.csv", index=False)
        summary.append(f"[완료] {p} 정의 단일 월물 {len(t)}종 · 원천 고유 상품 수(유형별) {t.attrs['counts']}")
    for p, t in build_statistics().items():
        d = BASE / "Statistics" / p
        d.mkdir(parents=True, exist_ok=True)
        t.assign(trade_date=t.trade_date.dt.strftime("%Y-%m-%d")).to_csv(d / f"{p}_statistics_daily_outright.csv", index=False)
        summary.append(f"[완료] {p} 통계 {len(t):,}행 · {t.trade_date.min().date()}~{t.trade_date.max().date()} · "
                       f"정산가 {t.settlement.notna().sum():,} · 미결제약정 {t.open_interest.notna().sum():,} · "
                       f"원천 레코드(유형별) {t.attrs['counts']}")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
