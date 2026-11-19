"""파이프라인 실행 보고서 — 통합 워크플로우의 최종 산출물(한 화면).

runner가 작업마다 남기는 결과 JSON(docker/logs/<job>_<시각>.json)을 단계별로 모아
성패·소요 시간·산출물 링크·Codex 교차검증 결과를 reports/ops/pipeline_run_latest.html에 쓴다.
24시간보다 오래된 결과는 '이번 실행 아님'으로 표시한다(과거 성공을 현재 성공으로 위장하지 않음).
"""
from __future__ import annotations

import glob
import html
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "docker" / "logs"
OUT = ROOT / "reports" / "ops" / "pipeline_run_latest.html"
FRESH = timedelta(hours=24)
STAGES = [
    ("01 수집", "데이터 수집(무료 커넥터·시세·웹 수집·비정형)",
     ["collect_free", "collect_quick", "te_update", "codex_crawl", "digest", "codex_verify_collect"]),
    ("02 정제", "정제·시점 정합(as-of)·마트 게이트·문서 보기",
     ["manual_parsers", "mart", "vault_export", "codex_verify_process"]),
    ("03 분석·평가", "모델 비교·검증·화면 생성·테스트",
     ["band_compare", "baseline", "g1_report", "g2_preview", "tests", "codex_verify_analyze"]),
]
LABELS = {
    "collect_free": "무료 커넥터 수집", "collect_quick": "빠른 수집(해상 경로·경보)", "te_update": "TE 시세 갱신",
    "codex_crawl": "Codex 웹 수집", "digest": "비정형 다이제스트", "codex_verify_collect": "Codex 교차검증 — 수집",
    "manual_parsers": "수동 업로드 파서", "mart": "마트·시점 정합 게이트", "vault_export": "Obsidian 볼트 보기",
    "codex_verify_process": "Codex 교차검증 — 정제", "band_compare": "참고 범위 방식 5종 비교",
    "baseline": "기준선 성적표", "g1_report": "G1 변수 중요도·브리프", "g2_preview": "G2 화면(해상 경로·범위)",
    "tests": "자동 테스트", "codex_verify_analyze": "Codex 교차검증 — 분석",
}


def latest(job: str) -> dict | None:
    files = sorted(glob.glob(str(LOGS / f"{job}_*.json")))
    if not files:
        return None
    d = json.loads(Path(files[-1]).read_text(encoding="utf-8"))
    d["_mtime"] = datetime.fromtimestamp(Path(files[-1]).stat().st_mtime)
    return d


def newest(pattern: str) -> Path | None:
    files = sorted(glob.glob(str(ROOT / pattern)), key=os.path.getmtime)
    return Path(files[-1]) if files else None


def rel(p: Path) -> str:
    return os.path.relpath(p, OUT.parent).replace("\\", "/")


def job_row(job: str, now: datetime) -> tuple[str, str]:
    d = latest(job)
    if d is None:
        return "skip", f"<tr class='skip'><td>{LABELS[job]}</td><td>실행 기록 없음</td><td></td><td></td></tr>"
    secs = sum(s.get("seconds", 0) for s in d.get("steps", []))
    when = d["_mtime"].strftime("%m-%d %H:%M")
    if now - d["_mtime"] > FRESH:
        state, label = "stale", "이번 실행 아님"
    elif d.get("failed"):
        state, label = "fail", "실패 " + ", ".join(html.escape(f) for f in d["failed"])
    else:
        state, label = "ok", "성공"
    tail = html.escape((d.get("steps") or [{}])[-1].get("tail", "")[-400:])
    return state, (f"<tr class='{state}'><td>{LABELS[job]}</td><td>{label}</td><td>{secs:,.0f}초</td>"
                   f"<td>{when}<details><summary>로그</summary><pre>{tail}</pre></details></td></tr>")


