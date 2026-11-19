"""IMF PortWatch 해협(초크포인트) 일별 통과 선박 수 수집 — AISstream 해협 집계 대체.

원천: IMF PortWatch Daily Chokepoints Data(ArcGIS FeatureServer, 키 불필요·무료).
위성 AIS 기반 일별 통과 척수(유형별: 탱커·건화물·컨테이너 등). 주 1회 갱신·약 4~7일 지연 →
**실시간이 아님**. 실시간 경보는 GDELT·해사 경보(UKMTO/MARAD) 등 OSINT가 보완한다
(docs/operations/actions_scope.md §PortWatch).
as-of: 규칙 PW_(lag_days=9 — 주간 배치가 직전 주 월요일분까지 늦게 반영되는 최악 지연 보수 적용).
"""
from __future__ import annotations

import os
import sys
import time
from datetime import date
from pathlib import Path

import httpx
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.pipeline.asof import attach_asof  # noqa: E402

PW_URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
          "Daily_Chokepoints_Data/FeatureServer/0/query")
OUTPUT_DIR = "data/raw"
PAGE_SIZE = 2000          # 서버 maxRecordCount(10000) 이하
MAX_RETRIES = 4
# 대두유 해상 경로와 그 우회로에 걸리는 해협만 수집 — portid → 지표 접미사
CHOKEPOINTS = {
    "chokepoint1": "SUEZ",
    "chokepoint2": "PANAMA",
    "chokepoint4": "BAB_EL_MANDEB",
    "chokepoint5": "MALACCA",
    "chokepoint6": "HORMUZ",
    "chokepoint7": "CAPE_GOOD_HOPE",
    "chokepoint12": "KOREA_STRAIT",
    # 우회로 판정용(2026-11-19 추가) — 말라카 대체(롬복·순다), 베트남·중국 남부 → 한국 항로(대만해협)
    "chokepoint11": "TAIWAN_STRAIT",
    "chokepoint15": "LOMBOK",
    "chokepoint19": "SUNDA",
}
# 원천 필드 → 지표 접미사
FIELDS = {"n_tanker": "TANKER", "n_dry_bulk": "DRY_BULK", "n_total": "TOTAL"}


def _get(params: dict) -> dict:
    """ArcGIS 질의 — 지수 백오프 재시도(data_pipeline.md)."""
    delay = 2
    for attempt in range(MAX_RETRIES):
        try:
            r = httpx.get(PW_URL, params=params, timeout=60)
            r.raise_for_status()
            body = r.json()
            if "error" in body:
                raise RuntimeError(f"ArcGIS 오류 응답: {body['error']}")
            return body
        except (httpx.HTTPError, RuntimeError, ValueError) as e:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"[오류] PortWatch 호출 실패: {e}") from e
            time.sleep(delay)
            delay *= 2
    return {}


def fetch_portwatch(start: str) -> pd.DataFrame:
    ids = ",".join(f"'{p}'" for p in CHOKEPOINTS)
    where = f"portid IN ({ids}) AND date >= DATE '{start}'"
    rows: list[dict] = []
    offset = 0
    while True:
        body = _get({"where": where, "outFields": "date,portid," + ",".join(FIELDS),
                     "orderByFields": "date ASC", "resultOffset": offset,
                     "resultRecordCount": PAGE_SIZE, "f": "json"})
        feats = body.get("features", [])
        rows += [f["attributes"] for f in feats]
        if len(feats) < PAGE_SIZE and not body.get("exceededTransferLimit"):
            break
        offset += len(feats)
    return pd.DataFrame(rows)


def to_long(raw: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in ["date", "portid", *FIELDS] if c not in raw.columns]
    if missing:
        raise ValueError(f"[오류] PortWatch 응답 컬럼 누락: {missing} — 원천 스키마 변경 확인 필요")
    raw = raw.assign(price_date=pd.to_datetime(raw["date"]).dt.tz_localize(None).dt.normalize(),
                     cp=raw["portid"].map(CHOKEPOINTS))
    long = raw.melt(id_vars=["price_date", "cp"], value_vars=list(FIELDS),
                    var_name="field", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value", "cp"])
    long["indicator_code"] = "PW_" + long["cp"] + "_" + long["field"].map(FIELDS) + "_TRANSITS"
    # (지표, 일자) 키 유일성 — mart 값충돌 게이트(D-033) 선제 방어
    long = long.groupby(["price_date", "indicator_code"], as_index=False)["value"].max()
    long["unit"] = "vessels/day"
    long["source_name"] = "IMF_PORTWATCH"
    long["ingested_at"] = pd.Timestamp.now("UTC")
    return long


def run() -> None:
    start_year = int(os.environ.get("HISTORICAL_START_YEAR", "2019"))  # 원천 시작 2019-01-01
    raw = fetch_portwatch(f"{max(start_year, 2019)}-01-01")
    if raw.empty:
        raise SystemExit("[오류] PortWatch 응답 0건 — 엔드포인트·네트워크 확인 필요")
    df = attach_asof(to_long(raw), source="IMF_PORTWATCH")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = f"{OUTPUT_DIR}/portwatch_chokepoints_{date.today():%Y%m%d}.parquet"
    df.to_parquet(out, index=False)
    print(f"[완료] PortWatch 해협 {df['indicator_code'].nunique()}지표 · {len(df)}건 → {out} "
          f"(최신 {df['price_date'].max():%Y-%m-%d} — 원천 지연 약 4~7일)")


if __name__ == "__main__":
    run()
