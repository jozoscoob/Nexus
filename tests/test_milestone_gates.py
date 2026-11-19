"""G1/G2 Preview 진입 조건을 외부 데이터 없이 검증하는 회귀 테스트."""
from __future__ import annotations

import re
import shlex
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from scripts import ingest_databento_bo
from scripts.build_unstructured_timeseries import _as_bool, _records_from_index
from scripts.build_snapshot_manifest import _validated_files, build_manifest
from src.features.build_feature_mart import _validate_target_rows, build_calendar
from src.forecasting.variable_importance_g1 import (
    _lasso_importance,
    _load_g1_feature_mart,
    _require_g1_target,
)
from src.pipeline.asof import ReleaseRule, _release_for, attach_asof
from src.pipeline.validators.c08_dq_validator import (
    _connector_name,
    _score_accuracy,
    _score_completeness,
    _score_consistency,
    _score_skewness,
    _target_contract_alerts,
)


@pytest.fixture
def valid_target_rows() -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-02", periods=1_100)
    return pd.DataFrame(
        {
            "indicator_code": "CBOT_BO_CLOSE",
            "value": pd.Series(range(len(dates)), dtype="float64") + 30.0,
            "price_date": dates,
            "event_time": dates,
            "available_at": dates,
            "target_eligible": True,
            "time_basis": "CME_SESSION",
            "unit": "USc/lb",
            "source_vintage": "test",
        }
    )


@pytest.fixture
def synthetic_feature_mart(tmp_path: Path) -> tuple[Path, Path]:
    dates = pd.bdate_range("2018-01-02", periods=1_100)
    driver = np.sin(np.arange(len(dates)) / 20.0)
    target_returns = pd.Series(driver * 0.01, dtype="float64")
    target_returns.iloc[-20:] = np.nan
    mart = pd.DataFrame(
        {
            "price_date": dates,
            "target_close": 40.0 + np.arange(len(dates)) * 0.01,
            "target_ret20": target_returns,
            "feat_CBOT_BO_CLOSE": 40.0 + np.arange(len(dates)) * 0.01,
            "feat_DRIVER": driver,
            "feat_CONTAMINATED": driver * 2,
            "age_DRIVER": 0.0,
        }
    )
    mart_path = tmp_path / "feature_mart.parquet"
    contract_path = tmp_path / "feature_contract.yaml"
    mart.to_parquet(mart_path, index=False)
    contract = {
        "target": {
            "indicator": "CBOT_BO_CLOSE",
            "target_eligible": True,
            "time_basis": ["CME_SESSION"],
            "unit": ["USc/lb"],
        },
        "features": {
            "feat_CBOT_BO_CLOSE": {"revision_contaminated": False},
            "feat_DRIVER": {"revision_contaminated": False},
            "feat_CONTAMINATED": {"revision_contaminated": True},
        },
    }
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    return mart_path, contract_path


@pytest.fixture
def snapshot_file(tmp_path: Path) -> Path:
    path = tmp_path / "report.json"
    path.write_text('{"status":"PASS"}\n', encoding="utf-8")
    return path


@pytest.fixture
def unstructured_index_file(tmp_path: Path) -> Path:
    path = tmp_path / "unstructured_index_gain.csv"
    pd.DataFrame(
        {
            "file": ["blocked.pdf", "valid.pdf"],
            "path": ["GAIN/2024/01/blocked.pdf", "GAIN/2024/01/valid.pdf"],
            "readable": ["False", "True"],
            "signals": [None, "weather"],
            "bull": [None, 2],
            "bear": [None, 1],
        }
    ).to_csv(path, index=False)
    return path


_RELEASE_WORKFLOWS = (
    ".github/workflows/external_data_refresh.yml",
    ".github/workflows/historical_backfill.yml",
    ".github/workflows/unstructured_analysis.yml",
)

# 발행 워크플로우에서 main 커밋·push가 승인된 잡과, 각 잡이 스테이징할 수 있는 경로 접두사.
# 승인 근거: A-181(일별 비정형 신호 아카이브)·A-284(한국어 헤드라인 캐시)·A-202(E1 스탬프)·
# DQ-23(최신 브리프 배포 브리지)·A-184/A-255(관세청 `_API.xlsx` — 업로드 원본 불변).
# 여기 없는 잡이 contents: write를 선언하거나 push하면 게이트 우회로 간주한다.
_APPROVED_WRITE_JOBS: dict[str, tuple[str, ...]] = {
    "daily-unstructured-digest": ("data/processed/", "data/semantic/events"),
    "signed-daily-stamp": ("data/processed/", "reports/pipeline/latest"),
    "customs-import-stats": ("data/raw/관세청/",),
    "customs-gw-extended": ("data/raw/관세청/",),
}
# data/raw 예외는 API 수집 동반 파일에만 허용 — 업로드 원본·parquet 스테이징 차단(A-184).
_RAW_STAGING_SUFFIX = "_API.xlsx"
_GIT_ADD_RE = re.compile(r"\bgit add\s+([^|&;\n]*)")


