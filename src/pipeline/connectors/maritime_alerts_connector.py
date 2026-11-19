"""해사 보안 경보 수집 — UKMTO·JMIC·MARAD·NGA 항행 경보를 해역별 일별 건수로 (PortWatch 4~7일 지연의 실시간 보완).

원천 판정(2026-11-19 실측):
  - UKMTO(ukmto.org)·MARAD MSCI(maritime.dot.gov)는 자동 수집 클라이언트를 403으로 차단하고 공식 RSS·API가 없다.
    → 봇 차단을 우회하지 않는다. 대신 Google News RSS 검색(무료·공개 피드)으로 해당 기관 명의 경보 보도를 모으고,
    각 항목의 원문 링크·매체명을 note에 남긴다(출처 추적).
  - NGA MSI 항행 경보 API(msi.nga.mil/api/publications/broadcast-warn)는 시도하되, 차단(503)·오류면 건너뛴다(비치명).
산출: 지표 MARALERT_{해역}_COUNT(일별 경보 보도 건수) + MARALERT_NGA_{NAVAREA}_ACTIVE(가능할 때).
as-of: 규칙 MARALERT_(1일 지연 — 수집이 장 마감 이후라 GDELT와 같은 사유).
해석 규율: 건수는 '보도·경보의 빈도'이지 사건 규모나 통항 차질의 측정이 아니다 — 통항 실측은 PortWatch가 담당.
"""
from __future__ import annotations

import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus

import httpx
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

OUTPUT_DIR = "data/raw"
UA = "Mozilla/5.0 (compatible; nexus-research/1.0)"
GNEWS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
NGA_API = "https://msi.nga.mil/api/publications/broadcast-warn"
LOOKBACK_DAYS = int(os.environ.get("MARALERT_LOOKBACK_DAYS", "14"))
MAX_RETRIES = 3
# 기관 명의 경보·주의보 검색어 — 기관명이 들어간 보도만 집계(일반 해운 뉴스 배제)
QUERIES = [
    '"UKMTO" incident', '"UKMTO" advisory', '"JMIC" advisory',
    '"MARAD" "maritime advisory"', '"U.S. Maritime Advisory"', '"navigational warning" Hormuz OR "Red Sea"',
]
# 해역 판정 키워드 — 경로 시나리오의 해협 코드와 맞춘다
REGIONS = {
    "HORMUZ": ["hormuz", "persian gulf", "arabian gulf", "gulf of oman", "oman", "khasab", "fujairah", "iran"],
    "RED_SEA": ["red sea", "bab el-mandeb", "bab-el-mandeb", "gulf of aden", "houthi", "yemen", "suez"],
    "BLACK_SEA": ["black sea", "sea of azov", "ukraine", "odesa", "odessa"],
    "MALACCA": ["malacca", "singapore strait", "sulu sea"],
    "TAIWAN": ["taiwan strait", "south china sea"],
    "WEST_AFRICA": ["gulf of guinea"],
}
AGENCIES = {"UKMTO": ["ukmto"], "JMIC": ["jmic"], "MARAD": ["marad", "u.s. maritime advisory", "us maritime advisory"],
            "NGA": ["navigational warning", "navarea"]}


def _get(url: str, **kw) -> httpx.Response | None:
    delay = 2
    for attempt in range(MAX_RETRIES):
        try:
            r = httpx.get(url, timeout=30, headers={"User-Agent": UA}, follow_redirects=True, **kw)
            if r.status_code == 200:
                return r
            if r.status_code in (403, 503):   # 봇 차단·점검 — 재시도해도 같으므로 즉시 포기(우회 금지)
                print(f"[정보] {url.split('?')[0]} HTTP {r.status_code} — 자동 수집 차단으로 판단, 건너뜀")
                return None
        except httpx.HTTPError as e:
            if attempt == MAX_RETRIES - 1:
                print(f"[경고] 호출 실패 {url.split('?')[0]}: {e}")
                return None
        time.sleep(delay)
        delay *= 2
    return None


