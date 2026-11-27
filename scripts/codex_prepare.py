"""Codex 검증 컨테이너 입력 준비(runner 측) — SPEC §3.8.

    python scripts/codex_prepare.py data       # 공개 데이터 사본 + 전체 요약 통계 + 스테이징 사본
    python scripts/codex_prepare.py semantic   # 비정형 요약·다이제스트·신호 사본

codex_work/ (gitignore)
  inputs/   검증 컨테이너에 읽기 전용으로 보임 — 공개 데이터 사본·요약 통계·비정형 입력만
  staging/  검증 컨테이너가 쓸 수 있는 버려도 되는 사본 — 매 실행 새로 만듦
  out/      검증 컨테이너의 보고서·제안 파일
  queue/    게이트 통과 제안 보관(runner 전용 — 검증 컨테이너에 마운트하지 않음)
라이선스·재배포 제한 원천(config/codex_data_access.yaml)은 파일 사본을 만들지 않고 요약 통계만 넘긴다.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from codex_bridge import SEMANTIC_INPUTS, _data_summary  # noqa: E402

WORK = Path(os.environ.get("CODEX_WORK_HOST", str(ROOT / "codex_work")))
CFG = yaml.safe_load((ROOT / "config" / "codex_data_access.yaml").read_text(encoding="utf-8"))


def _restricted(path: Path) -> bool:
    """경로 또는 source_name에 제한 표지가 있으면 True — 읽기 실패 시에도 제한으로 본다(거부 우선)."""
    marks = [m.lower() for m in CFG["restricted"]]
    if any(m in str(path).lower() for m in marks):
        return True
    try:
        df = pd.read_parquet(path, columns=["source_name"])
    except Exception:
        try:
            pd.read_parquet(path, columns=[])
            return False            # source_name 열이 없는 정상 파일 — 경로 판정만 적용
        except Exception:
            return True
    names = " ".join(str(s) for s in df["source_name"].dropna().unique()).lower()
    return any(m in names for m in marks)


def _latest_files() -> dict[str, Path]:
    latest: dict[str, Path] = {}
    for f in sorted(ROOT.glob("data/raw/**/*.parquet")):
        fam = re.sub(r"_\d{8}$", "", f.stem)
        if fam not in latest or f.stat().st_mtime > latest[fam].stat().st_mtime:
            latest[fam] = f
    return latest


def _fresh_dir(p: Path) -> Path:
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    return p


def _scope() -> tuple[str, float]:
    full = os.environ.get("CODEX_FULL") == "1" or date.today().weekday() == CFG["scope"]["full_sweep_weekday"]
    return ("weekly_full" if full else "daily"), CFG["scope"]["changed_within_hours"]


def prepare_data() -> dict:
    scope, hours = _scope()
    cutoff = datetime.now() - timedelta(hours=hours)
    pub_in = _fresh_dir(WORK / "inputs" / "public")
    pub_stage = _fresh_dir(WORK / "staging" / "public")
    _fresh_dir(WORK / "out" / "data")
    summary = _data_summary()
    files, restricted = [], []
    for fam, f in sorted(_latest_files().items()):
        rel = f.relative_to(ROOT / "data" / "raw")
        if _restricted(f):
            restricted.append(fam)
            if fam in summary:
                summary[fam]["restricted"] = True
            continue
        for base in (pub_in, pub_stage):
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, base / rel)
        files.append({"family": fam, "file": str(rel).replace("\\", "/"),
                      "changed_today": datetime.fromtimestamp(f.stat().st_mtime) >= cutoff})
        if fam in summary:
            summary[fam]["restricted"] = False
    (WORK / "inputs" / "data_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
    manifest = {"stage": "data", "date": str(date.today()), "scope": scope, "public_files": files,
                "restricted_families_stats_only": restricted}
    (WORK / "inputs" / "manifest_data.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                                          encoding="utf-8")
    focus = sum(1 for x in files if x["changed_today"]) if scope == "daily" else len(files)
    print(f"[완료] Codex 입력 준비(데이터·{scope}) — 공개 사본 {len(files)}개(점검 대상 {focus}) · "
          f"요약 통계만 {len(restricted)}개: {', '.join(restricted)}")
    return manifest


def prepare_semantic() -> dict:
    dst = _fresh_dir(WORK / "inputs" / "semantic")
    _fresh_dir(WORK / "out" / "semantic")
    files = []
    for pat in SEMANTIC_INPUTS:
        hits = sorted(glob.glob(str(ROOT / pat), recursive=True), key=os.path.getmtime)
        for f in hits[-40:] if "Summary" in pat else hits[-5:] if "digest" in pat else hits:
            fp = Path(f)
            if _restricted(fp) if fp.suffix == ".parquet" else any(
                    m.lower() in str(fp).lower() for m in CFG["restricted"]):
                continue
            rel = fp.relative_to(ROOT)
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fp, dst / rel)
            files.append(str(rel).replace("\\", "/"))
    manifest = {"stage": "semantic", "date": str(date.today()), "files": files,
                "ontology_read_only": ["/repo/src/semantic/entities.yaml", "/repo/src/semantic/ontology.yaml",
                                       "/repo/src/semantic/causal_chains.md"]}
    (WORK / "inputs" / "manifest_semantic.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                                              encoding="utf-8")
    print(f"[완료] Codex 입력 준비(시맨틱) — 비정형·온톨로지 입력 {len(files)}건")
    return manifest


def prepare_investigate(runs: int = 3) -> dict:
    """근본 원인 조사 입력 — 최근 실행 로그의 경고·오류, 오늘 Codex 보고서·제안, 공개 데이터 사본(데이터 준비 재사용)."""
    prepare_data()
    dst = _fresh_dir(WORK / "inputs" / "investigate")
    _fresh_dir(WORK / "out" / "investigate")
    logs = ROOT / "docker" / "logs"
    days = sorted({f.name.rsplit("_", 2)[-2] for f in logs.glob("collect_free_*.json")})[-runs:]
    seen, lines = set(), []
    for f in sorted(logs.glob("*.json")):
        parts = f.stem.rsplit("_", 2)
        if len(parts) < 3 or parts[-2] not in days:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for s in d.get("steps", []):
            for ln in s.get("tail", "").splitlines():
                key = (parts[0], ln[:100])
                if ln.startswith(("[경고]", "[오류]", "FAILED", "Traceback")) and key not in seen:
                    seen.add(key)
                    lines.append(f"{parts[-2]} {parts[0]} | {s.get('step', '')[:60]} | {ln[:300]}")
    (dst / "run_warnings.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    q = os.environ.get("CODEX_QUESTIONS_FILE", "")
    if q and Path(q).is_file():   # 승인자·작업자가 정한 질문 목록 — 있으면 기본 조사 목록 대신 이 질문에 답함
        shutil.copy2(q, dst / "questions.md")
    for name in (f"codex_verify_data_{date.today():%Y-%m-%d}.md", f"codex_proposals_{date.today():%Y-%m-%d}.json"):
        src = ROOT / "reports" / "ops" / name
        if src.is_file():
            shutil.copy2(src, dst / name)
    print(f"[완료] Codex 입력 준비(근본 원인 조사) — 최근 {len(days)}회 실행 경고·오류 {len(lines)}줄")
    return {"days": days, "lines": len(lines)}


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    for d in ("inputs", "staging", "out", "queue", "logs"):
        (WORK / d).mkdir(parents=True, exist_ok=True)
    if stage == "data":
        prepare_data()
    elif stage == "semantic":
        prepare_semantic()
    elif stage == "investigate":
        prepare_investigate()
    else:
        raise SystemExit("[오류] 사용법: codex_prepare.py data|semantic|investigate")