def _strip_comments(run_script: str) -> str:
    """run 스크립트에서 주석을 제거한 명령 행만 반환(주석 속 'git push' 오탐 방지)."""
    return "\n".join(line.split("#", 1)[0] for line in run_script.splitlines())


def _job_run_text(job: dict) -> str:
    runs = [step.get("run") for step in job.get("steps") or [] if isinstance(step, dict)]
    return "\n".join(_strip_comments(str(run)) for run in runs if run)


def _grants_contents_write(job: dict) -> bool:
    permissions = job.get("permissions")
    if isinstance(permissions, str):
        return permissions == "write-all"
    return isinstance(permissions, dict) and permissions.get("contents") == "write"


def _staged_paths(run_text: str) -> list[str]:
    """`git add` 인자를 경로 단위로 추출한다(플래그·리다이렉션 제외)."""
    paths: list[str] = []
    for match in _GIT_ADD_RE.finditer(run_text):
        for token in shlex.split(match.group(1)):
            if token.startswith("-"):
                raise AssertionError(f"[오류] git add 플래그({token}) 사용 — 경로를 명시해야 함")
            if ">" in token:
                continue
            paths.append(token)
    return paths


@pytest.fixture
def release_workflow_text() -> str:
    root = Path(__file__).resolve().parents[1]
    return "\n".join(
        (root / relative).read_text(encoding="utf-8") for relative in _RELEASE_WORKFLOWS
    )


@pytest.fixture
def release_workflow_jobs() -> list[tuple[str, str, dict]]:
    """(워크플로우 파일명, 잡 이름, 잡 정의) 목록 — yaml.safe_load 기준."""
    root = Path(__file__).resolve().parents[1]
    jobs: list[tuple[str, str, dict]] = []
    for relative in _RELEASE_WORKFLOWS:
        workflow = yaml.safe_load((root / relative).read_text(encoding="utf-8"))
        top_level = workflow.get("permissions")
        assert not _grants_contents_write({"permissions": top_level}), (
            f"[오류] {relative}: 워크플로우 전역 contents: write 금지 — 잡 단위로 선언해야 함"
        )
        for name, job in (workflow.get("jobs") or {}).items():
            jobs.append((Path(relative).name, name, job))
    assert jobs, "[오류] 발행 워크플로우 잡을 하나도 읽지 못함"
    return jobs


def test_databento_missing_key_is_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.delenv("DATABENTO_FROM_CSV", raising=False)
    with pytest.raises(RuntimeError, match="DATABENTO_API_KEY"):
        ingest_databento_bo.run()


def test_databento_missing_offline_csv_is_fatal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATABENTO_FROM_CSV", str(tmp_path / "missing.csv"))
    with pytest.raises(FileNotFoundError, match="CSV 없음"):
        ingest_databento_bo.run()


def test_databento_utc_output_cannot_be_targeted() -> None:
    source = pd.DataFrame(
        {"price_date": [pd.Timestamp("2026-08-09")], "close": [51.25], "volume": [100]}
    )
    output = ingest_databento_bo._to_long_output(source)
    assert set(output["time_basis"]) == {"UTC_CALENDAR_DAY"}
    assert not output["target_eligible"].any()
    assert set(output["indicator_code"]) == {"CBOT_BO_UTC_CLOSE", "CBOT_BO_UTC_VOLUME"}


def test_feature_mart_rejects_weekend_target(valid_target_rows: pd.DataFrame) -> None:
    broken = valid_target_rows.copy()
    broken.loc[0, ["price_date", "event_time", "available_at"]] = pd.Timestamp("2020-01-05")
    with pytest.raises(RuntimeError, match="주말 거래일"):
        _validate_target_rows(broken, "CBOT_BO_CLOSE")


