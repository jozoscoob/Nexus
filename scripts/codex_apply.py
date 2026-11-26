"""승인된 Codex 데이터 제안 적용(작업자 수동 실행 — SPEC §3.8). Codex는 이 스크립트를 실행할 수 없다.

    python scripts/codex_apply.py <제안ID>          # 예: 2026-11-27-D1
    python scripts/codex_apply.py <제안ID> --reject # 반려 기록만

순서: 게이트 통과 확인 → 실제 파일 백업(data/snapshots/codex_backup/<날짜>/, 14일 보관) → 수정본으로 교체 →
as-of 게이트(validate_asof) 재검사 → 실패 시 백업으로 즉시 복구.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("CODEX_WORK_HOST", str(ROOT / "codex_work")))
KEEP_DAYS = yaml.safe_load((ROOT / "config" / "codex_data_access.yaml").read_text(encoding="utf-8"))[
    "snapshot_keep_days"]
BACKUP = ROOT / "data" / "snapshots" / "codex_backup"


def _prune() -> None:
    cutoff = date.today() - timedelta(days=KEEP_DAYS)
    for d in BACKUP.glob("*"):
        try:
            if datetime.strptime(d.name, "%Y-%m-%d").date() < cutoff:
                shutil.rmtree(d)
        except ValueError:
            continue


def main(pid: str, reject: bool) -> int:
    pending_p = WORK / "queue" / "pending.json"
    pending = json.loads(pending_p.read_text(encoding="utf-8")) if pending_p.is_file() else []
    item = next((x for x in pending if x["id"] == pid), None)
    if item is None or item.get("status") != "승인 대기":
        raise SystemExit(f"[오류] 승인 대기 중인 제안이 아님: {pid}")
    if reject:
        item.update(status="반려", decided_at=datetime.now().isoformat(timespec="seconds"))
    elif item["kind"] != "data":
        raise SystemExit("[오류] 시맨틱 제안은 YAML을 직접 편집해 반영(검증: validate_semantic_layer --strict)")
    else:
        src = WORK / "queue" / pid / item["file"]
        real = ROOT / "data" / "raw" / item["file"]
        bak = BACKUP / f"{date.today():%Y-%m-%d}" / pid / item["file"]
        bak.parent.mkdir(parents=True, exist_ok=True)

        def _asof() -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "scripts/validate_asof.py"], cwd=ROOT, capture_output=True, text=True)

        before = _asof().returncode            # 적용 전부터 실패하던 게이트는 이번 제안 탓으로 보지 않음
        shutil.copy2(real, bak)
        shutil.copy2(src, real)
        chk = _asof()
        if chk.returncode and not before:
            shutil.copy2(bak, real)
            print(chk.stdout[-1500:])
            raise SystemExit(f"[오류] 적용 후 as-of 게이트 실패 — 백업으로 복구함: {item['file']}")
        item.update(status="적용", decided_at=datetime.now().isoformat(timespec="seconds"),
                    backup=str(bak.relative_to(ROOT)))
        _prune()
    pending_p.write_text(json.dumps(pending, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[완료] {pid} → {item['status']}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("[오류] 사용법: codex_apply.py <제안ID> [--reject]")
    sys.exit(main(sys.argv[1], "--reject" in sys.argv))
