"""Codex 연동 다리 — 승인자가 Codex로 만드는 비정형 크롤러·교차검증 도구를 n8n 파이프라인에 끼우는 계약.

사용(runner 작업 codex_crawl / codex_verify가 호출):
  python scripts/codex_bridge.py crawl    # 크롤러 실행 → 산출물 계약 검증
  python scripts/codex_bridge.py verify   # 당일 산출물 교차검증(읽기 전용)
  python scripts/codex_bridge.py verify collect|process|analyze   # 단계별 교차검증(산출물+코드+점검표)

설정(로컬 .env — 값은 커밋하지 않음):
  CODEX_CRAWLER_CMD   크롤러 실행 명령(예: "python tools/crawler/run.py"). 비어 있으면 crawl은 건너뜀.
  CODEX_VERIFY_CMD    교차검증 명령. 비어 있으면 PATH에 `codex` CLI가 있을 때 `codex exec`(읽기 전용 샌드박스)로 대체,
                      그것도 없으면 건너뜀.

크롤러 산출물 계약(data/processed/unstructured_crawl_*.parquet — 최신 파일 1개 검증):
  - as-of 필드: event_time, release_time, available_at, ingested_at, source_vintage (D-023)
  - 출처 필드: source_name, source_url, retrieved_at, content_sha256 (출처 추적·중복 판별)
  - available_at ≥ event_time, 미래 available_at 금지
건너뜀은 성공(0)으로 끝내고 사유를 남긴다. 계약 위반·실행 실패는 1 — n8n이 실패 알림을 보낸다.
외부 도구 실행(오케스트레이션)에만 subprocess를 쓰며, 데이터 읽기는 pandas로 한다.
"""
from __future__ import annotations

import glob
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "reports" / "ops"
CRAWL_GLOB = str(ROOT / "data" / "processed" / "unstructured_crawl_*.parquet")
ASOF_FIELDS = ["event_time", "release_time", "available_at", "ingested_at", "source_vintage"]
PROVENANCE_FIELDS = ["source_name", "source_url", "retrieved_at", "content_sha256"]
TIMEOUT_S = int(os.environ.get("CODEX_TIMEOUT_S", "1800"))
VERIFY_PROMPT = (
    "You are a read-only reviewer for the Nexus soybean-oil data pipeline. Review the files listed below, produced today. "
    "Check: (1) every dataset keeps as-of fields and no value is used before its available_at; (2) numbers in reports match "
    "their source tables; (3) wording makes no probability or buy/hold claims. Report findings as a Korean markdown list "
    "with file path and severity (치명/높음/참고). Do not modify any file.\n\nFiles:\n"
)


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT_S)


def check_contract(path: str) -> list[str]:
    df = pd.read_parquet(path)
    problems = [f"필드 누락: {c}" for c in ASOF_FIELDS + PROVENANCE_FIELDS if c not in df.columns]
    if problems:
        return problems
    ev, av = pd.to_datetime(df["event_time"]), pd.to_datetime(df["available_at"])
    if (av < ev).any():
        problems.append(f"available_at < event_time {int((av < ev).sum())}행")
    if (av > pd.Timestamp.now() + pd.Timedelta(days=1)).any():
        problems.append("미래 available_at 존재")
    if df["source_url"].isna().any():
        problems.append(f"source_url 결측 {int(df['source_url'].isna().sum())}행")
    return problems


def crawl() -> int:
    cmd = os.environ.get("CODEX_CRAWLER_CMD", "").strip()
    if not cmd:
        print("[정보] CODEX_CRAWLER_CMD 미설정 — 크롤러 단계 건너뜀(도구 완성 후 .env에 등록)")
        return 0
    proc = _run(shlex.split(cmd))
    print(proc.stdout[-3000:], proc.stderr[-2000:])
    if proc.returncode != 0:
        print(f"[오류] 크롤러 종료 코드 {proc.returncode}")
        return 1
    files = sorted(glob.glob(CRAWL_GLOB))
    if not files:
        print("[오류] 크롤러 산출물 없음 — data/processed/unstructured_crawl_*.parquet 계약 확인")
        return 1
    problems = check_contract(files[-1])
    if problems:
        print(f"[오류] 산출물 계약 위반({Path(files[-1]).name}): " + " · ".join(problems))
        return 1
    print(f"[완료] 크롤러 산출물 계약 통과 — {Path(files[-1]).name}")
    return 0