def _tag(text: str, table: dict[str, list[str]]) -> list[str]:
    t = text.lower()
    return [k for k, words in table.items() if any(w in t for w in words)]


def fetch_news_alerts() -> pd.DataFrame:
    since = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    rows, seen = [], set()
    for q in QUERIES:
        r = _get(GNEWS.format(q=quote_plus(q)))
        if r is None:
            continue
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError as e:
            print(f"[경고] RSS 파싱 실패({q}): {e}")
            continue
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            src = (it.find("source").text if it.find("source") is not None else "") or ""
            try:
                pub = parsedate_to_datetime(it.findtext("pubDate") or "")
            except (TypeError, ValueError):
                continue
            if pub < since or title in seen:
                continue
            agencies = _tag(title, AGENCIES)
            if not agencies:            # 기관명 없는 보도는 제외(검색 엔진의 느슨한 매칭 방지)
                continue
            seen.add(title)
            rows.append({"date": pub.astimezone(timezone.utc).date(), "title": title, "link": link,
                         "publisher": src, "agencies": agencies, "regions": _tag(title, REGIONS) or ["OTHER"]})
        time.sleep(1)
    return pd.DataFrame(rows)


def fetch_nga() -> pd.DataFrame:
    r = _get(NGA_API, params={"output": "json", "status": "A"})
    if r is None:
        return pd.DataFrame()
    try:
        items = next(iter(r.json().values()))
    except (ValueError, StopIteration, AttributeError):
        print("[정보] NGA 응답 형식 미확인 — 건너뜀")
        return pd.DataFrame()
    rows = [{"navArea": str(i.get("navArea", "")).upper(), "text": str(i.get("text", ""))[:300]} for i in items]
    return pd.DataFrame(rows)


def to_long(news: pd.DataFrame, nga: pd.DataFrame) -> pd.DataFrame:
    now = pd.Timestamp.now("UTC")
    out = []
    if not news.empty:
        ex = news.explode("regions")
        for (d, reg), g in ex.groupby(["date", "regions"]):
            note = " | ".join(f"[{'/'.join(a)}] {t} ({p}) {l}" for t, p, l, a in
                              g[["title", "publisher", "link", "agencies"]].head(5).itertuples(index=False))
            out.append({"price_date": pd.Timestamp(d), "indicator_code": f"MARALERT_{reg}_COUNT",
                        "value": float(len(g)), "unit": "reports/day", "note": note[:1500]})
    if not nga.empty:
        today = pd.Timestamp(date.today())
        for area, g in nga.groupby("navArea"):
            out.append({"price_date": today, "indicator_code": f"MARALERT_NGA_{area or 'NA'}_ACTIVE",
                        "value": float(len(g)), "unit": "warnings", "note": " | ".join(g["text"].head(3))[:1500]})
    df = pd.DataFrame(out)
    if df.empty:
        return df
    df["source_name"] = "MARITIME_ALERTS(GoogleNewsRSS·NGA)"
    df["ingested_at"] = now
    return df


def run() -> None:
    news, nga = fetch_news_alerts(), fetch_nga()
    df = to_long(news, nga)
    if df.empty:
        print("[경고] 해사 경보 0건 — 원천 응답 없음(비치명)")
        return
    df = attach_asof(df, source="MARITIME_ALERTS")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = f"{OUTPUT_DIR}/maritime_alerts_{date.today():%Y%m%d}.parquet"
    df.to_parquet(out, index=False)
    by = df.groupby("indicator_code")["value"].sum().sort_values(ascending=False).head(6).to_dict()
    print(f"[완료] 해사 경보 {len(news)}건(최근 {LOOKBACK_DAYS}일) → {out} · 해역별 {by}"
          + (f" · NGA {len(nga)}건" if not nga.empty else " · NGA 미수집(차단)"))


if __name__ == "__main__":
    run()
