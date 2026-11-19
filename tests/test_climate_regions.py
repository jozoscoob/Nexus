"""산지 설정(config/production_regions.yaml)·Open-Meteo 예보 층·as-of 정합 검증 (2026-09-13).

샌드박스 프록시가 open-meteo 호스트를 차단하므로 httpx는 전부 합성 응답으로 대체한다.
tier2 좌표 기대값은 설정 파일에서 읽는다(2026-09-13 벨트 중심 검증 반영 — 하드코딩 금지).
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest


def _utc_today() -> date:
    """예보 발행일 기준 — 요청이 timezone=UTC라 UTC 날짜(컨테이너 KST 00~09시에도 미래가 되지 않게)."""
    return datetime.now(timezone.utc).date()

from src.pipeline.asof import attach_asof, revision_status, rule_for
from src.pipeline.connectors import climate_connector as cc

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "production_regions.yaml"
CODE_RE = re.compile(r"^[A-Z]{2}_[A-Za-z]+$")
COORD_STATUSES = {"CONFIRMED", "INFERENCE"}

# 정본 좌표 표 §3.2 (docs/research_desk/_reference/soybean_oil_production_climate.md) — 승인자 확정값.
# tier1은 변경 금지 대상이므로 회귀 가드로 상수를 유지한다(설정 파일이 조용히 바뀌면 여기서 잡힌다).
CANONICAL_TIER1: dict[str, tuple[float, float]] = {
    "CN_Heilongjiang": (48.0, 128.0), "CN_Shandong": (36.5, 118.0), "CN_Jiangsu": (32.5, 120.0),
    "US_Illinois": (40.0, -89.0), "US_Iowa": (42.0, -93.5), "US_Indiana": (40.2, -86.1),
    "BR_MatoGrosso": (-13.0, -56.0), "BR_Parana": (-24.5, -51.5),
    "BR_MatoGrossodoSul": (-20.0, -54.5), "AR_Cordoba": (-31.4, -64.2),
    "AR_SantaFe": (-33.0, -60.6), "AR_BuenosAires": (-36.0, -60.0),
}
TIER2_CODES = {
    "BR_RioGrandedoSul", "BR_Goias", "US_Minnesota", "US_Nebraska", "US_Ohio",
    "PY_AltoParana", "IN_MadhyaPradesh", "MY_Sabah", "MY_Johor", "ID_Riau",
    "ID_CentralKalimantan",
}


@pytest.fixture(scope="module")
def regions() -> dict[str, dict]:
    return cc.load_production_regions(CONFIG)


@pytest.fixture(scope="module")
def raw_entries() -> dict[str, dict]:
    """설정 파일 원문(share_note·anchor 등 로더가 버리는 필드 포함) — 최소 파서 경로."""
    entries = cc._parse_regions_minimal(CONFIG.read_text(encoding="utf-8"))
    return {e["code"]: e for e in entries}


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cc.time, "sleep", lambda *_: None)


# ── 설정 파일 ──────────────────────────────────────────────────────────────────
def test_config_loads_23_regions(regions: dict[str, dict]) -> None:
    assert len(regions) == 23
    tiers = [int(i["tier"]) for i in regions.values()]
    assert tiers.count(1) == 12 and tiers.count(2) == 11


def test_tier1_confirmed_with_canonical_coords(regions: dict[str, dict]) -> None:
    t1 = {c: i for c, i in regions.items() if int(i["tier"]) == 1}
    assert set(t1) == set(CANONICAL_TIER1)
    for code, (lat, lon) in CANONICAL_TIER1.items():
        assert t1[code]["coord_status"] == "CONFIRMED", code
        assert (t1[code]["lat"], t1[code]["lon"]) == (lat, lon), code
        assert t1[code]["crop"] == "soy"


def test_tier2_codes_and_crops(regions: dict[str, dict]) -> None:
    t2 = {c: i for c, i in regions.items() if int(i["tier"]) == 2}
    assert set(t2) == TIER2_CODES
    assert {i["crop"] for i in t2.values()} == {"soy", "palm"}
    assert all(i["crop"] == "palm" for c, i in t2.items() if c[:2] in ("MY", "ID"))
    assert all(i["crop"] == "soy" for c, i in t2.items() if c[:2] not in ("MY", "ID"))


def test_every_region_has_coord_status_and_share_note(regions: dict[str, dict],
                                                      raw_entries: dict[str, dict]) -> None:
    # 좌표 라벨은 두 값만 허용, 근거 문구는 전 지역 필수(2026-09-13 검증 규약)
    for code, info in regions.items():
        assert info["coord_status"] in COORD_STATUSES, code
        assert str(raw_entries[code].get("share_note", "")).strip(), f"{code}: share_note 누락"


def test_tier2_verification_fields(raw_entries: dict[str, dict]) -> None:
    # tier2는 벨트 기준점·출처 URL·검증일을 설정 파일에 보존해야 재대조가 가능하다
    for code in TIER2_CODES:
        e = raw_entries[code]
        assert str(e.get("anchor", "")).strip(), f"{code}: anchor 누락"
        assert "http" in str(e.get("source_url", "")), f"{code}: source_url 누락"
        assert str(e.get("verified_on", "")).strip(), f"{code}: verified_on 누락"


def test_coordinates_within_physical_range(regions: dict[str, dict]) -> None:
    # 기대 좌표는 설정 파일이 원천 — 여기서는 물리 범위·반구 정합만 검사한다
    hemisphere = {"BR": (-1, -1), "AR": (-1, -1), "PY": (-1, -1), "US": (1, -1), "CN": (1, 1),
                  "IN": (1, 1), "MY": (1, 1), "ID": (None, 1)}   # ID는 적도 양측
    for code, info in regions.items():
        lat, lon = info["lat"], info["lon"]
        assert -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0, code
        assert round(lat, 1) == lat and round(lon, 1) == lon, f"{code}: 0.1° 반올림 규약 위반"
        lat_sign, lon_sign = hemisphere[code[:2]]
        if lat_sign is not None:
            assert lat * lat_sign > 0, f"{code}: 위도 반구 불일치"
        assert lon * lon_sign > 0, f"{code}: 경도 반구 불일치"


def test_codes_unique_and_pattern(regions: dict[str, dict]) -> None:
    codes = list(regions)
    assert len(codes) == len(set(codes))
    assert all(CODE_RE.match(c) for c in codes), [c for c in codes if not CODE_RE.match(c)]


def test_builtin_tier1_matches_config(regions: dict[str, dict]) -> None:
    # 내장 폴백 dict가 설정 파일 tier1과 어긋나면 폴백 시 좌표가 조용히 바뀐다
    for code, info in cc._BUILTIN_REGIONS.items():
        assert (info["lat"], info["lon"]) == (regions[code]["lat"], regions[code]["lon"]), code


def test_minimal_parser_matches_yaml(regions: dict[str, dict], raw_entries: dict[str, dict]) -> None:
    # pyyaml 부재 CI 경로: 최소 파서가 동일 결과를 내야 tier2가 조용히 사라지지 않는다
    assert set(raw_entries) == set(regions)
    for code, info in regions.items():
        got = (float(raw_entries[code]["lat"]), float(raw_entries[code]["lon"]))
        assert got == (info["lat"], info["lon"]), code
        assert int(raw_entries[code]["tier"]) == info["tier"]
        assert raw_entries[code]["coord_status"] == info["coord_status"]


def test_fallback_on_missing_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = cc.load_production_regions(tmp_path / "missing.yaml")
    assert len(out) == 12 and set(out) == set(cc._BUILTIN_REGIONS)
    assert all(i["tier"] == 1 for i in out.values())
    assert "[경고]" in capsys.readouterr().out


def test_fallback_on_parse_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("regions:\n  - code: X_Y\n    lat: 1.0\n", encoding="utf-8")  # lon 누락
    assert len(cc.load_production_regions(bad)) == 12


def test_climate_tier_env_filters(monkeypatch: pytest.MonkeyPatch,
                                  regions: dict[str, dict]) -> None:
    monkeypatch.setenv("CLIMATE_TIER", "1")
    assert len(cc._select_regions(regions)) == 12
    monkeypatch.setenv("CLIMATE_TIER", "all")
    assert len(cc._select_regions(regions)) == 23


# ── 예보 층 ────────────────────────────────────────────────────────────────────
class _Resp:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def _synthetic_forecast(days: int = 15) -> dict:
    start = _utc_today()
    times = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    return {"daily": {"time": times, **{v: [float(i) for i in range(days)]
                                        for v in cc.FORECAST_VARS}}}


@pytest.fixture
def forecast_df(monkeypatch: pytest.MonkeyPatch, regions: dict[str, dict]) -> pd.DataFrame:
    calls: list[dict] = []

    def _fake_get(url: str, params: dict | None = None, timeout: float = 0) -> _Resp:
        assert url == cc.OPEN_METEO_FORECAST_BASE
        calls.append(params or {})
        return _Resp(_synthetic_forecast())

    monkeypatch.setattr(cc.httpx, "get", _fake_get)
    monkeypatch.delenv("CLIMATE_TIER", raising=False)
    two = {c: regions[c] for c in ("BR_MatoGrosso", "MY_Sabah")}
    df = cc.fetch_openmeteo_forecast(two, forecast_days=15)
    assert len(calls) == 2 and all(p["timezone"] == "UTC" for p in calls)
    return df


def test_forecast_rows_shape(forecast_df: pd.DataFrame) -> None:
    assert "FCST_precipitation_sum_BR_MatoGrosso" in set(forecast_df["indicator_code"])
    assert len(forecast_df) == 2 * len(cc.FORECAST_VARS) * 15
    per = forecast_df.groupby(["region_code", "indicator_code"]).size()
    assert (per == 15).all()
    # A-263: price_date = 발행일(오늘) — 미래 price_date 0건, 유효일·리드는 별도 열
    assert (forecast_df["price_date"] == pd.Timestamp(_utc_today())).all()
    assert (forecast_df["valid_date"] >= forecast_df["price_date"]).all()
    assert (forecast_df["valid_date"] > pd.Timestamp(_utc_today())).sum() == 2 * 5 * 14
    assert forecast_df["lead_days"].between(0, 16).all()
    assert ((forecast_df["valid_date"] - forecast_df["price_date"]).dt.days
            == forecast_df["lead_days"]).all()
    assert forecast_df["source_name"].eq(cc.FORECAST_SOURCE_NAME).all()
    assert forecast_df["note"].str.startswith(f"issue_date={_utc_today().isoformat()}").all()


def test_forecast_asof_no_future_availability(forecast_df: pd.DataFrame) -> None:
    out = attach_asof(forecast_df, source="CLIMATE")
    ing = pd.to_datetime(out["ingested_at"]).dt.tz_localize(None)
    assert (out["available_at"] <= ing).all(), "예보 행 available_at이 수집 시각을 넘음"
    # A-263: event_time = 발행일 — A-195 전망 분기(event_time > ingested_at)는 더 이상 발동하지 않는다
    assert (out["event_time"] <= ing).all()
    assert (out["available_at"].dt.normalize() == pd.Timestamp(_utc_today())).all()
    assert out["vintage_known"].all() and out["source_vintage"].eq(_utc_today().isoformat()).all()


def test_fcst_rules_registered() -> None:
    rule = rule_for("FCST_precipitation_sum_BR_MatoGrosso")
    assert rule.kind == "immediate" and rule.lag_days == 0 and rule.revises
    assert revision_status("FCST_temperature_2m_max_US_Iowa") == "full"
    # 기존 아카이브 규칙은 그대로(lag 6)
    assert rule_for("precipitation_sum_BR_MatoGrosso").lag_days == 6


def test_forecast_region_failure_is_nonfatal(monkeypatch: pytest.MonkeyPatch,
                                             regions: dict[str, dict]) -> None:
    def _flaky(url: str, params: dict | None = None, timeout: float = 0) -> _Resp:
        if params and params["latitude"] == regions["MY_Sabah"]["lat"]:
            raise RuntimeError("synthetic 429")
        return _Resp(_synthetic_forecast())

    monkeypatch.setattr(cc.httpx, "get", _flaky)
    monkeypatch.setattr(cc, "_fetch", lambda url, params=None, max_retries=4: _flaky(url, params))
    two = {c: regions[c] for c in ("BR_MatoGrosso", "MY_Sabah")}
    df = cc.fetch_openmeteo_forecast(two)
    assert set(df["region_code"]) == {"BR_MatoGrosso"}
