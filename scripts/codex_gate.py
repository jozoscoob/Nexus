"""Codex 제안 게이트(runner 측, SPEC §3.8) — 실제 데이터는 바꾸지 않는다.

    python scripts/codex_gate.py

데이터 제안(codex_work/out/data/proposals.json)마다 스테이징 수정본과 실제 파일(data/raw)을 비교:
  ① 열·자료형 동일  ② as-of 필드 존재 · available_at<event_time 0 · 미래 available_at 0
  ③ 행 수 변화 ≤ 기준  ④ 수치 열 규모(최소·최대)가 원본 대비 기준 배수 이내  ⑤ 변경 행 수(전후 비교)
통과한 수정본은 codex_work/queue/<제안ID>/로 보관(스테이징은 다음 실행에 지워지므로) → 승인자 승인 후
scripts/codex_apply.py <제안ID>로만 실제 데이터에 반영. 시맨틱 제안은 목록만 등록(적용은 YAML 편집 — 승인 후 작업자).
결과: reports/ops/codex_proposals_<날짜>.json·.md, codex_work/queue/pending.json
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("CODEX_WORK_HOST", str(ROOT / "codex_work")))
CFG = yaml.safe_load((ROOT / "config" / "codex_data_access.yaml").read_text(encoding="utf-8"))["gate"]
OPS = ROOT / "reports" / "ops"


def _check(real_p: Path, new_p: Path) -> tuple[list[str], dict]:
    fails, info = [], {}
    real, new = pd.read_parquet(real_p), pd.read_parquet(new_p)
    if list(real.columns) != list(new.columns) or [str(t) for t in real.dtypes] != [str(t) for t in new.dtypes]:
        fails.append("열·자료형 불일치")
    for c in ("event_time", "release_time", "available_at", "source_vintage"):
        if c in real.columns and c not in new.columns:
            fails.append(f"as-of 필드 삭제: {c}")
    if {"available_at", "event_time"} <= set(new.columns):
        av = pd.to_datetime(new["available_at"], errors="coerce", utc=True)
        ev = pd.to_datetime(new["event_time"], errors="coerce", utc=True)
        if int((av < ev).sum()):
            fails.append(f"available_at<event_time {int((av < ev).sum())}행")
        if int((av > pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=1)).sum()):
            fails.append("미래 available_at")
    ratio = abs(len(new) - len(real)) / max(len(real), 1)
    info.update(rows_before=len(real), rows_after=len(new))
    if ratio > CFG["max_row_change_ratio"]:
        fails.append(f"행 수 변화 {ratio:.1%} > {CFG['max_row_change_ratio']:.0%}")
    for c in real.select_dtypes("number").columns.intersection(new.columns):
        a, b = real[c].abs().max(), pd.to_numeric(new[c], errors="coerce").abs().max()
        if pd.notna(a) and pd.notna(b) and a > 0 and b > 0 and max(a / b, b / a) > CFG["max_value_scale_ratio"]:
            fails.append(f"수치 규모 급변: {c} ({a:.4g}→{b:.4g})")
    if not fails and list(real.columns) == list(new.columns) and len(real) == len(new):
        info["rows_changed"] = int((real.reset_index(drop=True).astype(str)
                                    != new.reset_index(drop=True).astype(str)).any(axis=1).sum())
    return fails, info


def main() -> int:
    today = f"{date.today():%Y-%m-%d}"
    queue = WORK / "queue"
    queue.mkdir(parents=True, exist_ok=True)
    pending_p = queue / "pending.json"
    pending = json.loads(pending_p.read_text(encoding="utf-8")) if pending_p.is_file() else []
    results = []
    prop_p = WORK / "out" / "data" / "proposals.json"
    props = []
    if prop_p.is_file():
        try:
            props = json.loads(prop_p.read_text(encoding="utf-8")) or []
        except json.JSONDecodeError as e:
            print(f"[경고] proposals.json 형식 오류: {e}")
    for i, p in enumerate(props, 1):
        pid = f"{today}-D{i}"
        rel = str(p.get("file", "")).lstrip("/").removeprefix("public/")
        real_p, new_p = ROOT / "data" / "raw" / rel, WORK / "staging" / "public" / rel
        item = {"id": pid, "kind": "data", "file": rel, "problem": p.get("problem", ""), "fix": p.get("fix", ""),
                "severity": p.get("severity", "")}
        if not p.get("staging_written") or not new_p.is_file():
            item.update(gate="해당 없음(수정본 없음 — 지적만)")
        elif ".." in rel or not real_p.is_file():
            item.update(gate="불통과", reasons=["실제 파일 없음 또는 경로 이상"])
        else:
            fails, info = _check(real_p, new_p)
            item.update(info, gate="불통과" if fails else "통과", reasons=fails)
            if not fails:
                dst = queue / pid / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(new_p, dst)
                pending.append({**item, "status": "승인 대기"})
        results.append(item)
    sem_p = WORK / "out" / "semantic" / "proposals.yaml"
    if sem_p.is_file():
        try:
            sem = yaml.safe_load(sem_p.read_text(encoding="utf-8")) or {}
            n = sum(len(sem.get(k) or []) for k in ("entity_proposals", "causal_chain_proposals", "mapping_gaps"))
            if n:
                dst = queue / f"{today}-S" / "proposals.yaml"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sem_p, dst)
                item = {"id": f"{today}-S", "kind": "semantic", "count": n, "gate": "검토 대상(YAML 편집은 승인 후)"}
                results.append(item)
                pending = [x for x in pending if x["id"] != item["id"]] + [{**item, "status": "승인 대기"}]
        except yaml.YAMLError as e:
            print(f"[경고] 시맨틱 proposals.yaml 형식 오류: {e}")
    pending_p.write_text(json.dumps(pending, ensure_ascii=False, indent=1), encoding="utf-8")
    OPS.mkdir(parents=True, exist_ok=True)
    (OPS / f"codex_proposals_{today}.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                                        encoding="utf-8")
    lines = [f"# Codex 제안 — {today}", "", "| ID | 종류 | 대상 | 게이트 | 내용 |", "|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['kind']} | {r.get('file', r.get('count', ''))} | {r['gate']} "
              f"{'· ' + '; '.join(r.get('reasons', [])) if r.get('reasons') else ''} | "
              f"{str(r.get('problem', ''))[:120]} |" for r in results]
    lines += ["", "승인하려면 제안 ID를 알려 주세요. 승인된 항목만 백업 후 반영됩니다(scripts/codex_apply.py)."]
    (OPS / f"codex_proposals_{today}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok = sum(1 for r in results if r["gate"] == "통과")
    print(f"[완료] Codex 제안 게이트 — 제안 {len(results)}건 · 데이터 수정본 통과 {ok}건 · 승인 대기 누적 "
          f"{sum(1 for x in pending if x['status'] == '승인 대기')}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
