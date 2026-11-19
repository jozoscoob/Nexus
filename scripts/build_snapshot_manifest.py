#!/usr/bin/env python3
"""검증된 산출물(data/gold·reports)의 로컬 스냅샷 매니페스트를 만든다.

G2 재현 조건(입력 스냅샷 SHA256·git SHA)을 기록하는 용도. 파일을
`data/snapshots/{snapshot_id}/manifest.json`에 쓰며 원본은 복사하지 않는다(덮어쓰기 금지).
사용: python scripts/build_snapshot_manifest.py data/gold/feature_mart.parquet [--snapshot-id ID] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_ALLOWED_ROOTS = (Path("data/gold"), Path("reports/market"), Path("reports/pipeline"))
SNAPSHOT_DIR = Path("data/snapshots")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_metadata(path: Path) -> dict[str, Any]:
    try:
        relative = path.relative_to(Path.cwd().resolve())
    except ValueError:
        relative = Path(path.name)
    metadata: dict[str, Any] = {
        "path": relative.as_posix(),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }
    if path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
        metadata["rows"] = len(frame)
        metadata["columns"] = [str(column) for column in frame.columns]
    return metadata


def _validated_files(raw_paths: list[str]) -> list[Path]:
    files = [Path(raw).resolve() for raw in raw_paths]
    roots = [root.resolve() for root in DEFAULT_ALLOWED_ROOTS]
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f"[오류] 매니페스트 대상 파일 없음: {path}")
        if not any(path.is_relative_to(root) for root in roots):
            raise ValueError(
                f"[오류] 허용되지 않은 업로드 경로: {path}. "
                f"허용 루트: {[str(root) for root in roots]}")
    return sorted(set(files))


def build_manifest(files: list[Path], snapshot_id: str) -> dict[str, Any]:
    """스냅샷 매니페스트를 생성한다. 비밀정보·계정명은 포함하지 않는다."""
    return {
        "schema_version": "1.0",
        "snapshot_id": snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": os.environ.get("GITHUB_SHA", "local"),
        "source_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "files": [_file_metadata(path) for path in files],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="로컬 스냅샷 매니페스트 생성")
    parser.add_argument("paths", nargs="+", help="data/gold 또는 reports 하위 검증 산출물")
    parser.add_argument("--dry-run", action="store_true", help="매니페스트만 출력하고 저장하지 않음")
    parser.add_argument("--snapshot-id", default=os.environ.get("NEXUS_SNAPSHOT_ID", ""))
    args = parser.parse_args()

    files = _validated_files(args.paths)
    snapshot_id = args.snapshot_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = build_manifest(files, snapshot_id)
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    print(text)
    if args.dry_run:
        return 0
    out = SNAPSHOT_DIR / snapshot_id / "manifest.json"
    if out.exists():
        raise FileExistsError(f"[오류] 스냅샷 매니페스트가 이미 있음(덮어쓰기 금지): {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"[완료] 스냅샷 매니페스트 저장: {out} · {len(files)}개 파일")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
