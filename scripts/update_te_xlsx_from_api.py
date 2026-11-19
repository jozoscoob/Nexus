#!/usr/bin/env python3
"""Trading Economics API → 기존 수동 xlsx(연도 시트 × Month/Day/Open/High/Low/Close) 증분 갱신 (A-248).

배경: 승인자가 수동 업로드본 26파일을 2026-09-10까지 직접 갱신했고, 그 이후 일자는 API로
매일 1행씩 덧붙인다. 기존 파일 형식·경로를 그대로 유지하며 **마지막 일자 이후 행만 append**한다.

모드:
  - `snapshot`(기본, 일별): `/markets/symbol/{sym}` 스냅샷 1건을 받아 당일 종가 1행을 append한다.
    historical 엔드포인트가 월별 표본만 반환한 실측(A-249) 때문에 일별 경로는 스냅샷으로 둔다.
  - `historical`(공백 복구): `/markets/historical/{sym}` 창 조회. 며칠 이상 빠진 파일을 메울 때만
    수동 dispatch로 실행한다(밀도·점프 게이트 유지).

규약:
  - 심볼은 자기발견(A-150 — /markets/search → :COM/:IND 우선 A-159) + REGISTRY의 고정 심볼 우선.
  - historical 엔드포인트 409/403은 '플랜 미포함'으로 판정해 파일을 건드리지 않고 보고만 한다(A-140).
  - 스로틀(409/429/"slow down") 확인 시 남은 파일 호출을 **즉시 중단**한다(A-105·A-112 — 실패 처리가
    스로틀을 자초하던 구조 반복 금지). 비치명 종료.
  - 새 연도 시트는 원본 헤더(Month|Day|Open|High|Low|Close)를 복제해 생성. 내림차순 시트는 상단 삽입.
  - 갱신 전 원본을 `.bak` 없이 임시 사본에 쓰고, 재판독 검증(시트 수·마지막 일자 진전)을 통과할
    때만 교체한다(A-109 .partial 가드와 동일 원리).
  - 샌드박스는 api.tradingeconomics.com 차단 — GitHub Actions(te_xlsx_update.yml)에서 실행한다.

사용: python scripts/update_te_xlsx_from_api.py [--mode snapshot|historical] [--repair-gap] [--dry-run]
      [--only "Soybeans,BDI"]
출력: xlsx 갱신 + reports/market/te_api_update_{date}.md
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import httpx
import pandas as pd
from openpyxl import load_workbook

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

TE_ROOT = Path("data/raw/Trading Economics/Markets/Commodities")
REPORT_DIR = Path("reports/market")
_YEAR_SHEET_RE = re.compile(r"(\d{4})\s*년")
HEADER = ["Month", "Day", "Open", "High", "Low", "Close"]
THROTTLE = ("slow down", "throttle", "too many")
MIN_DENSITY = 0.6      # 응답 행 수 / 요청 창 영업일 수 — 미만이면 일별 관측이 아니라고 판정(A-249)
MAX_JUMP = 0.30        # 기존 마지막 종가 대비 첫 신규 종가 변동률 상한 — 초과 시 계약·집계 혼입 의심(A-249)
SYMBOL_PACING_S = 0.5  # 심볼 호출 간 간격 — 26파일 × 1~2심볼 ≈ 26~52회(A-105 스로틀 자초 방지)
MODES = ("snapshot", "historical")

# 스냅샷 응답 컬럼 후보(A-027/A-034 실측 — 심볼·플랜에 따라 일부만 옴)
_SNAP_DATE_KEYS = ("DateTime", "Date", "datetime", "date")
_SNAP_CLOSE_KEYS = ("Last", "last", "Close", "close")   # Close는 '전일 종가'일 수 있어 Last 우선
_SNAP_OPEN_KEYS = ("Open", "open")
_SNAP_HIGH_KEYS = ("DayHigh", "High", "dayHigh", "high")
_SNAP_LOW_KEYS = ("DayLow", "Low", "dayLow", "low")

# 파일명 품목 → (검색어, 이름 키워드, 고정 심볼 후보). 고정 심볼은 자기발견 실패 시 폴백.
# 검색어는 str 또는 tuple[str, ...] — 여러 개면 순서대로 시도한다(2026-09-13: 고정 심볼 TTF:COM·WCI:IND·
#   DAP:COM이 빈 스냅샷을 반환하고 단일 검색어가 :COM/:IND 필터 뒤 0건이라 다중 검색어 폴백 도입).
SearchTerms = str | tuple[str, ...]
REGISTRY: dict[str, tuple[SearchTerms, tuple[str, ...], tuple[str, ...]]] = {
    "Soybeans":      ("soybeans", ("soybean",), ("S 1:COM",)),
    "Corn":          ("corn", ("corn",), ("C 1:COM",)),
    "Wheat":         ("wheat", ("wheat",), ("W 1:COM",)),
    "Palm Oil":      ("palm oil", ("palm",), ("PLO:COM",)),
    "Canola":        ("canola", ("canola",), ("RS1:COM",)),
    "Rapeseed":      ("rapeseed", ("rapeseed",), ("RSD:COM",)),
    "Sunflower Oil": ("sunflower oil", ("sunflower",), ()),
    "Sugar":         ("sugar", ("sugar",), ("SB1:COM",)),
    "Brent Crude Oil": ("brent", ("brent",), ("CO1:COM",)),
    "WTI Crude Oil": ("crude oil", ("crude", "wti"), ("CL1:COM",)),
    "Coal":          ("coal", ("coal",), ("XAL1:COM",)),
    "Natural Gas":   ("natural gas", ("natural", "gas"), ("NG1:COM",)),
    "EU Natural Gas": (("ttf", "eu natural gas", "dutch ttf"), ("ttf",), ("TTF:COM",)),
    "UK Natural Gas": ("uk gas", ("uk", "gas"), ("NBP:COM",)),
    "Gasoline":      ("gasoline", ("gasoline",), ("XB1:COM",)),
    "Heating Oil":   ("heating oil", ("heating",), ("HO1:COM",)),
    "Naphtha":       ("naphtha", ("naphtha",), ("NAPHTHA:COM",)),
    "Ethanol":       ("ethanol", ("ethanol",), ("ETHANOL:COM",)),
    "Urea":          ("urea", ("urea",), ("UREA:COM",)),
    "Di-ammonium":   (("dap", "diammonium", "di-ammonium phosphate", "phosphate"), ("dap",),
                      ("DAP:COM",)),
    "BDI":           ("baltic dry", ("baltic", "dry"), ("BDIY:IND",)),
    "CRB Index":     ("crb", ("crb",), ("CRY:IND",)),
    "GSCI":          ("gsci", ("gsci",), ("SPGSCI:IND",)),
    "EU Carbon Permits": ("carbon", ("carbon",), ("EECXM:IND",)),
    "Containerized Freight Index": ("containerized freight", ("container",), ("CFI:IND",)),
    "Drewry World Container Index": (("drewry", "world container index", "container"), ("drewry",),
                                     ("WCI:IND",)),
}


def search_terms_of(commodity: str) -> tuple[str, ...]:
    """REGISTRY 검색어를 항상 tuple로 정규화(str 단일 검색어 하위 호환)."""
    term = REGISTRY.get(commodity, (commodity.lower(), (), ()))[0]
    return (term,) if isinstance(term, str) else tuple(term)


def _commodity_of(path: Path) -> str:
    parts = path.stem.split("_")
    return parts[1].strip() if len(parts) >= 3 else path.stem


def _read_last_date(path: Path) -> tuple[date | None, bool]:
    """마지막 관측일과 시트 정렬 방향(내림차순 여부)."""
    wb = load_workbook(path, read_only=True, data_only=True)
    years = sorted((int(m.group(1)), n) for n in wb.sheetnames if (m := _YEAR_SHEET_RE.search(n)))
    if not years:
        return None, False
    ws = wb[years[-1][1]]
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0] is not None and r[1] is not None]
    if not rows:
        return date(years[-1][0], 1, 1) - timedelta(days=1), False
    first, last = rows[0], rows[-1]
    desc = (int(first[0]), int(first[1])) > (int(last[0]), int(last[1]))
    m, d = (first if desc else last)[:2]
    return date(years[-1][0], int(m), int(d)), desc


def _read_last_close(path: Path) -> float | None:
    """마지막 관측 행의 Close(정렬 방향 자동)."""
    last, desc = _read_last_date(path)
    if last is None:
        return None
    ws = load_workbook(path, read_only=True, data_only=True)[f"{last.year}년"]
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0] is not None and r[1] is not None]
    if not rows:
        return None
    row = rows[0] if desc else rows[-1]
    try:
        return float(row[5])
    except (TypeError, ValueError, IndexError):
        return None


def _te_get(url: str, params: dict, timeout: int = 30) -> httpx.Response:
    return httpx.get(url, params=params, timeout=timeout)


def discover_symbols(te_key: str, commodity: str) -> list[str]:
    """심볼 후보 목록 — 고정 심볼 → 검색어별 /markets/search(순서대로) → /markets/commodities.

    검색어는 여러 개일 수 있으며 첫 매칭이 나오는 검색어에서 멈춘다. 이름 매칭은 키워드 전부 포함
    또는 검색어 자체 포함(예: 'eu natural gas' ⊂ 'EU Natural Gas TTF') 중 하나면 통과한다.
    """
    _, kws, fixed = REGISTRY.get(commodity, (commodity.lower(), (commodity.lower(),), ()))
    terms = search_terms_of(commodity)
    found: list[str] = []
    urls = [(t, f"https://api.tradingeconomics.com/markets/search/{quote(t)}") for t in terms]
    urls.append(("", "https://api.tradingeconomics.com/markets/commodities"))
    for term, url in urls:
        try:
            r = _te_get(url, {"c": te_key})
            if r.status_code != 200:
                continue
            data = r.json()
            for item in data if isinstance(data, list) else []:
                name = str(item.get("Name") or item.get("name") or "").lower()
                kw_hit = bool(kws) and all(k.lower() in name for k in kws)
                term_hit = bool(term) and term.lower() in name
                if kw_hit or term_hit:
                    sym = item.get("Symbol") or item.get("symbol")
                    if sym and str(sym) not in found:
                        found.append(str(sym))
            if found:
                if term:
                    print(f"[정보] TE 심볼 검색 매칭({commodity}): 검색어 '{term}' → {found}")
                break
        except Exception as e:  # noqa: BLE001
            print(f"[정보] TE 심볼 검색 실패({commodity}, '{term or 'commodities'}'): {e}")
    # A-159 우선 정렬 + A-256 첫 라이브 런 교훈: 비상품 접미(:HB 등)는 다른 상품(BIF:HB → DAP -64%)을
    #   집어 점프 게이트에만 걸리므로 :COM/:IND 외 심볼은 후보에서 제외한다.
    found = [x for x in found if x.endswith((":COM", ":IND"))]
    found.sort(key=lambda x: (0 if x.endswith(":COM") else 1))
    return list(dict.fromkeys((*fixed, *found)))


def fetch_history(te_key: str, symbols: list[str], d1: date, d2: date) -> tuple[pd.DataFrame, str]:
    """→ (DataFrame[date,open,high,low,close], 상태) 상태 ∈ ok | plan | empty | error."""
    last_status = "empty"
    for sym in symbols:
        r = _te_get(f"https://api.tradingeconomics.com/markets/historical/{quote(sym, safe=':')}",
                    {"c": te_key, "d1": d1.isoformat(), "d2": d2.isoformat(), "f": "json"})
        if r.status_code in (403, 409) or any(t in r.text.lower() for t in THROTTLE):
            print(f"[정보] TE historical {r.status_code} ({sym}) — 플랜 미포함/스로틀 추정")
            return pd.DataFrame(), "plan"
        if r.status_code != 200:
            print(f"[정보] TE historical HTTP {r.status_code} ({sym}) — 다음 심볼")
            last_status = "error"
            continue
        data = r.json()
        if not isinstance(data, list) or not data:
            continue
        raw = pd.DataFrame(data)
        dcol = next((c for c in ("Date", "DateTime", "date") if c in raw.columns), None)
        ccol = next((c for c in ("Close", "Last", "close") if c in raw.columns), None)
        if not dcol or not ccol:
            continue
        out = pd.DataFrame({
            "date": pd.to_datetime(raw[dcol], errors="coerce").dt.normalize(),
            "open": pd.to_numeric(raw.get("Open"), errors="coerce"),
            "high": pd.to_numeric(raw.get("High"), errors="coerce"),
            "low": pd.to_numeric(raw.get("Low"), errors="coerce"),
            "close": pd.to_numeric(raw[ccol], errors="coerce"),
        }).dropna(subset=["date", "close"])
        out = out[(out["date"].dt.date > d1) & (out["date"].dt.date <= d2)]   # 요청 창 밖·미래 행 차단(A-246)
        if out.empty:
            continue
        out = out.sort_values("date").drop_duplicates("date")
        # A-249 밀도 게이트: 첫 실행(2026-09-07) 실측 — 2개월 창에 4~5행(7/7·7/8·8/7·9/7)만 반환되고
        #   값이 하루 만에 BDI 735→2,875·Brent 71→97로 점프. 일별 관측이 아닌 표본(월별·다른 집계)을
        #   연도 시트에 섞으면 표준화 지수 경보가 오염되므로, 영업일 대비 밀도가 낮으면 거부한다.
        bdays = len(pd.bdate_range(d1, d2)) - 1
        density = len(out) / max(bdays, 1)
        if bdays >= 5 and density < MIN_DENSITY:
            print(f"[경고] TE historical {sym}: 밀도 {density:.0%}({len(out)}/{bdays} 영업일) < {MIN_DENSITY:.0%} — "
                  f"일별 관측 아님(표본/집계 의심) → 파일 미갱신")
            return out, "sparse"
        print(f"[완료] TE historical {len(out)}행 ({sym}, {d1}~{d2}, 밀도 {density:.0%})")
        return out, "ok"
    return pd.DataFrame(), last_status


def _pick(rec: dict, keys: tuple[str, ...]) -> object | None:
    """응답 레코드에서 후보 키 중 첫 유효값(빈 문자열·None 제외)."""
    for k in keys:
        if k in rec and rec[k] not in (None, ""):
            return rec[k]
    return None


def _parse_snapshot(rec: dict, last_date: date | None = None,
                    today: date | None = None) -> tuple[dict | None, list[str], str]:
    """스냅샷 레코드 1건 → ({date,open,high,low,close}, 응답 컬럼 목록, 상태).

    상태: ok | fields(날짜·종가 컬럼 없음) | stale(파일 마지막 일자 이하) | future | weekend.
    수용 조건은 세 가지뿐이다 — 파일 마지막 일자 초과 · 오늘 이하 · 평일(월~금).
    `date == today`도 수용한다: 워크플로우가 **미국 장 마감 이후(21:30 UTC = KST 06:30)** 에만
    돌기 때문에 당일 값은 이미 확정 종가다(그 전 시각에 수동 실행하면 장중값이 들어갈 수 있음).
    """
    cols = sorted(rec.keys()) if isinstance(rec, dict) else []
    if not isinstance(rec, dict):
        return None, cols, "fields"
    raw_date, raw_close = _pick(rec, _SNAP_DATE_KEYS), _pick(rec, _SNAP_CLOSE_KEYS)
    if raw_date is None or raw_close is None:
        return None, cols, "fields"
    ts = pd.to_datetime(raw_date, errors="coerce", utc=False)
    close = pd.to_numeric(pd.Series([raw_close]), errors="coerce").iloc[0]
    if pd.isna(ts) or pd.isna(close):
        return None, cols, "fields"
    obs = ts.date() if hasattr(ts, "date") else None
    if obs is None:
        return None, cols, "fields"
    ref = today or date.today()
    if obs > ref:
        return None, cols, "future"
    if obs.weekday() >= 5:                      # 토·일 스탬프 = 주말 스냅샷 잔상
        return None, cols, "weekend"
    if last_date is not None and obs <= last_date:
        return None, cols, "stale"

    def _num(keys: tuple[str, ...]) -> float:
        v = _pick(rec, keys)
        if v is None:
            return float("nan")
        return float(pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0])

    row = {"date": obs, "open": _num(_SNAP_OPEN_KEYS), "high": _num(_SNAP_HIGH_KEYS),
           "low": _num(_SNAP_LOW_KEYS), "close": float(close)}
    return row, cols, "ok"


def fetch_snapshot(te_key: str, symbols: list[str], last_date: date | None,
                   today: date) -> tuple[dict | None, str, str, list[str]]:
    """심볼을 차례로 조회해 첫 유효 스냅샷 1건을 반환.

    → (행, 상태, 사용 심볼, 마지막 응답 컬럼). 상태 ∈ ok | empty | fields | stale | weekend |
      future | throttle | error. throttle이면 호출부는 남은 파일을 중단해야 한다(A-105).
    """
    status, cols = "empty", []
    for i, sym in enumerate(symbols):
        if i:
            time.sleep(SYMBOL_PACING_S)
        try:
            r = _te_get(f"https://api.tradingeconomics.com/markets/symbol/{quote(sym, safe=':')}",
                        {"c": te_key, "f": "json"})
        except Exception as e:  # noqa: BLE001
            print(f"[경고] TE 스냅샷 요청 실패({sym}): {e}")
            status = "error"
            continue
        if r.status_code in (409, 429) or any(t in r.text.lower() for t in THROTTLE):
            print(f"[경고] TE 스냅샷 스로틀 HTTP {r.status_code} ({sym}) — 이번 실행 중단")
            return None, "throttle", sym, cols
        if r.status_code != 200:
            print(f"[정보] TE 스냅샷 HTTP {r.status_code} ({sym}) — 다음 심볼")
            status = "error"
            continue
        try:
            data = r.json()
        except Exception as e:  # noqa: BLE001
            print(f"[경고] TE 스냅샷 JSON 파싱 실패({sym}): {e}")
            status = "error"
            continue
        records = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        if not records:
            status = "empty"
            continue
        row, cols, st = _parse_snapshot(records[0], last_date, today)   # 첫 레코드만 사용
        if st == "ok" and row is not None:
            print(f"[완료] TE 스냅샷 {sym}: {row['date']} 종가 {row['close']}")
            return row, "ok", sym, cols
        if st == "fields":
            print(f"[경고] TE 스냅샷 {sym}: 날짜/종가 컬럼 없음 — 응답 컬럼 {cols}")
        else:
            print(f"[정보] TE 스냅샷 {sym}: 행 제외({st}) — 파일 마지막 {last_date}, 오늘 {today}")
        status = st
    return None, status, symbols[0] if symbols else "", cols


def append_rows(path: Path, rows: pd.DataFrame, desc: bool) -> int:
    """rows(date/open/high/low/close)를 연도 시트에 append. 반환: 추가 행 수."""
    wb = load_workbook(path)
    added = 0
    for year, grp in rows.groupby(rows["date"].dt.year):
        name = f"{year}년"
        if name not in wb.sheetnames:
            ws = wb.create_sheet(name)
            ws.append(HEADER)
        ws = wb[name]
        recs = [[int(d.month), int(d.day), o, h, l, c] for d, o, h, l, c in
                grp[["date", "open", "high", "low", "close"]].itertuples(index=False)]
        recs = [[m, dd] + [None if pd.isna(v) else float(v) for v in vals] for m, dd, *vals in recs]
        if desc:   # 내림차순 시트: 오름차순으로 순회하며 매번 2행에 삽입 → 최신이 최상단
            for rec in recs:
                ws.insert_rows(2)
                for j, v in enumerate(rec, start=1):
                    ws.cell(2, j, v)
        else:
            for rec in recs:
                ws.append(rec)
        added += len(recs)
    wb.save(path)
    return added


def _validate(orig: Path, cand: Path) -> tuple[bool, str]:
    """재판독 검증 — 행 수 증가·마지막 일자 진전·시트 수 유지 이상."""
    a, _ = _read_last_date(orig); b, _ = _read_last_date(cand)
    wa, wb_ = load_workbook(orig, read_only=True), load_workbook(cand, read_only=True)
    if len(wb_.sheetnames) < len(wa.sheetnames):
        return False, "시트 수 감소"
    if a and b and b < a:
        return False, f"마지막 일자 역행 {a}→{b}"
    return True, f"{a}→{b}"


def _jump_ratio(path: Path, first_new: float) -> float | None:
    """기존 마지막 종가 대비 신규 첫 종가 변동률(기존 종가 없으면 None)."""
    last_close = _read_last_close(path)
    if not last_close:
        return None
    return first_new / last_close - 1


GAP_DAYS = 7   # 연속 관측 사이 달력일 간격이 이보다 크면 '공백'으로 본다(주말·연휴 3~4일은 정상)


def _find_recent_gap(path: Path) -> date | None:
    """최신 연도 시트에서 마지막 공백의 시작일(공백 직전 관측일). 공백이 없으면 None.

    일별 스냅샷 모드는 '오늘 1행'만 붙이므로 수집이 멈춘 기간이 있으면 그 뒤에 오늘 행이 붙어 공백이
    가려진다(2026-11-19 실측: 09-23 → 11-18). 공백 복구 모드는 이 공백을 찾아 그 뒤 행을 걷어 내고
    historical 창으로 다시 채운다.
    """
    wb = load_workbook(path, read_only=True, data_only=True)
    years = sorted((int(m.group(1)), n) for n in wb.sheetnames if (m := _YEAR_SHEET_RE.search(n)))
    if not years:
        return None
    y, name = years[-1]
    ds = sorted(date(y, int(r[0]), int(r[1])) for r in wb[name].iter_rows(min_row=2, values_only=True)
                if r and r[0] is not None and r[1] is not None)
    gaps = [(a, b) for a, b in zip(ds, ds[1:]) if (b - a).days > GAP_DAYS]
    return gaps[-1][0] if gaps else None


def _truncate_after(path: Path, cut: date) -> int:
    """cut 이후 관측 행을 해당 연도 시트에서 삭제. 반환: 삭제 행 수."""
    wb = load_workbook(path)
    name = f"{cut.year}년"
    if name not in wb.sheetnames:
        return 0
    ws = wb[name]
    drop = [i for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2)
            if r and r[0] is not None and r[1] is not None and date(cut.year, int(r[0]), int(r[1])) > cut]
    for i in reversed(drop):
        ws.delete_rows(i)
    wb.save(path)
    return len(drop)


def _commit_rows(path: Path, rows: pd.DataFrame, desc: bool,
                 cut: date | None = None) -> tuple[bool, int, str]:
    """임시 사본에 append → 재판독 검증 통과 시에만 원본 교체. → (성공, 추가 행 수, 메시지).

    cut이 주어지면(공백 복구) 사본에서 cut 이후 행을 먼저 걷어 낸 뒤 append한다 — 원본은 검증 통과 시에만 바뀐다.
    """
    with tempfile.TemporaryDirectory() as td:
        cand = Path(td) / path.name
        shutil.copy(path, cand)
        if cut is not None:
            _truncate_after(cand, cut)
        n = append_rows(cand, rows, desc)
        ok, msg = _validate(path, cand)
        if not ok:
            return False, 0, msg
        shutil.copy(cand, path)
    return True, n, msg


def run(dry_run: bool = False, only: set[str] | None = None, mode: str = "snapshot",
        repair_gap: bool = False) -> list[dict]:
    if mode not in MODES:
        raise SystemExit(f"[오류] 알 수 없는 모드: {mode} — {MODES} 중 하나여야 함")
    te_key = os.environ.get("TRADING_ECONOMICS_API_KEY", "").strip()
    if not te_key and not dry_run:
        raise SystemExit("[오류] TRADING_ECONOMICS_API_KEY 미설정 — GitHub Secrets 확인")
    today = date.today()
    print(f"[정보] TE xlsx 갱신 시작 — 모드 {mode}, 기준일 {today}"
          + (" (dry-run — API 호출 없음)" if dry_run else ""))
    results: list[dict] = []
    throttled = False
    for path in sorted(TE_ROOT.rglob("*.xlsx")):
        commodity = _commodity_of(path)
        if only and commodity not in only:
            continue
        last, desc = _read_last_date(path)
        rec = {"file": path.name, "commodity": commodity, "last_before": last, "mode": mode,
               "status": "", "added": 0, "symbol": ""}
        if throttled:                       # 스로틀 확인 후 남은 파일은 호출하지 않는다
            rec["status"] = "스로틀 — 중단"; results.append(rec); continue
        if last is None:
            rec["status"] = "시트 없음"; results.append(rec); continue
        cut = _find_recent_gap(path) if (mode == "historical" and repair_gap) else None
        if cut is not None:
            rec["status"] = f"공백 복구({cut} 이후 재조회)"
        # snapshot은 '오늘 1행'을 노리므로 마지막 일자가 오늘이어야 최신. historical은 1일 여유.
        elif last >= (today if mode == "snapshot" else today - timedelta(days=1)):
            rec["status"] = "최신"; results.append(rec); continue
        if dry_run:
            rec["status"] = f"dry-run(갱신 필요 {last}~{today})"; results.append(rec); continue

        symbols = discover_symbols(te_key, commodity)
        rec["symbol"] = ",".join(symbols[:3])
        if not symbols:
            rec["status"] = "심볼 미발견"; results.append(rec); continue

        if mode == "snapshot":
            row, status, used, cols = fetch_snapshot(te_key, symbols, last, today)
            time.sleep(SYMBOL_PACING_S)
            if status == "throttle":
                throttled = True
                rec["status"] = "스로틀 — 중단"; results.append(rec); continue
            if status == "empty":
                # 모든 심볼이 빈 스냅샷 — 시도 심볼·검색어를 로그·보고서에 남겨 다음 런 로그로 확정한다
                terms = search_terms_of(commodity)
                print(f"[정보] {path.name}: 스냅샷 응답 없음 — 시도 심볼 {symbols}, 검색어 {list(terms)}")
                rec["symbol"] = ",".join(symbols)
                rec["tried_terms"] = " / ".join(terms)
            if status != "ok" or row is None:
                rec["status"] = {"empty": f"스냅샷 응답 없음(시도 {len(symbols)}심볼)", "error": "HTTP 오류",
                                 "fields": f"필드 없음(컬럼 {cols})", "stale": "최신",
                                 "weekend": "주말 스탬프 — 제외",
                                 "future": "미래 일자 — 제외"}.get(status, f"미갱신({status})")
                results.append(rec); continue
            rec["symbol"] = used
            new_rows = pd.DataFrame([{**row, "date": pd.Timestamp(row["date"])}])
        else:
            hist, status = fetch_history(te_key, symbols, cut or last, today)
            if status != "ok":
                rec["status"] = {"plan": "플랜 미포함(409/403)", "empty": "응답 0행", "error": "HTTP 오류",
                                 "sparse": f"밀도 부족({len(hist)}행) — 미갱신"}[status]
                results.append(rec); continue
            new_rows = hist

        first_new = float(new_rows["close"].iloc[0])
        jump = None if cut is not None else _jump_ratio(path, first_new)   # 복구는 공백 전 종가와 비교 불가
        if jump is not None and abs(jump) > MAX_JUMP:
            rec["status"] = f"점프 {jump:+.0%}(계약·집계 혼입 의심) — 미갱신"
            print(f"[경고] {path.name}: 기존 종가 대비 {jump:+.0%}(신규 {first_new}) — 미갱신")
            results.append(rec); continue

        ok, n, msg = _commit_rows(path, new_rows, desc, cut=cut)
        if not ok:
            rec["status"] = f"검증 실패({msg}) — 원본 유지"; results.append(rec); continue
        rec["status"] = f"갱신(+{n}행, {msg})"; rec["added"] = n
        results.append(rec)
        print(f"[완료] {path.name}: +{n}행 ({msg})")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rp = REPORT_DIR / f"te_api_update_{today.isoformat()}.md"
    lines = [f"# Trading Economics API 갱신 결과 — {today}", "",
             "| 파일 | 품목 | 모드 | 갱신 전 마지막 일자 | 심볼 | 상태 | 추가 행 |",
             "|---|---|---|---|---|---|---|"]
    lines += [f"| {r['file']} | {r['commodity']} | {r['mode']} | {r['last_before']} "
              f"| {r['symbol']} | {r['status']} | {r['added']} |" for r in results]
    empty = [r for r in results if r.get("tried_terms")]
    if empty:
        lines += ["", "> ℹ️ 스냅샷 응답 없음 — 시도 심볼·검색어(다음 실행 로그에서 유효 심볼 확정용):"]
        lines += [f">   - {r['commodity']}: 심볼 `{r['symbol']}` · 검색어 `{r['tried_terms']}`"
                  for r in empty]
    plan = [r for r in results if r["status"].startswith("플랜")]
    if plan:
        lines += ["", f"> ⚠️ {len(plan)}건이 '플랜 미포함(409/403)' — 연장 플랜에 Markets Historical이 "
                      "포함되지 않았다면 ①플랜 상향 또는 ②일별 스냅샷 append로 대체해야 함(결정 요청)."]
    if throttled:
        lines += ["", "> ⚠️ 스로틀(409/429)로 남은 파일 호출을 중단함 — 다음 회차에서 이어서 갱신됨(비치명)."]
    rp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[완료] 보고서 → {rp}")
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=MODES, default="snapshot",
                    help="snapshot=일별 1행 append(기본) · historical=공백 복구 창 조회")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--repair-gap", action="store_true",
                    help="historical 모드 전용 — 최신 연도 시트의 마지막 공백(>7일)을 찾아 그 뒤를 재조회로 채움")
    a = ap.parse_args()
    run(dry_run=a.dry_run, only=set(x.strip() for x in a.only.split(",") if x.strip()) or None,
        mode=a.mode, repair_gap=a.repair_gap)
