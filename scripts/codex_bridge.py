"""Codex 연동 다리 — 승인자가 Codex로 만드는 비정형 크롤러·교차검증 도구를 n8n 파이프라인에 끼우는 계약.

사용(runner 작업 codex_crawl / codex_verify가 호출):
  python scripts/codex_bridge.py crawl    # 크롤러 실행 → 산출물 계약 검증
  python scripts/codex_bridge.py verify   # 당일 산출물 교차검증(읽기 전용)

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


def _today_outputs() -> list[str]:
    today = date.today()
    out = []
    for pat in ("reports/market/*.md", "reports/g2_preview/*.html", "data/processed/*.json"):
        for f in glob.glob(str(ROOT / pat)):
            if datetime.fromtimestamp(Path(f).stat().st_mtime).date() == today:
                out.append(str(Path(f).relative_to(ROOT)))
    return sorted(out)


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
    if mode not in ("crawl", "verify"):
        raise SystemExit("[오류] 사용법: codex_bridge.py crawl|verify")
    sys.exit(crawl() if mode == "crawl" else verify())
