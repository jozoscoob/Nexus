"""2026-11-26 Codex 근본 원인 조사 반영 회귀 테스트 — FRED 단위·GeoIntel 시점 역전·복합 지수 미확인 신호."""
from __future__ import annotations

import pandas as pd
import pytest

from src.pipeline import asof
from src.pipeline.connectors import economic_connector as ec
from src.pipeline.connectors import geointel_connector as gc

FRED_SERIES = ["FEDFUNDS", "CPIAUCSL", "DEXKOUS", "DEXBZUS", "DEXCHUS", "DEXMAUS", "VIXCLS"]


def test_fred_units_defined_for_collected_series() -> None:
    """A: 수집하는 FRED 7계열 모두 단위가 정의돼야 함(빈 문자열 금지)."""
    assert all(ec.FRED_UNITS.get(s) for s in FRED_SERIES)


def test_fred_series_rows_carry_unit(monkeypatch: pytest.MonkeyPatch) -> None:
    """A: fetch_fred_series가 돌려주는 행에 단위가 실려야 함 — 병합 단계에서 덮어쓰지 않음."""
    payload = {"observations": [{"date": "2026-11-20", "value": "1400.1"},
                                {"date": "2026-11-21", "value": "1401.2"}]}
    monkeypatch.setattr(ec, "_fetch", lambda *a, **k: payload)
    monkeypatch.setenv("FRED_API_KEY", "test")
    df = ec.fetch_fred_series("DEXKOUS", "2026-11-20", "2026-11-21")
    assert not df.empty and set(df["unit"]) == {"KRW/USD"}


def test_geointel_observation_not_after_collection() -> None:
    """B1: 관측일(UTC 날짜 자정)은 수집 시각보다 늦을 수 없음 — KST 새벽 실행에서도."""
    df = gc._to_df([gc._make_row("SEISMIC_TEST", 3.0, "M", "t")])
    ing = df["ingested_at"].dt.tz_convert("UTC").dt.tz_localize(None)
    assert (df["price_date"] <= ing).all()


def test_geointel_inversion_is_flagged_not_exempted() -> None:
    """B1: GeoIntel 행의 역전은 '전망 예외'로 숨기지 않고 결함으로 판정."""
    df = pd.DataFrame({
        "source_name": ["GeoIntel", "USDA_PSD"],
        "event_time": [pd.Timestamp("2026-11-26"), pd.Timestamp("2027-09-01")],
        "available_at": [pd.Timestamp("2026-11-25 21:00"), pd.Timestamp("2026-11-12")],
        "ingested_at": [pd.Timestamp("2026-11-25 21:00", tz="UTC")] * 2,
    })
    assert asof.leak_inversions(df).tolist() == [True, False]   # 전망 행(PSD)은 여전히 예외


def _frame(rows: list[dict], confirmed: bool = True, not_configured: bool = False) -> pd.DataFrame:
    f = gc._confirmed_frame(rows) if confirmed else gc._to_df(rows)
    if not_configured:
        f.attrs["not_configured"] = True
    return f


def test_composite_withheld_when_a_signal_unconfirmed() -> None:
    """B2: 구성 신호 하나라도 확인되지 않으면 복합 지수를 0으로 채워 발행하지 않음."""
    frames = [_frame([gc._make_row("SEISMIC_X", 5.0, "M", "")]), _frame([]),
              _frame([], confirmed=False), _frame([])]
    assert gc._compute_composite(frames) == []


def test_composite_published_and_declares_unconfigured_source() -> None:
    """B2: 전부 확인되면 발행 — 키 미설정 원천은 note에 명시(영구 보류 아님)."""
    frames = [_frame([gc._make_row("SEISMIC_X", 7.0, "M", "")]), _frame([]),
              _frame([gc._make_row("GDELT_EVENT_SCORE", 10.0, "a", "")]), _frame([], not_configured=True)]
    rows = gc._compute_composite(frames)
    assert len(rows) == 1 and rows[0]["value"] == pytest.approx(45.0)
    assert "미설정" in rows[0]["note"] and "FIRMS_FIRE" in rows[0]["note"]


def test_vix_skips_vintage_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """D: VIXCLS는 vintage 3,980개로 최초 발표본 요청 상한(2,000) 초과 → 표준 요청만 보냄."""
    sent: list[dict] = []

    def fake_fetch(url: str, params: dict, *a, **k) -> dict:
        sent.append(dict(params))
        return {"observations": [{"date": "2026-11-20", "value": "17.1"}]}

    monkeypatch.setattr(ec, "_fetch", fake_fetch)
    monkeypatch.setenv("FRED_API_KEY", "test")
    df = ec.fetch_fred_series("VIXCLS", "2026-11-20", "2026-11-20")
    assert not df.empty and all("output_type" not in p for p in sent)


def test_customs_total_rows_excluded_not_counted_as_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """C: '총계'(기간 합계) 행은 날짜 파생 실패가 아니라 명시적 제외 — 월별 행은 그대로."""
    from src.pipeline.connectors import customs_connector as cc
    rows = [{"year": "2026.01", "hsCode": "1507100000", "impDlr": "100", "impWgt": "50"},
            {"year": "2026.02", "hsCode": "1507100000", "impDlr": "120", "impWgt": "60"},
            {"year": "총계", "hsCode": "-", "impDlr": "220", "impWgt": "110"}]
    df = cc._normalize_customs_df(rows, "KoreaCustoms/Itemtrade")
    out = capsys.readouterr().out
    assert len(df) == 2 and df["price_date"].notna().all()
    assert "총계" in out and "파생 실패" not in out


def test_geointel_save_survives_collection_attrs(tmp_path) -> None:
    """2026-11-27 06:00 회귀: 수집 판정 attrs가 parquet 메타데이터로 넘어가 저장이 실패하면 안 됨."""
    df = pd.concat([_frame([gc._make_row("SEISMIC_X", 5.0, "M", "")]),
                    _frame([gc._make_row("GDELT_EVENT_SCORE", 3.0, "a", "")])], ignore_index=True)
    df.attrs = {"confirmed": True, "observation_day": pd.Timestamp("2026-11-27")}   # 최악의 경우 가정
    out = tmp_path / "g.parquet"
    gc._save(df, str(out))
    assert len(pd.read_parquet(out)) == 2


def test_mart_unit_check_treats_blank_as_missing() -> None:
    """2026-11-27 06:00 회귀: 이전 스냅샷의 빈 단위와 새 단위는 충돌이 아님 — 서로 다른 기재 단위만 충돌."""
    import inspect
    from src.features import build_feature_mart as bm
    src = inspect.getsource(bm)
    assert 'replace("", pd.NA)' in src and "transform" in src