# 단계별 교차검증 범위 — 산출물(오늘 갱신분) + 그 산출물을 만든 코드 + 단계 점검표
STAGES: dict[str, dict] = {
    "collect": {
        "outputs": ["data/raw/*.parquet", "data/processed/unstructured_daily_signals.csv", "docker/logs/collect_free_*.log"],
        "code": ["src/pipeline/connectors/*_connector.py", "src/pipeline/asof.py"],
        "checks": "(a) every collected parquet has price_date, indicator_code, value and the as-of fields "
                  "event_time/available_at/ingested_at; (b) no duplicate (price_date, indicator_code) rows that would make "
                  "an as-of join pick an arbitrary value; (c) available_at is never earlier than event_time and never in the "
                  "future; (d) connector errors are not silently reported as success (empty frames, swallowed exceptions).",
    },
    "process": {
        "outputs": ["data/gold/feature_contract.yaml", "reports/market/feature_mart_*.md",
                    "reports/market/data_readiness_*.md", "reports/market/session_close_validation_*.md",
                    "docker/logs/mart_*.log", "docker/logs/manual_parsers_*.log"],
        "code": ["src/features/build_feature_mart.py", "src/pipeline/asof.py", "scripts/validate_asof.py",
                 "scripts/validate_session_close.py", "scripts/data_readiness.py"],
        "checks": "(a) the feature mart joins each indicator with available_at <= t (no forward-fill from period start); "
                  "(b) value conflicts fail hard instead of being resolved silently; (c) target columns (target_*) are never "
                  "used as features; (d) the target series is the CME settlement with time_basis checks; (e) parquet at "
                  "data/gold/feature_mart.parquet can be inspected with pandas to confirm (a)-(c).",
    },
    "analyze": {
        "outputs": ["reports/market/g2_band_backtest_*.md", "reports/g2_preview/g2_preview_latest.html",
                    "reports/g2_preview/band_method_compare.json", "reports/market/g1_*.md"],
        "code": ["src/evaluation/band_backtest.py", "scripts/g2_band_method_compare.py", "src/reporting/g2_preview.py",
                 "src/logistics/route_scenarios.py"],
        "checks": "(a) walk-forward evaluation uses only information realized by t (calibration pairs with s+h <= t); "
                  "(b) every number on the G2 page matches its source table or JSON; (c) coverage/width/pinball are computed "
                  "as documented; (d) page wording makes no probability promise or buy/hold recommendation.",
    },
}
STAGE_PROMPT = (
    "You are a read-only reviewer for the Nexus soybean-oil data pipeline, stage '{stage}'. Inspect the outputs and the code "
    "that produced them (you may run read-only Python/pandas to open parquet files). Checks: {checks} Report findings as a "
    "Korean markdown table: 파일 | 심각도(치명/높음/참고) | 내용 | 근거(줄·값). If nothing is wrong, say so per check. "
    "Do not modify any file.\n\nOutputs updated today:\n{outputs}\n\nCode:\n{code}\n"
)


def _today(paths: list[str]) -> list[str]:
    today, out = date.today(), []
    for pat in paths:
        for f in glob.glob(str(ROOT / pat)):
            if datetime.fromtimestamp(Path(f).stat().st_mtime).date() == today:
                out.append(str(Path(f).relative_to(ROOT)).replace("\\", "/"))
    return sorted(out)


def _today_outputs() -> list[str]:
    return _today(["reports/market/*.md", "reports/g2_preview/*.html", "data/processed/*.json"])


def _codex_cmd(prompt: str) -> list[str] | None:
    """codex CLI와 로그인(CODEX_HOME/auth.json)이 모두 있을 때만 실행 — 로그인 없는 서버에서는 건너뜀(비치명)."""
    auth = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
    if shutil.which("codex") and auth.is_file() and auth.stat().st_size > 0:
        return ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt]
    return None


def verify_stage(stage: str) -> int:
    spec = STAGES[stage]
    outputs = _today(spec["outputs"])
    if not outputs:
        print(f"[정보] '{stage}' 단계 오늘 갱신된 산출물 없음 — 교차검증 건너뜀")
        return 0
    code = sorted({str(Path(f).relative_to(ROOT)).replace("\\", "/") for pat in spec["code"]
                   for f in glob.glob(str(ROOT / pat))})
    cmd = _codex_cmd(STAGE_PROMPT.format(stage=stage, checks=spec["checks"], outputs="\n".join(outputs[:60]),
                                         code="\n".join(code)))
    if cmd is None:
        print("[정보] codex CLI 또는 로그인 없음 — 교차검증 건너뜀")
        return 0
    proc = _run(cmd)
    OPS.mkdir(parents=True, exist_ok=True)
    out = OPS / f"codex_verify_{stage}_{date.today():%Y-%m-%d}.md"
    out.write_text(f"# Codex 교차검증 — {stage} 단계 · {date.today()}\n\n산출물 {len(outputs)}건 · 코드 {len(code)}건 · "
                   f"종료 코드 {proc.returncode}\n\n{proc.stdout}\n", encoding="utf-8")
    print(f"[{'완료' if proc.returncode == 0 else '오류'}] {stage} 교차검증 → {out}")
    print(proc.stdout[-2500:])
    return 0 if proc.returncode == 0 else 1