def test_feature_mart_rejects_utc_target(valid_target_rows: pd.DataFrame) -> None:
    broken = valid_target_rows.copy()
    broken["time_basis"] = "UTC_CALENDAR_DAY"
    with pytest.raises(RuntimeError, match="time_basis"):
        _validate_target_rows(broken, "CBOT_BO_CLOSE")


def test_feature_mart_rejects_inverted_target_availability(
    valid_target_rows: pd.DataFrame,
) -> None:
    broken = valid_target_rows.copy()
    broken.loc[0, "available_at"] = broken.loc[0, "event_time"] - pd.Timedelta(days=1)
    with pytest.raises(RuntimeError, match="available_at"):
        _validate_target_rows(broken, "CBOT_BO_CLOSE")


def test_feature_mart_does_not_fallback_without_target() -> None:
    features = pd.DataFrame(
        {
            "indicator_code": ["CPO_USD_MT"],
            "event_time": [pd.Timestamp("2024-01-02")],
            "available_at": [pd.Timestamp("2024-01-02")],
            "value": [900.0],
            "target_eligible": [False],
            "time_basis": ["MARKET_DAY"],
            "unit": ["USD/MT"],
        }
    )
    with pytest.raises(RuntimeError, match="검증된 목표변수"):
        build_calendar(features, "2024-01-01", "2024-12-31")


def test_g1_rejects_brent_fallback() -> None:
    dates = pd.bdate_range("2020-01-01", periods=1_100)
    brent = pd.DataFrame(
        {"indicator_code": "BRENT_USD_BBL", "price_date": dates, "value": 70.0}
    )
    wide = pd.DataFrame({"BRENT_USD_BBL": 70.0}, index=dates)
    with pytest.raises(RuntimeError, match="대체 타깃"):
        _require_g1_target({"commodity": brent}, wide)


def test_g1_accepts_only_valid_session_target(valid_target_rows: pd.DataFrame) -> None:
    wide = valid_target_rows.pivot(index="price_date", columns="indicator_code", values="value")
    assert _require_g1_target({"target": valid_target_rows}, wide) == "CBOT_BO_CLOSE"


def test_c08_empty_frame_is_rejected_by_all_scored_dimensions() -> None:
    empty = pd.DataFrame()
    assert _score_accuracy(empty, "economic_indicators") == 0.0
    assert _score_completeness(empty) == 0.0
    assert _score_consistency(empty, "economic_indicators") == 0.0
    assert _score_skewness(empty) == 0.0


def test_c08_uses_longest_connector_prefix() -> None:
    assert _connector_name("economic_indicators_20260813") == "economic_indicators"
    assert _connector_name("databento_bo_utc_historical") == "databento_bo_utc_historical"


def test_c08_target_contract_rejects_weekend(valid_target_rows: pd.DataFrame) -> None:
    broken = valid_target_rows.copy()
    broken.loc[0, "price_date"] = pd.Timestamp("2020-01-05")
    assert any("주말" in alert for alert in _target_contract_alerts(broken))


def test_asof_comtrade_delay_applied_once() -> None:
    event = pd.Timestamp("2024-01-31")
    rule = ReleaseRule("lag_days", lag_days=45)
    assert _release_for(event, rule) == event + timedelta(days=45)


def test_utc_bar_available_after_bucket_end() -> None:
    row = pd.DataFrame(
        {
            "price_date": [pd.Timestamp("2024-01-07")],
            "indicator_code": ["CBOT_BO_UTC_CLOSE"],
            "value": [48.0],
        }
    )
    result = attach_asof(row, source="CBOT_BO_UTC_")
    assert result.loc[0, "available_at"] == pd.Timestamp("2024-01-08")


def test_snapshot_manifest_has_lineage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("GITHUB_RUN_ID", "42")
    manifest = build_manifest([], "snapshot-test")
    assert manifest["snapshot_id"] == "snapshot-test"
    assert manifest["source_commit"] == "abc123"
    assert manifest["source_run_id"] == "42"
    assert manifest["files"] == []


def test_snapshot_manifest_records_content_hash(snapshot_file: Path) -> None:
    manifest = build_manifest([snapshot_file], "snapshot-hash")
    assert manifest["files"][0]["bytes"] > 0
    assert len(manifest["files"][0]["sha256"]) == 64


def test_snapshot_rejects_paths_outside_release_roots(snapshot_file: Path) -> None:
    with pytest.raises(ValueError, match="허용되지 않은 업로드 경로"):
        _validated_files([str(snapshot_file)])


