"""n8n 워크플로우 JSON 생성기 — 파이프라인 전체를 runner 작업(POST http://runner:8000/run/<job>)의 사슬로 정의한다.

분류(승인자 지시 2026-11-19): 01 수집 · 02 정제 · 03 분석·평가 · 04 통합(01→02→03을 하위 워크플로우로 호출)
+ 00 시연(빠른 실행) · 주간 정비 · Databento(유료·수동) · 실패 알림. 각 단계 끝에 Codex 읽기 전용 교차검증.
참고한 설계 패턴: n8n 템플릿의 하위 워크플로우(Execute Workflow) 모듈화·오류 워크플로우,
crewAI/Mastra의 역할·단계 분리, Dify/Langflow의 단계별 관찰 가능성, LiteLLM의 호출 단일 창구(여기서는
runner HTTP 단일 창구). 새 플랫폼은 설치하지 않음.

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


def sub_trigger_nodes() -> list[dict]:
    """하위 워크플로우: 통합 워크플로우에서 호출(Execute Workflow Trigger) + 단독 수동 실행."""
    return [{"parameters": {}, "id": "manual", "name": "수동 실행", "type": "n8n-nodes-base.manualTrigger",
             "typeVersion": 1, "position": [0, 200]},
            {"parameters": {"inputSource": "passthrough"}, "id": "called", "name": "통합 워크플로우에서 호출",
             "type": "n8n-nodes-base.executeWorkflowTrigger", "typeVersion": 1.1, "position": [0, 0]}]


def note_node(text: str, width: int = 520) -> dict:
    return {"parameters": {"content": text, "width": width, "height": 220}, "id": "note", "name": "설명",
            "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, -280]}


def call_node(i: int, wf_id: str, title: str) -> dict:
    return {"parameters": {"source": "database", "workflowId": {"__rl": True, "value": wf_id, "mode": "id"},
                           "mode": "once", "options": {"waitForSubWorkflow": True}},
            "id": f"call_{wf_id}", "name": title, "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2,
            "alwaysOutputData": True, "position": [240 * (i + 1), 100]}


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


def chain(wf_id: str, name: str, cron: str | None, cron_label: str, jobs: list[tuple],
          sub: bool = False, note: str = "") -> dict:
    nodes = sub_trigger_nodes() if sub else trigger_nodes(cron, cron_label)
    titles = []
    for i, (job, title, *rest) in enumerate(jobs):
        nodes.append(job_node(i, job, title, disabled=bool(rest and rest[0])))
        titles.append(title)
    nodes += check_nodes(len(jobs), titles)
    order = titles + ["결과 점검", "실패만 통과", "실패 알림 기록"]
    conn = {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}
    for t in [n["name"] for n in nodes if n["type"].endswith("Trigger")]:
        conn[t] = {"main": [[{"node": titles[0], "type": "main", "index": 0}]]}
    if note:
        nodes.append(note_node(note))
    return {"id": wf_id, "name": name, "nodes": nodes, "connections": conn, "active": False,
            "settings": {"timezone": "Asia/Seoul", "executionOrder": "v1", "errorWorkflow": ERROR_WF_ID}}


def integrated(wf_id: str, name: str, cron: str, cron_label: str, stages: list[tuple], note: str) -> dict:
    """하위 워크플로우를 차례로 호출 → 실행 보고(최종 산출물) → 결과 점검. 단계 실패가 있어도 다음 단계는
    저장된 최신 데이터로 진행하고, 실행 보고·알림이 실패를 드러낸다(조용한 성공 금지)."""
    nodes = trigger_nodes(cron, cron_label)
    titles = []
    for i, (sub_id, title) in enumerate(stages):
        nodes.append(call_node(i, sub_id, title))
        titles.append(title)
    report = "실행 보고(최종 산출물)"
    nodes.append(job_node(len(stages), "run_report", report))
    titles.append(report)
    nodes += check_nodes(len(titles), [report])
    order = titles + ["결과 점검", "실패만 통과", "실패 알림 기록"]
    conn = {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}
    for t in [n["name"] for n in nodes if n["type"].endswith("Trigger")]:
        conn[t] = {"main": [[{"node": titles[0], "type": "main", "index": 0}]]}
    nodes.append(note_node(note, 620))
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


COLLECT, PROCESS, ANALYZE = "nexusCollect01", "nexusProcess01", "nexusAnalyze01"
WORKFLOWS = {
    # 01 수집 — 무료 커넥터·시세·웹 수집(Codex 크롤러)·비정형(RSS·뉴스) → Codex 교차검증
    "nexus_01_collect.json": chain(COLLECT, "Nexus 01 수집", None, "", [
        ("collect_free", "무료 커넥터 수집"), ("te_update", "TE 시세 갱신"), ("codex_crawl", "Codex 웹 수집"),
        ("digest", "비정형 다이제스트(RSS·뉴스)"), ("codex_verify_collect", "Codex 교차검증 — 수집")], sub=True,
        note="## 01 수집\n정형(가격·거시·기상·해상)과 비정형(RSS·뉴스·웹)을 모은다.\n"
             "- 커넥터는 실패해도 비치명 — 저장된 최신 데이터로 다음 단계 진행\n"
             "- 모든 행에 as-of 필드(event_time·available_at)\n"
             "- 끝에 Codex가 중복 키·시점 역전·조용한 실패를 점검"),
    # 02 정제 — 수동 업로드 파서 → 시점 정합 마트·게이트(fail-closed) → 문서·온톨로지 볼트 보기 → Codex 교차검증
    "nexus_02_process.json": chain(PROCESS, "Nexus 02 정제", None, "", [
        ("manual_parsers", "수동 업로드 파서"), ("mart", "마트·시점 정합 게이트"),
        ("vault_export", "Obsidian 볼트 보기"), ("codex_verify_process", "Codex 교차검증 — 정제")], sub=True,
        note="## 02 정제\n원천별 형식을 하나의 계약(price_date·indicator_code·value + as-of 5필드)으로 맞춘다.\n"
             "- 마트: available_at ≤ t인 최근값만(ASOF JOIN), 값 충돌은 즉시 실패\n"
             "- 목표변수는 CME 정산가 교차검증 계열만\n"
             "- 문서·온톨로지는 Obsidian 볼트 보기로 내보냄"),
    # 03 분석·평가 — 방식 비교(walk-forward)·기준선 성적표·화면·테스트 → Codex 교차검증
    "nexus_03_analyze.json": chain(ANALYZE, "Nexus 03 분석·평가", None, "", [
        ("band_compare", "참고 범위 방식 5종 비교"), ("baseline", "기준선 성적표"),
        ("g1_report", "G1 변수 중요도·일별 브리프"), ("g2_preview", "G2 화면(해상 경로·범위)"), ("tests", "자동 테스트"),
        ("codex_verify_analyze", "Codex 교차검증 — 분석")], sub=True,
        note="## 03 분석·평가\n여러 방식을 같은 walk-forward 조건에서 비교하고, 기준선을 못 이기면 승격하지 않는다.\n"
             "- 지표: coverage·폭·pinball(분위 손실)\n"
             "- 화면 수치는 원천 표와 대조(Codex)\n"
             "- 확률 약속·구매 권고 문구 금지"),
    # 04 통합 — 화~토 06:00 KST(미국 장 마감 후). 01 → 02 → 03 → 실행 보고. id는 구 일일 파이프라인을 대체
    "nexus_04_integrated.json": integrated(
        "nexusDaily01", "Nexus 04 통합 파이프라인", "0 6 * * 2-6", "화~토 06:00",
        [(COLLECT, "01 수집"), (PROCESS, "02 정제"), (ANALYZE, "03 분석·평가")],
        note="## 04 통합 파이프라인\n01 수집 → 02 정제 → 03 분석·평가를 하위 워크플로우로 차례로 호출하고\n"
             "실행 보고(reports/ops/pipeline_run_latest.html)를 최종 산출물로 남긴다.\n"
             "- 단계 실패는 다음 단계를 막지 않되 보고·알림에 드러남\n"
             "- 전체 약 25~35분"),
    # 00 시연 — 빠른 실행: 해상 경로·경보만 새로 수집하고 나머지는 저장 데이터로
    "nexus_00_demo.json": chain("nexusDemo01", "Nexus 00 시연(빠른 실행)", None, "", [
        ("collect_quick", "빠른 수집(해상 경로·경보)"), ("mart", "마트·시점 정합 게이트"),
        ("band_compare", "참고 범위 방식 5종 비교"), ("g2_preview", "G2 화면(해상 경로·범위)"),
        ("vault_export", "Obsidian 볼트 보기"), ("codex_verify_analyze", "Codex 교차검증 — 분석"),
        ("run_report", "실행 보고(최종 산출물)")],
        note="## 00 시연(빠른 실행)\n통합 파이프라인과 같은 흐름을 짧게 — 수집은 해상 경로·경보만,\n"
             "나머지는 저장된 최신 데이터로 정제 → 분석 → Codex 검증 → 실행 보고까지 끝낸다."),
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
