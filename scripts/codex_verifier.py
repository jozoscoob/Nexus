"""Codex 검증 — 격리 컨테이너 안에서 실행(SPEC §3.8).

    python scripts/codex_verifier.py data | semantic

이 컨테이너가 볼 수 있는 것(그 밖의 파일·키·데이터는 마운트되지 않아 존재하지 않음):
  /work/inputs   읽기 전용 — 공개 데이터 사본·전체 요약 통계(제한 원천 포함, 통계만)·비정형 입력
  /work/staging  쓰기 가능 — 버려도 되는 공개 데이터 사본(수정 시험용, 매 실행 새로 만듦)
  /work/out      쓰기 가능 — 보고서·제안
  /repo/src · /repo/scripts · /repo/config   읽기 전용 코드
격리는 컨테이너가 담당하므로 Codex 자체 샌드박스는 끈다(Docker 기본 보안 설정은 그대로).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

WORK = Path(os.environ.get("CODEX_WORK", "/work"))
TIMEOUT_S = int(os.environ.get("CODEX_TIMEOUT_S", "1800"))

COMMON = (
    "You are the read-only reviewer for the Nexus soybean-oil procurement pipeline, running in an isolated "
    "container. Layout: /work/inputs is READ-ONLY input; /work/staging is a throwaway writable copy you may "
    "change to test fixes; /work/out is where you write results; /repo/src, /repo/scripts, /repo/config are "
    "read-only code. There is nothing else to find: no API keys, no other data. Never try to reach any network "
    "address except your own API. Write all prose in Korean.\n"
)
DATA_PROMPT = COMMON + (
    "TASK: verify the structured data. Read /work/inputs/manifest_data.json first. scope=daily means focus on "
    "public_files with changed_today=true (skim the rest); scope=weekly_full means check every public file. "
    "Public files under /work/inputs/public may be read in full (pandas/pyarrow are installed). Families in "
    "restricted_families_stats_only are licensed: you only have their statistics in "
    "/work/inputs/data_summary.json — do not ask for or guess their values. "
    "Checks: (a) as-of fields event_time, release_time, available_at, source_vintage present; no "
    "available_at < event_time; no future available_at; (b) duplicate keys using dup_key_columns from the summary "
    "(layers with mart_excluded=true are reference-only); (c) units, scales, date gaps, stale sources versus "
    "their release cycle; (d) code paths in /repo/src/pipeline that could report a failed source as success. "
    "If you can fix a data problem, write the corrected file to the SAME relative path under "
    "/work/staging/public and record it. OUTPUT FILES: (1) /work/out/data/proposals.json — a JSON list of "
    "objects {\"file\": <path relative to public/>, \"problem\": str, \"fix\": str, \"severity\": "
    "\"치명\"|\"높음\"|\"참고\", \"staging_written\": true|false}; use [] if none. (2) optional code patches as "
    "unified diffs in /work/out/data/patches/*.diff. Finally print a Korean markdown table to stdout: "
    "파일 | 심각도(치명/높음/참고) | 내용 | 근거(통계 키·코드 줄·행 예시).\n"
)
SEMANTIC_PROMPT = COMMON + (
    "TASK: semantic/ontology review. Read /work/inputs/manifest_semantic.json; the unstructured inputs (news/RSS "
    "digests, daily signals, GAIN/FAO summaries) are under /work/inputs/semantic and may be read in full; the "
    "dictionary and ontology are read-only at /repo/src/semantic. Find: (1) new terms or events not covered by "
    "entities.yaml; (2) existing terms whose meaning or price direction seems to shift; (3) candidate causal "
    "chains (cause -> mechanism -> soybean-oil price) with the supporting snippet and file; (4) daily signal "
    "indicators with no dictionary or ontology mapping. PROPOSALS ONLY. OUTPUT FILE: "
    "/work/out/semantic/proposals.yaml with keys entity_proposals, causal_chain_proposals, mapping_gaps "
    "(lists; each item has id, proposal, evidence_file, evidence_quote, confidence). Then print a Korean "
    "markdown table per task to stdout: 항목 | 제안 | 근거 파일·발췌 | 확신도.\n"
)


INVESTIGATE_PROMPT = COMMON + (
    "TASK: root-cause investigation — do NOT just restate symptoms. Inputs: /work/inputs/investigate/"
    "run_warnings.txt (warnings/errors from the last pipeline runs), today's data review and proposals in the same "
    "folder, public data copies under /work/inputs/public, code under /repo. Investigate at least these, then any "
    "other RECURRING problem you find in run_warnings.txt (collection, processing, refinement, analysis): "
    "(A) FRED economic_indicators rows saved with an empty unit; (B) GeoIntel rows whose event date is after "
    "available_at, and the GeoIntel composite risk counting unconfirmed/failed signals as 0; (C) repeated "
    "price_date derivation failures and dropped rows in the customs connector; (D) the FRED 400 'series missing' "
    "warning; (E) any analysis/quality-step warnings. For each item give: the definitive root cause with evidence "
    "(file:line and the exact code, plus a data row or log line), whether it is a code defect, an external-source "
    "issue or a missing key/config, and the smallest correct fix. For code defects write a unified diff against "
    "/repo paths to /work/out/investigate/patches/<ID>.diff (do not apply it). Write /work/out/investigate/"
    "findings.json: a list of {id, title, category: code|external|config, root_cause, evidence, fix, "
    "patch_file|null, test_idea}. Then print a Korean markdown table: ID | 제목 | 분류 | 근본 원인 | 근거 | 수정안.\n"
)


def _codex_ready() -> bool:
    auth = Path(os.environ.get("CODEX_HOME", "/root/.codex")) / "auth.json"
    return bool(shutil.which("codex")) and auth.is_file() and auth.stat().st_size > 0


def run(stage: str) -> int:
    out = WORK / "out" / stage
    out.mkdir(parents=True, exist_ok=True)
    manifest = WORK / "inputs" / ("investigate/run_warnings.txt" if stage == "investigate" else f"manifest_{stage}.json")
    if not manifest.is_file():
        print(f"[오류] 입력 준비 안 됨: {manifest} — runner의 codex_prepare가 먼저 실행돼야 함")
        return 1
    if not _codex_ready():
        print(f"[경고] codex CLI 또는 로그인 없음 — {stage} 검증 미실행")
        return 0
    prompt = {"data": DATA_PROMPT, "semantic": SEMANTIC_PROMPT, "investigate": INVESTIGATE_PROMPT}[stage]
    cmd = ["codex", "exec", "--sandbox", "danger-full-access", "--skip-git-repo-check", "-C", str(WORK), prompt]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S, cwd=str(WORK))
    (out / "report.md").write_text(
        f"# Codex 검증 — {stage} · {date.today()}\n\n격리 컨테이너 실행 · 종료 코드 {proc.returncode}\n\n"
        f"{proc.stdout}\n", encoding="utf-8")
    print(f"[{'완료' if proc.returncode == 0 else '오류'}] {stage} 검증 → {out / 'report.md'}")
    print(proc.stdout[-2500:])
    if proc.returncode:
        print(proc.stderr[-1500:])
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    s = sys.argv[1] if len(sys.argv) > 1 else ""
    if s not in ("data", "semantic", "investigate"):
        raise SystemExit("[오류] 사용법: codex_verifier.py data|semantic|investigate")
    sys.exit(run(s))