# ── SPEC §3.2 / §3.7: 정형 데이터는 요약 통계만, 비정형·시맨틱은 전체 열람 ─────────────────────────────
DATA_CODE = ["src/pipeline/connectors/*_connector.py", "src/pipeline/asof.py", "src/features/build_feature_mart.py",
             "scripts/validate_asof.py", "scripts/validate_session_close.py", "scripts/data_readiness.py"]
DATA_PROMPT = (
    "You are a read-only reviewer for the Nexus soybean-oil data pipeline. LICENSED DATA RULE: do NOT open any file under "
    "data/ and do NOT print raw price or market values. Review ONLY the per-file summary statistics JSON below and the code. "
    "Checks: (a) every dataset keeps the as-of fields (use asof_fields_present, not the truncated columns list) and has "
    "zero available_at<event_time and zero future available_at; (b) duplicate keys (dup_key_columns) and null rates look "
    "sane — layers with mart_excluded=true are not model inputs, so treat their duplicates as reference only;(c) date coverage per source is fresh for its "
    "release cycle; (d) the code would not silently report a failed source as success. Report a Korean markdown table: "
    "파일 | 심각도(치명/높음/참고) | 내용 | 근거(통계 키·코드 줄). Do not modify any file.\n\nSummary JSON:\n{summary}\n\nCode:\n{code}\n"
)
SEMANTIC_INPUTS = ["data/processed/unstructured_daily_signals.csv", "reports/market/daily_unstructured_digest_*.md",
                   "src/semantic/*.yaml", "src/semantic/causal_chains.md", "data/raw/**/Summary/*.md"]
SEMANTIC_PROMPT = (
    "You are the semantic-layer reviewer for the Nexus soybean-oil project. You MAY read the unstructured inputs below in full "
    "(news/RSS digests, daily signals, GAIN/FAO summaries) and the ontology files. Tasks: (1) new terms or events in the last "
    "days that the dictionary (src/semantic/entities.yaml) does not cover; (2) existing terms whose meaning or price direction "
    "seems to be shifting; (3) candidate causal chains (cause → mechanism → soybean-oil price) with the supporting snippet and "
    "file; (4) daily signal indicators with no dictionary or ontology mapping. PROPOSALS ONLY — do not modify any file. Output "
    "Korean markdown: a table per task (항목 | 제안 | 근거 파일·발췌 | 확신도) and, for task 1 and 3, a YAML snippet a human "
    "can paste after review.\n\nInputs:\n{inputs}\n"
)


ASOF_FIELDS = ("event_time", "period_end", "release_time", "available_at", "source_vintage")
IDENTITY_AXES = ("region_code", "country_code", "hs_code", "lead_days", "valid_date")
MART_EXCLUDED = ("climate_forecast",)   # build_feature_mart.EXCLUDE_PREFIXES와 동일 — 마트 미투입 층


def _data_summary() -> dict:
    """라이선스 원값 없이 파일별 구조·품질 통계만 — Codex에 넘기는 유일한 데이터 정보."""
    import re as _re
    latest: dict[str, Path] = {}
    for f in sorted(ROOT.glob("data/raw/**/*.parquet")):
        fam = _re.sub(r"_\d{8}$", "", f.stem)
        if fam not in latest or f.stat().st_mtime > latest[fam].stat().st_mtime:
            latest[fam] = f
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    out = {}
    for fam, f in sorted(latest.items()):
        try:
            df = pd.read_parquet(f)
        except Exception as e:  # 손상 파일 — 요약에 표시
            out[fam] = {"error": type(e).__name__}
            continue
        cols = list(df.columns)
        item = {"file": str(f.relative_to(ROOT)).replace("\\", "/"), "rows": int(len(df)), "n_columns": len(cols),
                "columns": cols[:40],
                # as-of 5필드 존재를 명시 — 열 목록 절단으로 '필드 없음' 오판이 나지 않게(2026-11-24 첫 서버 검증)
                "asof_fields_present": [c for c in ASOF_FIELDS if c in cols],
                "mart_excluded": fam.startswith(MART_EXCLUDED)}
        if "indicator_code" in df.columns:
            item["indicators"] = int(df["indicator_code"].nunique())
        if "price_date" in df.columns:
            d = pd.to_datetime(df["price_date"], errors="coerce")
            item["date_min"], item["date_max"] = str(d.min())[:10], str(d.max())[:10]
        if "value" in df.columns:
            item["value_null_rate"] = round(float(df["value"].isna().mean()), 4)
        if {"indicator_code", "event_time"} <= set(df.columns):
            # 식별 키 = 지표·시점 + 원천이 따로 둔 축(지역·국가·품목·예보 선행일) — 축을 빼면 정상 행이 중복으로 집계됨
            key = ["indicator_code", "event_time"] + [c for c in IDENTITY_AXES if c in cols]
            item["dup_key_columns"] = key
            item["dup_keys"] = int(df.duplicated(key).sum())
        if {"available_at", "event_time"} <= set(df.columns):
            av = pd.to_datetime(df["available_at"], errors="coerce", utc=True).dt.tz_localize(None)
            ev = pd.to_datetime(df["event_time"], errors="coerce", utc=True).dt.tz_localize(None)
            item["available_before_event"] = int((av < ev).sum())
            item["future_available"] = int((av > now + pd.Timedelta(days=1)).sum())
        else:
            item["asof_fields"] = "missing"
        out[fam] = item
    return out


