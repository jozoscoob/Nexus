"""CFTC COT 커넥터 — 변환·as-of 지연 검증(네트워크 없음)."""
import pandas as pd
import pytest

from src.pipeline.asof import attach_asof
from src.pipeline.connectors.cot_connector import NET_PAIRS, to_long


@pytest.fixture
def raw_cot() -> pd.DataFrame:
    row = {"report_date_as_yyyy_mm_dd": "2026-11-03T00:00:00.000", "open_interest_all": "600"}
    for i, (lo, sh) in enumerate(NET_PAIRS.values()):
        row[lo], row[sh] = str(100 + i), "40"
    return pd.DataFrame([row])


def test_net_and_pct(raw_cot: pd.DataFrame) -> None:
    d = to_long(raw_cot).set_index("indicator_code")["value"]
    assert d["COT_SBO_MM_NET"] == 60
    assert d["COT_SBO_MM_NET_PCT_OI"] == pytest.approx(10.0)


def test_no_lookahead(raw_cot: pd.DataFrame) -> None:
    """화요일 기준 포지션은 금요일 장 마감 후 공개 — 기준일 당일·주중에 보이면 누수."""
    d = attach_asof(to_long(raw_cot), source="CFTC_COT")
    assert (d["available_at"] - d["event_time"]).dt.days.min() >= 4
