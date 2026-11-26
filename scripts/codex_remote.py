"""runner → Codex 검증 컨테이너 호출(SPEC §3.8).

    python scripts/codex_remote.py data | semantic

검증 컨테이너가 없으면(노트북 개발 환경 등) 건너뜀(0). 보고서를 reports/ops/codex_verify_<단계>_<날짜>.md로 옮겨
실행 요약 메일·실행 보고가 기존 경로에서 읽게 한다.
"""
from __future__ import annotations

import os
import shutil
import sys
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("CODEX_WORK_HOST", str(ROOT / "codex_work")))
URL = os.environ.get("CODEX_VERIFIER_URL", "http://codex-verifier:8000")
TIMEOUT_S = float(os.environ.get("CODEX_REMOTE_TIMEOUT_S", "3600"))


def main(stage: str) -> int:
    headers = {"X-Runner-Token": os.environ.get("VERIFIER_TOKEN", "")}
    try:
        r = httpx.post(f"{URL}/run/codex_verify_{stage}", headers=headers,
                       timeout=httpx.Timeout(TIMEOUT_S, connect=10))
    except httpx.TransportError as e:
        print(f"[경고] Codex 검증 컨테이너에 연결할 수 없음({type(e).__name__}) — {stage} 검증 미실행")
        return 0
    if r.status_code in (401, 404):
        print(f"[오류] 검증 컨테이너 응답 {r.status_code}: {r.text[:200]}")
        return 1
    body = r.json()
    for s in body.get("steps", []):
        print(s.get("tail", "")[-3000:])
    report = WORK / "out" / stage / "report.md"
    if report.is_file():
        dst = ROOT / "reports" / "ops" / f"codex_verify_{stage}_{date.today():%Y-%m-%d}.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report, dst)
        print(f"[완료] 보고서 → {dst.relative_to(ROOT)}")
    return 1 if body.get("failed") else 0


if __name__ == "__main__":
    s = sys.argv[1] if len(sys.argv) > 1 else ""
    if s not in ("data", "semantic", "investigate"):
        raise SystemExit("[오류] 사용법: codex_remote.py data|semantic|investigate")
    sys.exit(main(s))