def verify_data() -> int:
    summary = _data_summary()
    OPS.mkdir(parents=True, exist_ok=True)
    sp = OPS / f"codex_data_summary_{date.today():%Y-%m-%d}.json"
    sp.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    code = sorted({str(Path(f).relative_to(ROOT)).replace("\\", "/") for pat in DATA_CODE for f in glob.glob(str(ROOT / pat))})
    cmd = _codex_cmd(DATA_PROMPT.format(summary=json.dumps(summary, ensure_ascii=False)[:60000], code="\n".join(code)))
    return _run_and_save("data", cmd, f"요약 통계 {len(summary)}개 원천 · 코드 {len(code)}건")


def verify_semantic() -> int:
    files = []
    for pat in SEMANTIC_INPUTS:
        hits = sorted(glob.glob(str(ROOT / pat), recursive=True), key=os.path.getmtime)
        files += hits[-40:] if "Summary" in pat else hits[-5:] if "digest" in pat else hits
    rel = [str(Path(f).relative_to(ROOT)).replace("\\", "/") for f in files]
    cmd = _codex_cmd(SEMANTIC_PROMPT.format(inputs="\n".join(rel)))
    return _run_and_save("semantic", cmd, f"비정형·온톨로지 입력 {len(rel)}건")


def _run_and_save(stage: str, cmd: list[str] | None, scope: str) -> int:
    if cmd is None:
        print(f"[경고] codex CLI 또는 로그인 없음 — {stage} 검증 미실행")   # 요약 메일에 '검증 미실행'으로 표시됨
        return 0
    proc = _run(cmd)
    OPS.mkdir(parents=True, exist_ok=True)
    out = OPS / f"codex_verify_{stage}_{date.today():%Y-%m-%d}.md"
    out.write_text(f"# Codex 검증 — {stage} · {date.today()}\n\n{scope} · 종료 코드 {proc.returncode}\n\n{proc.stdout}\n",
                   encoding="utf-8")
    print(f"[{'완료' if proc.returncode == 0 else '오류'}] {stage} 검증 → {out}")
    print(proc.stdout[-2500:])
    return 0 if proc.returncode == 0 else 1


def verify() -> int:
    files = _today_outputs()
    if not files:
        print("[정보] 오늘 생성된 산출물 없음 — 교차검증 건너뜀")
        return 0
    custom = os.environ.get("CODEX_VERIFY_CMD", "").strip()
    if custom:
        cmd = shlex.split(custom) + files
    elif shutil.which("codex"):
        cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", VERIFY_PROMPT + "\n".join(files)]
    else:
        print("[정보] CODEX_VERIFY_CMD 미설정·codex CLI 없음 — 교차검증 건너뜀")
        return 0
    proc = _run(cmd)
    OPS.mkdir(parents=True, exist_ok=True)
    out = OPS / f"codex_verify_{date.today():%Y-%m-%d}.md"
    out.write_text(f"# Codex 교차검증 — {date.today()}\n\n대상 {len(files)}건: " + ", ".join(files)
                   + f"\n\n종료 코드 {proc.returncode}\n\n{proc.stdout}\n", encoding="utf-8")
    print(f"[{'완료' if proc.returncode == 0 else '오류'}] 교차검증 결과 → {out}")
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    stage = sys.argv[2] if len(sys.argv) > 2 else ""
    if mode == "crawl":
        sys.exit(crawl())
    if mode == "verify" and stage == "data":
        sys.exit(verify_data())
    if mode == "verify" and stage == "semantic":
        sys.exit(verify_semantic())
    if mode == "verify" and stage in STAGES:
        sys.exit(verify_stage(stage))
    if mode == "verify" and not stage:
        sys.exit(verify())
    raise SystemExit("[오류] 사용법: codex_bridge.py crawl | verify [data|semantic|collect|process|analyze]")