def test_unstructured_index_does_not_emit_nan_tags(
    unstructured_index_file: Path,
) -> None:
    records = _records_from_index("gain", unstructured_index_file, "TEST")
    codes = {record["indicator_code"] for record in records}
    assert "UNSTR_GAIN_NAN" not in codes
    assert "UNSTR_GAIN_weather" in codes
    assert _as_bool(pd.Series(["False", "True"])).tolist() == [False, True]


def _needs(job: dict) -> list[str]:
    needs = job.get("needs") or []
    return [needs] if isinstance(needs, str) else list(needs)


def _gated_on_model_readiness(job: dict) -> bool:
    """needs에 model-readiness가 있고 if:가 그 success를 요구해야 게이트로 인정."""
    return "model-readiness" in _needs(job) and (
        "needs.model-readiness.result == 'success'" in str(job.get("if", ""))
    )


def test_release_workflows_do_not_bypass_model_gates(
    release_workflow_text: str, release_workflow_jobs: list[tuple[str, str, dict]]
) -> None:
    forbidden = [
        "validate_asof.py --warn",
        "build_unstructured_timeseries.py || true",
    ]
    for pattern in forbidden:
        assert pattern not in release_workflow_text, f"[오류] 게이트 우회 패턴 잔존: {pattern}"
    # 일별·백필 양쪽 G1 분석 잡이 Model Readiness success에 종속돼야 한다.
    # (구 검사 `needs: [model-readiness]` 리터럴은 일별 잡의 needs 확장으로 1건만 매칭 — 구조 검사로 대체)
    gated = {
        f"{workflow}/{name}"
        for workflow, name, job in release_workflow_jobs
        if name == "g1-analysis" and _gated_on_model_readiness(job)
    }
    assert len(gated) >= 2, f"[오류] Model Readiness 게이트를 통과하는 G1 잡 부족: {gated}"


def _check_write_scope(workflow: str, name: str, job: dict) -> bool:
    """잡 하나의 main 커밋 범위를 검사한다. 쓰기(권한 선언 또는 push) 잡이면 True."""
    run_text = _job_run_text(job)
    pushes = "git push" in run_text
    writes = _grants_contents_write(job)
    if not (pushes or writes):
        assert not _staged_paths(run_text), (
            f"[오류] {workflow}/{name}: 쓰기 권한 없는 잡의 git add — 승인 목록 확인"
        )
        return False
    assert name in _APPROVED_WRITE_JOBS, (
        f"[오류] {workflow}/{name}: 미승인 잡의 contents: write 또는 git push"
    )
    assert not re.search(r"\bgit commit\s+(-a\b|--all\b)", run_text), (
        f"[오류] {workflow}/{name}: git commit -a는 추적 파일 전량 스테이징 — 금지"
    )
    staged = _staged_paths(run_text)
    assert staged, f"[오류] {workflow}/{name}: push 잡인데 git add 경로가 없음"
    for path in staged:
        assert path.startswith(_APPROVED_WRITE_JOBS[name]), (
            f"[오류] {workflow}/{name}: 승인 범위 밖 경로 스테이징 — {path}"
        )
        if path.startswith("data/raw/"):
            assert path.endswith(_RAW_STAGING_SUFFIX), (
                f"[오류] {workflow}/{name}: data/raw는 {_RAW_STAGING_SUFFIX}만 허용 — {path}"
            )
    return True


def test_release_workflows_commit_only_from_approved_jobs(
    release_workflow_jobs: list[tuple[str, str, dict]],
) -> None:
    """main 커밋·push는 승인된 잡(A-181·A-202·DQ-23·A-184·A-255)에서, 승인된 경로만."""
    seen_write_jobs = {
        name for workflow, name, job in release_workflow_jobs
        if _check_write_scope(workflow, name, job)
    }
    # 승인 목록의 잡이 실제로 존재해야 한다 — 잡 개명 시 허용 목록이 조용히 비지 않도록
    assert seen_write_jobs == set(_APPROVED_WRITE_JOBS), (
        f"[오류] 승인 목록과 워크플로우 불일치: {set(_APPROVED_WRITE_JOBS) ^ seen_write_jobs}"
    )


