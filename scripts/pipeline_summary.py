"""실행 요약 메일 본문 생성(SPEC §3.3) — n8n이 마지막 줄의 `__SUMMARY__{json}`을 읽어 Gmail로 보낸다.

daily : 이번 실행(최근 4시간 안에 끝난 작업)의 성패 → 성공이면 3줄 요약, 실패면 실패 단계·원인 한 줄·로그 위치
weekly: 최근 7일 일일 요약 기록(reports/ops/daily_summary_*.json)의 성패·Codex 지적 건수

제목은 항상 `[Nexus]`로 시작 — Gmail 필터가 'Nexus' 라벨로 옮긴다. 메일 발송 실패는 파이프라인 성패와 무관(n8n에서 분리).
"""
from __future__ import annotations

import glob
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "docker" / "logs"
OPS = ROOT / "reports" / "ops"
RUN_WINDOW = timedelta(hours=4)
PIPELINE_JOBS = ["collect_free", "te_update", "digest", "codex_verify_semantic", "manual_parsers", "mart_build", "vault_export",
                 "quality", "codex_verify_data", "band_compare", "baseline", "g1_report", "g2_preview", "run_report"]
LABEL = {"collect_free": "수집", "te_update": "TE 시세", "digest": "비정형 다이제스트", "codex_verify_semantic": "Codex 시맨틱 검토",
         "manual_parsers": "수동 파서", "mart_build": "마트", "vault_export": "볼트 보기", "quality": "품질 점검",
         "codex_verify_data": "Codex 데이터 검증", "band_compare": "범위 방식 비교", "baseline": "기준선",
         "g1_report": "G1 보고서", "g2_preview": "G2 화면", "run_report": "실행 보고"}


def _fresh_results(now: datetime) -> dict[str, dict]:
    out = {}
    for job in PIPELINE_JOBS:
        files = sorted(glob.glob(str(LOGS / f"{job}_*.json")))
        if not files:
            continue
        d = json.loads(Path(files[-1]).read_text(encoding="utf-8"))
        if now - datetime.fromtimestamp(Path(files[-1]).stat().st_mtime) <= RUN_WINDOW:
            out[job] = d
    return out


def _first_error(d: dict) -> str:
    for step in d.get("steps", []):
        if step.get("returncode"):
            lines = [l for l in step.get("tail", "").splitlines() if "[오류]" in l or "Error" in l or "FAILED" in l]
            if lines:
                return lines[-1][:200]
            return (step.get("tail", "").strip().splitlines()[-1:] or [""])[0][:200]
    return ""


def _warnings(res: dict[str, dict], limit: int = 3) -> list[str]:
    """성공 단계 안의 [경고] 줄 — 실패는 아니지만 데이터가 갱신되지 않은 원천을 메일에 노출."""
    out = []
    for d in res.values():
        for step in d.get("steps", []):
            out += [l.strip()[:160] for l in step.get("tail", "").splitlines() if l.startswith("[경고]")]
    uniq = list(dict.fromkeys(out))
    # 선택 API 키 미등록은 매일 반복되는 알려진 상태 — 1줄로 접고, 새로 생긴 경고를 앞에 보인다
    keyless = [w for w in uniq if "미등록" in w or "환경변수가 설정되지" in w]
    other = [w for w in uniq if w not in keyless]
    shown = other[:limit] + ([f"외 {len(other) - limit}건"] if len(other) > limit else [])
    return shown + ([f"선택 API 키 미등록으로 건너뛴 원천 {len(keyless)}건(알려진 상태)"] if keyless else [])


def _codex_counts(stage: str) -> str:
    f = OPS / f"codex_verify_{stage}_{date.today():%Y-%m-%d}.md"
    if not f.exists():
        return "미실행"
    t = f.read_text(encoding="utf-8")
    crit = len(re.findall(r"[|]\s*치명\s*[|]", t))
    high = len(re.findall(r"[|]\s*높음\s*[|]", t))
    return f"치명 {crit} · 높음 {high}"


def daily() -> dict:
    now = datetime.now()
    res = _fresh_results(now)
    failed = {j: d for j, d in res.items() if d.get("failed")}
    secs = sum(s.get("seconds", 0) for d in res.values() for s in d.get("steps", []))
    asof = (ROOT / "reports" / "terminal" / "nexus_terminal.html").exists()
    codex_note = f"Codex 데이터 {_codex_counts('data')} / 시맨틱 제안 {'있음' if (OPS / f'codex_verify_semantic_{date.today():%Y-%m-%d}.md').exists() else '미실행'}"
    if failed:
        subject = f"[Nexus] ❌ 파이프라인 실패 {len(failed)}단계 — {date.today()}"
        lines = [f"실패: {', '.join(LABEL.get(j, j) for j in failed)} (성공 {len(res) - len(failed)}단계)"]
        lines += [f"- {LABEL.get(j, j)}: {_first_error(d) or '원인 미상'} · 로그 {Path(d.get('log', '')).name}" for j, d in failed.items()]
        lines += [codex_note, "이전 정상 산출물은 그대로 유지됩니다. 실행 보고: reports/ops/pipeline_run_latest.html"]
    else:
        subject = f"[Nexus] ✅ 일일 파이프라인 정상 — {date.today()}"
        lines = [f"{len(res)}단계 모두 성공 · 소요 {secs / 60:.0f}분",
                 codex_note,
                 "산출물: 터미널·G2 화면·G1 보고서 갱신" + ("" if asof else " (터미널 없음)")]
    warns = _warnings(res)
    if warns:
        lines += ["주의(실패 아님 — 갱신 건너뜀):"] + [f"- {w}" for w in warns]
    out = {"subject": subject, "body": "\n".join(lines), "failed": bool(failed), "steps": len(res)}
    OPS.mkdir(parents=True, exist_ok=True)
    (OPS / f"daily_summary_{date.today():%Y-%m-%d}.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def weekly() -> dict:
    days = []
    for i in range(7):
        d = date.today() - timedelta(days=i)
        f = OPS / f"daily_summary_{d:%Y-%m-%d}.json"
        days.append((d, json.loads(f.read_text(encoding="utf-8")) if f.exists() else None))
    ran = [x for _, x in days if x]
    ok = sum(1 for x in ran if not x["failed"])
    lines = [f"최근 7일: 실행 {len(ran)}일 · 정상 {ok}일 · 실패 {len(ran) - ok}일 · 기록 없음 {7 - len(ran)}일"]
    lines += [f"- {d} {'✅' if x and not x['failed'] else '❌' if x else '—'} {x['subject'].split('—')[0].replace('[Nexus] ', '').strip() if x else '실행 기록 없음'}"
              for d, x in sorted(days)]
    return {"subject": f"[Nexus] 📊 주간 요약 — {date.today() - timedelta(days=6)} ~ {date.today()}", "body": "\n".join(lines),
            "failed": len(ran) - ok > 0, "steps": len(ran)}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    out = weekly() if mode == "weekly" else daily()
    print(out["body"])
    print("__SUMMARY__" + json.dumps(out, ensure_ascii=False))
