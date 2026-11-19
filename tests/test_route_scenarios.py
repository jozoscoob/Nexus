"""해상 경로 시나리오 단위 테스트 — 합성 PortWatch 프레임으로 판정·선례·우회 산술을 검증."""
import pandas as pd
import pytest

from src.logistics import route_scenarios as rs


@pytest.fixture
def transits() -> pd.DataFrame:
    idx = pd.date_range("2019-01-01", "2026-11-15", freq="D")
    df = pd.DataFrame({"HORMUZ": 40.0, "PANAMA": 12.0, "CAPE_GOOD_HOPE": 10.0,
                       "MALACCA": 70.0, "BAB_EL_MANDEB": 20.0}, index=idx)
    df.loc["2026-03-01":, "HORMUZ"] = 1.0          # 최근 붕괴
    df.loc["2026-03-01":, "CAPE_GOOD_HOPE"] = 16.0  # 우회 유입
    return df


@pytest.fixture
def cfg() -> dict:
    return rs.load_config()


def test_status_flags_disruption_and_inflow(transits, cfg):
    st, asof = rs.strait_status(transits, cfg["status_rule"])
    assert asof == "2026-11-15"
    assert st["HORMUZ"].state == "disrupted"
    assert st["CAPE_GOOD_HOPE"].state == "elevated"
    assert st["PANAMA"].state == "normal"


def test_precedent_change_is_computed_from_data(transits, cfg):
    pr = rs.precedents(transits, cfg["contingencies"]["hormuz_us_iran"])
    crisis = [p for p in pr if p.name.startswith("2026")][0]
    assert crisis.changes["HORMUZ"] == pytest.approx(-97.5, abs=0.1)


def test_extra_days_range_orders_fast_then_slow(cfg):
    lo, hi = rs.extra_days(16000, 9600, cfg["speed_knots"])
    assert 0 < lo < hi
    assert lo == pytest.approx(6400 / (14.0 * 24), abs=0.1)


def test_hormuz_has_no_physical_detour_on_korea_lanes(transits, cfg):
    st, _ = rs.strait_status(transits, cfg["status_rule"])
    view = {c["id"]: c for c in rs.contingency_view(cfg, transits, st)}
    assert view["hormuz_us_iran"]["route_impacts"] == []   # 한국향 대두유 항로는 호르무즈 미경유
    assert view["hormuz_us_iran"]["active_now"] == ["HORMUZ"]
    usg = [i for i in view["panama_drought"]["route_impacts"] if i["route"] == "RT-USG-KR"][0]
    assert [d["name"] for d in usg["detours"]][:1] == ["수에즈 경유"]   # 거리순 정렬


def test_missing_data_degrades_honestly(cfg, tmp_path):
    rep = rs.build(raw_dir=tmp_path)
    assert rep["as_of"] is None and rep["status"] == {}
