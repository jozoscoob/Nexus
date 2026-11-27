"""보고서 Google Drive 저장 — 승인자 승인(2026-11-26), 범위 drive.file(rclone이 만든 폴더·파일만 접근).

    python scripts/drive_upload.py                    # 오늘(KST) 보고서
    python scripts/drive_upload.py --date 2026-11-24  # 특정 날짜
    python scripts/drive_upload.py --backfill-month 2026-11 [--extra DIR]   # 그 달 전체 재업로드

Drive 구조(승인자 지정 2026-11-27): <보고서>/G1/YYYY년/M월/YYYY-MM-DD/ — 연·월 폴더는 바뀔 때 자동 생성 — 원격 루트는 rclone 설정의 root_folder_id(앱이 만든 'Nexus Reports'
폴더 ID)라서 승인자가 그 폴더를 원하는 위치로 옮겨도 계속 동작한다. 링크는 공유 링크가 아닌 폴더 주소(승인자 계정만 열람).
올리는 것: G1 보고서(요약 미포함 원본)·G1 경보·일별 브리프, 실행 보고, 실행 요약, Codex 검증·제안 보고서.
결과 링크: reports/ops/drive_links_<날짜>.json(실행 요약 메일이 읽음). rclone·원격 미설정이면 건너뜀(0).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "reports" / "ops"
PIPE = ROOT / "reports" / "pipeline"
REMOTE = os.environ.get("NEXUS_DRIVE_REMOTE", "nexusdrive")
CATEGORY = os.environ.get("NEXUS_DRIVE_CATEGORY", "G1")
DRY_RUN = os.environ.get("NEXUS_DRIVE_DRY_RUN") == "1"
KST = ZoneInfo(os.environ.get("TZ", "Asia/Seoul"))
G1_PATTERNS = ("g1_variable_importance_*_ko.html", "g1_variable_importance_*_en.html",
               "g1_variable_importance_*_ko.md", "g1_daily_brief_*.html", "g1_alert_*.md")
OPS_FILES = ("codex_verify_data_{d}.md", "codex_verify_semantic_{d}.md", "codex_verify_investigate_{d}.md",
             "codex_proposals_{d}.md")


def _rclone(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["rclone", *args], capture_output=True, text=True, timeout=900)


def _ready() -> bool:
    if not shutil.which("rclone"):
        print("[경고] rclone 미설치 — Drive 저장 건너뜀")
        return False
    remotes = _rclone("listremotes").stdout.split()
    if f"{REMOTE}:" not in remotes:
        print(f"[경고] Drive 원격 '{REMOTE}' 미설정 — Drive 저장 건너뜀(승인자 1회 로그인 필요)")
        return False
    return True


def _kst_day(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, KST).strftime("%Y-%m-%d")


def _collect(day: str, extra: list[Path]) -> list[tuple[Path, str]]:
    """(원본 경로, Drive 파일명) — G1 원본은 이름 그대로, 날짜 없는 파일은 날짜를 붙여 보존."""
    out: list[tuple[Path, str]] = []
    for base in [PIPE, *extra]:
        for pat in G1_PATTERNS:
            out += [(p, p.name) for p in sorted(base.glob(pat)) if _kst_day(p) == day]
    for name in OPS_FILES:
        p = OPS / name.format(d=day)
        if p.is_file():
            out.append((p, p.name))
    summ = OPS / f"daily_summary_{day}.json"
    if summ.is_file():
        out.append((summ, f"run_summary_{day}.json"))
    run_html = OPS / "pipeline_run_latest.html"
    if run_html.is_file() and _kst_day(run_html) == day:      # 매일 덮어쓰는 파일 — 그날 사본을 날짜 이름으로 보존
        out.append((run_html, f"pipeline_run_{day}.html"))
    return out


def _day_dir(day: str) -> tuple[str, str]:
    """(부모 경로, 날짜 폴더명) — 예: ('G1/2026년/11월', '2026-11-27'). 월은 0 없이(승인자 표기 '11월')."""
    y, m, _ = day.split("-")
    return f"{CATEGORY}/{y}년/{int(m)}월", day


def _folder_url(parent: str, day: str) -> str | None:
    r = _rclone("lsjson", f"{REMOTE}:{parent}", "--dirs-only")
    try:
        for item in json.loads(r.stdout or "[]"):
            if item.get("Name") == day and item.get("ID"):
                return f"https://drive.google.com/drive/folders/{item['ID']}"
    except json.JSONDecodeError:
        pass
    return None


def upload(day: str, extra: list[Path]) -> int:
    files = _collect(day, extra)
    if not files:
        print(f"[정보] {day} 올릴 보고서 없음")
        return 0
    parent, folder = _day_dir(day)
    if DRY_RUN:
        print(f"[정보] (시험) {REMOTE}:{parent}/{folder}/ ← {', '.join(n for _, n in files)}")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        for src, name in files:
            shutil.copy2(src, Path(tmp) / name)
        r = _rclone("copy", tmp, f"{REMOTE}:{parent}/{folder}", "--no-traverse")
    if r.returncode:
        print(f"[오류] Drive 업로드 실패({day}): {r.stderr.strip()[-400:]}")
        return 1
    url = _folder_url(parent, folder)
    OPS.mkdir(parents=True, exist_ok=True)
    (OPS / f"drive_links_{day}.json").write_text(json.dumps(
        {"date": day, "folder_url": url, "files": [n for _, n in files]}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"[완료] Drive {parent}/{folder} — {len(files)}개 파일 · 폴더 {url or '(링크 확인 실패)'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--backfill-month")
    ap.add_argument("--extra", action="append", default=[], help="추가로 훑을 G1 보고서 폴더(백필용)")
    a = ap.parse_args()
    if not _ready():
        return 0
    extra = [Path(x) for x in a.extra]
    if a.backfill_month:
        days = sorted({_kst_day(p) for base in [PIPE, *extra] for pat in G1_PATTERNS for p in base.glob(pat)}
                      | {p.stem.rsplit("_", 1)[-1] for p in OPS.glob("daily_summary_*.json")})
        days = [d for d in days if d.startswith(a.backfill_month)]
        print(f"[정보] 백필 {a.backfill_month}: {', '.join(days)}")
        return max((upload(d, extra) for d in days), default=0)
    return upload(a.date or datetime.now(KST).strftime("%Y-%m-%d"), extra)


if __name__ == "__main__":
    sys.exit(main())
