"""n8n 워크플로우 JSON 생성기 — 파이프라인 전체를 runner 작업(POST http://runner:8000/run/<job>)의 사슬로 정의한다.

산출: docker/n8n/nexus_*.json (자격 증명 없음 — runner는 내부 네트워크 HTTP라 인증 노드가 필요 없음).
가져오기(키 불필요): docker compose -f docker/compose.yml exec n8n n8n import:workflow --separate --input=/workflows
워크플로우는 가져온 뒤 꺼진 상태 — n8n 화면에서 켠다(한 번만).
각 작업 노드는 오류를 던지지 않고 응답을 그대로 넘기며, 마지막 '결과 점검' 노드가 실패 단계를 모아
runner /alert로 알린다. 워크플로우 자체가 멈추면(타임아웃 등) 오류 워크플로우가 같은 곳으로 알린다.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docker" / "n8n"
RUNNER = "http://runner:8000"
ERROR_WF_ID = "nexusErrorAlert01"
TWO_HOURS_MS = 7_200_000


def trigger_nodes(cron: str | None, label: str) -> list[dict]:
    nodes = [{"parameters": {}, "id": "manual", "name": "수동 실행", "type": "n8n-nodes-base.manualTrigger",
              "typeVersion": 1, "position": [0, 200]}]
    if cron:
        nodes.append({"parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": cron}]}},
                      "id": "schedule", "name": label, "type": "n8n-nodes-base.scheduleTrigger",
                      "typeVersion": 1.2, "position": [0, 0]})
    return nodes


def job_node(i: int, job: str, title: str, disabled: bool = False) -> dict:
    node = {"parameters": {"method": "POST", "url": f"{RUNNER}/run/{job}",
                           "options": {"timeout": TWO_HOURS_MS,
                                       "response": {"response": {"neverError": True, "fullResponse": True}}}},
            "id": job, "name": title, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
            "position": [240 * (i + 1), 100]}
    if disabled:
        node["disabled"] = True
    return node


def check_nodes(n: int, titles: list[str]) -> list[dict]:
    steps = json.dumps(titles, ensure_ascii=False)
    check = f"""const steps = {steps};
const fails = [];
for (const s of steps) {{
  let r;
  try {{ r = $(s).first().json; }} catch (e) {{ continue; }}   // 비활성 노드는 건너뜀
  const body = r.body || r;
  const code = r.statusCode ?? 200;
  if (code >= 400 || (Array.isArray(body.failed) && body.failed.length)) {{
    fails.push({{ step: s, status: code, failed: body.failed || body.error || null, log: body.log || null }});
  }}
}}
return [{{ json: {{ workflow: $workflow.name, ok: fails.length === 0, fails, at: new Date().toISOString() }} }}];"""
    only_fail = "return $json.ok ? [] : [{ json: $json }];"
    x = 240 * (n + 1)
    return [
        {"parameters": {"jsCode": check}, "id": "check", "name": "결과 점검", "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [x, 100]},
        {"parameters": {"jsCode": only_fail}, "id": "only_fail", "name": "실패만 통과", "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [x + 240, 100]},
        {"parameters": {"method": "POST", "url": f"{RUNNER}/alert", "sendBody": True, "specifyBody": "json",
                        "jsonBody": "={{ JSON.stringify($json) }}", "options": {}},
         "id": "alert", "name": "실패 알림 기록", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
         "position": [x + 480, 100]},
    ]


def chain(wf_id: str, name: str, cron: str | None, cron_label: str, jobs: list[tuple]) -> dict:
    nodes = trigger_nodes(cron, cron_label)
    titles = []
    for i, (job, title, *rest) in enumerate(jobs):
        nodes.append(job_node(i, job, title, disabled=bool(rest and rest[0])))
        titles.append(title)
    nodes += check_nodes(len(jobs), titles)
    order = titles + ["결과 점검", "실패만 통과", "실패 알림 기록"]
    conn = {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}
    for t in [n["name"] for n in nodes if n["type"].endswith("Trigger")]:
        conn[t] = {"main": [[{"node": titles[0], "type": "main", "index": 0}]]}
    return {"id": wf_id, "name": name, "nodes": nodes, "connections": conn, "active": False,
            "settings": {"timezone": "Asia/Seoul", "executionOrder": "v1", "errorWorkflow": ERROR_WF_ID}}


def error_workflow() -> dict:
    body = "={{ JSON.stringify({ workflow: $json.workflow.name, failed_node: $json.execution.lastNodeExecuted, " \
           "error: $json.execution.error.message, at: new Date().toISOString() }) }}"
    return {"id": ERROR_WF_ID, "name": "Nexus 실패 알림", "active": False,
            "settings": {"timezone": "Asia/Seoul", "executionOrder": "v1"},
            "nodes": [{"parameters": {}, "id": "err", "name": "워크플로우 오류", "type": "n8n-nodes-base.errorTrigger",
                       "typeVersion": 1, "position": [0, 0]},
                      {"parameters": {"method": "POST", "url": f"{RUNNER}/alert", "sendBody": True,
                                      "specifyBody": "json", "jsonBody": body, "options": {}},
                       "id": "alert", "name": "실패 알림 기록", "type": "n8n-nodes-base.httpRequest",
                       "typeVersion": 4.2, "position": [240, 0]}],
            "connections": {"워크플로우 오류": {"main": [[{"node": "실패 알림 기록", "type": "main", "index": 0}]]}}}


WORKFLOWS = {
    # 화~토 06:00 KST = 미국 장 마감(전일) 이후. 수집 → 크롤러 → 다이제스트 → 마트·게이트 → 성적표 → 화면 → 테스트 → 교차검증
    "nexus_daily.json": chain("nexusDaily01", "Nexus 일일 파이프라인", "0 6 * * 2-6", "화~토 06:00", [
        ("collect_free", "무료 커넥터 수집"), ("te_update", "TE 시세 갱신"), ("codex_crawl", "Codex 비정형 크롤러"),
        ("digest", "일별 비정형 다이제스트"), ("mart", "마트·게이트"), ("baseline", "기준선 성적표"),
        ("g2_preview", "해상 경로·G2 화면"), ("tests", "테스트"), ("codex_verify", "Codex 교차검증")]),
    # 일요일 07:00 — 공백 복구·수동 업로드 재파싱·마트 재생성
    "nexus_weekly.json": chain("nexusWeekly01", "Nexus 주간 정비", "0 7 * * 0", "일 07:00", [
        ("te_repair", "TE 시세 공백 복구"), ("manual_parsers", "수동 업로드 파서"), ("mart", "마트·게이트"),
        ("baseline", "기준선 성적표"), ("g2_preview", "해상 경로·G2 화면"),
        ("vault_export", "Obsidian 볼트 보기 내보내기")]),
    # 유료 — 수동 실행만(스케줄 없음). 실행 전 비용 확인
    "nexus_databento_manual.json": chain("nexusDatabento01", "Databento 유료 수집(수동)", None, "", [
        ("databento", "Databento 수집(유료)"), ("mart", "마트·게이트")]),
    "nexus_error_alert.json": error_workflow(),
}


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, wf in WORKFLOWS.items():
        (OUT / name).write_text(json.dumps(wf, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[완료] {name} — 노드 {len(wf['nodes'])}개")


if __name__ == "__main__":
    run()