def test_release_workflow_guard_rejects_unapproved_staging() -> None:
    """가드 자체 검증 — 미승인 잡·소스/gold/워크플로우 경로·일괄 스테이징은 반드시 걸린다."""
    push = "git commit -m x && git push origin HEAD:main"
    approved = {"permissions": {"contents": "write"}}

    def job(add: str) -> dict:
        return {**approved, "steps": [{"run": f"git add {add} 2>/dev/null || true\n{push}"}]}

    with pytest.raises(AssertionError, match="미승인 잡"):
        _check_write_scope("w.yml", "g1-analysis", job("data/processed/x.csv"))
    for path in ("src/x.py", "data/gold/feature_mart.parquet", ".github/workflows/a.yml", "."):
        with pytest.raises(AssertionError, match="승인 범위 밖"):
            _check_write_scope("w.yml", "signed-daily-stamp", job(path))
    with pytest.raises(AssertionError, match="_API.xlsx"):
        _check_write_scope("w.yml", "customs-gw-extended", job("data/raw/관세청/upload.xlsx"))
    with pytest.raises(AssertionError, match="플래그"):
        _check_write_scope("w.yml", "signed-daily-stamp", job("-A"))
    with pytest.raises(AssertionError, match="commit -a"):
        _check_write_scope(
            "w.yml", "signed-daily-stamp", {**approved, "steps": [{"run": "git commit -a -m x"}]}
        )
    # 쓰기 권한도 push도 없는 잡의 git add 역시 차단
    with pytest.raises(AssertionError, match="쓰기 권한 없는"):
        _check_write_scope("w.yml", "geointel", {"steps": [{"run": "git add data/processed/a"}]})
    # 정상 경로: 승인 잡 + 승인 경로(따옴표·리다이렉션·|| 폴백 포함)는 통과
    assert _check_write_scope(
        "w.yml",
        "daily-unstructured-digest",
        job('data/processed/a.csv "data/semantic/events" || git add data/processed/b.json'),
    )
    # 주석 속 'git push'는 push로 세지 않는다
    assert "git push" not in _job_run_text(
        {"steps": [{"run": "echo ok   # D-026 신규 git push 저장소 금지"}]}
    )


def test_g1_loads_only_asof_noncontaminated_features(
    synthetic_feature_mart: tuple[Path, Path],
) -> None:
    mart_path, contract_path = synthetic_feature_mart
    analysis, levels, target = _load_g1_feature_mart(
        mart_path=mart_path, contract_path=contract_path, horizon=20
    )
    assert target == "target_ret20"
    assert list(analysis.columns) == ["target_ret20", "DRIVER"]
    assert "CBOT_BO_CLOSE" in levels.columns


def test_elasticnet_uses_walk_forward_splits() -> None:
    from sklearn.model_selection import TimeSeriesSplit

    dates = pd.bdate_range("2020-01-02", periods=240)
    x1 = np.sin(np.arange(len(dates)) / 8.0)
    x2 = np.cos(np.arange(len(dates)) / 12.0)
    wide = pd.DataFrame(
        {"target_ret20": 0.8 * x1 - 0.2 * x2, "driver_a": x1, "driver_b": x2},
        index=dates,
    )
    result = _lasso_importance(wide, "target_ret20")
    assert not result.empty
    for train, test in TimeSeriesSplit(n_splits=5, gap=20).split(wide):
        assert dates[train].max() < dates[test].min()

def test_forecast_rows_available_at_capped_at_ingestion():
    """A-195: 마케팅연도 전망 행의 available_at은 수집 시점을 넘을 수 없다.

    구 결함: same_month 규칙이 기간 라벨(미래 MY)에서 발표일을 앞으로 파생해
    미래 available_at 871건 생성 — 이미 보유한 데이터가 '미래에 가용'으로 표기됨.
    """
    import pandas as pd
    from src.pipeline.asof import attach_asof, leak_inversions

    now = pd.Timestamp.utcnow().tz_localize(None)
    df = pd.DataFrame({
        "price_date": pd.to_datetime(["2025-10-01", "2026-10-01"]),   # 과거 MY · 전망 MY
        "indicator_code": ["PSD_Production"] * 2,
        "value": [1.0, 2.0],
        "ingested_at": [now, now],
    })
    out = attach_asof(df, source="WASDE_")
    # 과거 행: same_month 규칙 유지 (해당 월 12일 발표)
    assert out.loc[0, "available_at"] == pd.Timestamp("2025-10-12")
    # 전망 행: 수집 시점으로 캡 — 미래 금지
    assert out.loc[1, "available_at"] <= now + pd.Timedelta(seconds=1)
    # 전망 행의 available_at < event_time 역전은 공용 판정에서 누수로 세지 않는다
    assert int(leak_inversions(out).sum()) == 0