def outputs() -> list[tuple[str, Path | None]]:
    return [
        ("G2 미리보기(참고 범위·해상 경로)", newest("reports/g2_preview/g2_preview_latest.html")),
        ("G1 일일 브리프", newest("reports/pipeline/g1_daily_brief_*.html")),
        ("참고 범위 방식 비교(JSON)", newest("reports/g2_preview/band_method_compare.json")),
        ("기준선 성적표", newest("reports/market/g2_band_backtest_*.md")),
        ("마트 보고", newest("reports/market/feature_mart_*.md")),
        ("Codex 교차검증 — 수집", newest("reports/ops/codex_verify_collect_*.md")),
        ("Codex 교차검증 — 정제", newest("reports/ops/codex_verify_process_*.md")),
        ("Codex 교차검증 — 분석", newest("reports/ops/codex_verify_analyze_*.md")),
    ]


def main() -> None:
    now = datetime.now()
    sections, counts = [], {"ok": 0, "fail": 0, "stale": 0, "skip": 0}
    for title, desc, jobs in STAGES:
        rows = []
        for j in jobs:
            state, row = job_row(j, now)
            counts[state] += 1
            rows.append(row)
        sections.append(f"<section><h2>{title}</h2><p class='desc'>{desc}</p><table><thead><tr><th>단계</th>"
                        f"<th>결과</th><th>소요</th><th>시각</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>")
    links = "".join(f"<li><a href='{rel(p)}'>{name}</a> <span>{datetime.fromtimestamp(p.stat().st_mtime):%m-%d %H:%M}</span></li>"
                    if p else f"<li class='skip'>{name} — 아직 없음</li>" for name, p in outputs())
    vault = ROOT / "data" / "vault_view" / "Nexus"
    n_notes = len(list(vault.rglob("*.md"))) if vault.exists() else 0
    verdict = "정상" if counts["fail"] == 0 else f"실패 {counts['fail']}건"
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nexus 파이프라인 실행 보고</title><style>
:root{{--bg:#fafaf7;--fg:#1f2328;--muted:#6b6f76;--line:#e3e1da;--ok:#1a7f37;--fail:#c62828;--stale:#9a6700;--accent:#b7791f}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 "IBM Plex Sans KR","Noto Sans KR",system-ui,sans-serif}}
main{{max-width:960px;margin:0 auto;padding:24px 16px}} h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:17px;margin:24px 0 2px}}
.desc,.meta,span{{color:var(--muted);font-size:13px}} table{{width:100%;border-collapse:collapse;margin-top:6px}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
tr.ok td:nth-child(2){{color:var(--ok)}} tr.fail td:nth-child(2){{color:var(--fail);font-weight:600}}
tr.stale td,tr.skip td,li.skip{{color:var(--muted)}} pre{{white-space:pre-wrap;font-size:12px;max-height:200px;overflow:auto}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}} .kpi div{{border:1px solid var(--line);border-radius:8px;padding:10px 14px;background:#fff}}
.kpi b{{display:block;font-size:20px}} a{{color:var(--accent)}} ul{{padding-left:18px}}
</style></head><body><main>
<h1>Nexus 파이프라인 실행 보고</h1><p class="meta">생성 {now:%Y-%m-%d %H:%M} · 수집 → 정제 → 분석·평가 · 단계마다 Codex 읽기 전용 교차검증</p>
<div class="kpi"><div><b>{verdict}</b>전체 판정</div><div><b>{counts['ok']}</b>성공 단계</div>
<div><b>{counts['fail']}</b>실패 단계</div><div><b>{counts['stale'] + counts['skip']}</b>이번 실행 아님·기록 없음</div><div><b>{n_notes}</b>볼트 노트</div></div>
{''.join(sections)}<h2>산출물</h2><ul>{links}</ul>
<p class="meta">과거 관측 요약·방법 검증 결과이며 가격 전망이나 구매 권고가 아님. 구매·보류 판단은 담당자 승인 절차를 따름.</p>
</main></body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"[완료] 실행 보고 → {OUT.relative_to(ROOT)} · 판정 {verdict} · 성공 {counts['ok']} · 실패 {counts['fail']}")


if __name__ == "__main__":
    main()
