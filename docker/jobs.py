"""n8n → 파이프라인 작업 실행 엔드포인트 (D-053).

POST /run/<job> 로 정해진 작업만 실행한다(임의 명령 불가). 한 번에 하나만 실행.
subprocess는 파이프라인 단계 오케스트레이션 용도이며 데이터 접근은 각 스크립트의 SDK가 담당한다.
"""
import hmac
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PY = sys.executable
# 2026-11-19: Actions 정지(09-29~)로 Actions 전용이던 geointel·shipping 수집을 로컬로 이관 +
#   portwatch(IMF 해협 통과 척수 — AISstream 해협 집계 대체) 신규. Perplexity 키 부재 시 각 커넥터가 건너뜀.
CONNECTORS = ["economic", "climate", "gpr", "wasde", "production", "commodity", "customs", "cot",
              "geointel", "shipping", "portwatch", "maritime_alerts"]
MANUAL_PARSERS = ["ingest_te_xlsx", "ingest_wasde_xlsx", "ingest_psd_data", "ingest_gats_data",
                  "ingest_ice_volumes", "ingest_nasa_power_xlsx", "ingest_customs_gw_uploads",
                  "ingest_fx_brl_usd_xlsx", "ingest_enso_oni_xlsx"]

# 작업명 → (단계 목록, 실패 시 중단 여부). 수집은 비치명, 마트·게이트는 fail-closed(A-108).
JOBS: dict[str, tuple[list[list[str]], bool]] = {
    "databento": ([[PY, "scripts/ingest_databento_bo.py"]], True),
    "collect_free": ([[PY, f"src/pipeline/connectors/{c}_connector.py"] for c in CONNECTORS], False),
    "manual_parsers": ([[PY, f"scripts/{s}.py"] for s in MANUAL_PARSERS]
                       + [[PY, "-m", "src.features.structural_indicators"]], False),
    # 목표변수(CBOT_BO_CLOSE) 발행이 선행돼야 준비도 게이트가 열림 — Actions 전용이던 단계를 로컬에도
    #   배치(2026-11-17). 무료 경로: 커밋된 Databento CSV + yfinance 정산가 교차검증(유료 API 미호출).
    "mart": ([[PY, "scripts/validate_session_close.py"],
              [PY, "scripts/data_readiness.py"],
              [PY, "-m", "src.features.build_feature_mart", "--self-test"],
              [PY, "-m", "src.features.build_feature_mart"],
              [PY, "scripts/validate_asof.py"]], True),
    # 단일 파이프라인(SPEC §3.1): ②정제의 마트 생성 / ③품질 점검을 분리한 작업 — 기존 'mart'는 시연·주간 정비용으로 유지
    "mart_build": ([[PY, "scripts/validate_session_close.py"],
                    [PY, "-m", "src.features.build_feature_mart", "--self-test"],
                    [PY, "-m", "src.features.build_feature_mart"]], True),
    "quality": ([[PY, "scripts/data_readiness.py"],
                 [PY, "scripts/validate_asof.py"],
                 [PY, "scripts/validate_semantic_layer.py", "--strict"],
                 [PY, "-m", "pytest", "-q", "tests"]], False),
    # Codex 검증(SPEC §3.8): runner가 입력 준비(공개 사본·제한 원천은 통계만) → 격리 검증 컨테이너 호출 → 제안 게이트.
    #   검증 컨테이너가 없으면(노트북) 호출 단계가 '미실행'으로 건너뜀
    "codex_verify_data": ([[PY, "scripts/codex_prepare.py", "data"], [PY, "scripts/codex_remote.py", "data"],
                           [PY, "scripts/codex_gate.py"]], False),
    "codex_verify_semantic": ([[PY, "scripts/codex_prepare.py", "semantic"],
                               [PY, "scripts/codex_remote.py", "semantic"]], False),
    # 근본 원인 조사(승인자 지시 2026-11-26): 최근 실행 경고·오류 + 오늘 검토 결과 → Codex가 원인·근거·수정 diff 제안(적용은 작업자)
    "codex_investigate": ([[PY, "scripts/codex_prepare.py", "investigate"],
                           [PY, "scripts/codex_remote.py", "investigate"]], False),
    # 메일 본문 생성(실행 요약·주간 요약) — n8n이 응답의 마지막 줄 JSON을 메일로 보냄
    "pipeline_summary": ([[PY, "scripts/pipeline_summary.py", "daily"]], False),
    # 보고서 Google Drive 저장(승인자 승인 2026-11-26) — 날짜별 폴더, 링크는 메일에. rclone 미설정이면 건너뜀(비치명)
    "drive_upload": ([[PY, "scripts/drive_upload.py"]], False),
    "weekly_summary": ([[PY, "scripts/pipeline_summary.py", "weekly"]], False),
    # TE 시세 xlsx 증분 갱신(TRADING_ECONOMICS_API_KEY) → 정형화 — Actions te_xlsx_update.yml 대체
    "te_update": ([[PY, "scripts/update_te_xlsx_from_api.py", "--mode", "snapshot"],
                   [PY, "scripts/ingest_te_xlsx.py"]], False),
    # 일별 비정형 다이제스트(RSS·GDELT·신호 아카이브) — Actions external_data_refresh 다이제스트 잡 대체
    "digest": ([[PY, "scripts/daily_unstructured_digest.py"]], False),
    # TE 시세 공백 복구(수집 중단 기간을 historical 창으로 재조회 — 일별 스냅샷이 공백을 가리는 문제 대응)
    "te_repair": ([[PY, "scripts/update_te_xlsx_from_api.py", "--mode", "historical", "--repair-gap"],
                   [PY, "scripts/ingest_te_xlsx.py"]], False),
    # G2 Preview 화면: 해상 경로 시나리오 → 화면 생성(portwatch 수집·마트 이후)
    "g2_preview": ([[PY, "-m", "src.logistics.route_scenarios"],
                    [PY, "-m", "src.reporting.g2_preview"]], False),
    # Codex 연동(승인자 도구) — 비정형 크롤러 실행·산출 계약 검증 / 당일 산출물 교차검증. 미설정이면 건너뜀(비치명)
    "codex_crawl": ([[PY, "scripts/codex_bridge.py", "crawl"]], False),
    "codex_verify": ([[PY, "scripts/codex_bridge.py", "verify"]], False),
    # 시맨틱 레이어 → Obsidian 볼트 보기(data/vault_view/Nexus). 검증 실패 시 내보내지 않음(정본은 YAML)
    "vault_export": ([[PY, "scripts/validate_semantic_layer.py", "--strict"],
                      [PY, "scripts/export_obsidian_vault.py"]], True),
    "baseline": ([[PY, "-m", "src.evaluation.band_backtest"]], True),
    # 분석·평가: 참고 범위 산출 방식 5종 walk-forward 비교(모델 비교·검증)
    "band_compare": ([[PY, "scripts/g2_band_method_compare.py"]], True),
    # G1 변수 중요도·일별 브리프(약 6분) — 마트 이후. reports/pipeline/g1_daily_brief_*.html
    "g1_report": ([[PY, "src/forecasting/variable_importance_g1.py"]], False),
    # 시연용 빠른 수집 — 해상 경로(PortWatch)·해상 경보 RSS만. 실패해도 저장된 데이터로 이후 단계 진행(비치명)
    "collect_quick": ([[PY, f"src/pipeline/connectors/{c}_connector.py"] for c in ("portwatch", "maritime_alerts")], False),
    # 단계별 Codex 교차검증(읽기 전용) — 산출물+생성 코드+점검표. codex 미설치·산출물 없음이면 건너뜀(비치명)
    "codex_verify_collect": ([[PY, "scripts/codex_bridge.py", "verify", "collect"]], False),
    "codex_verify_process": ([[PY, "scripts/codex_bridge.py", "verify", "process"]], False),
    "codex_verify_analyze": ([[PY, "scripts/codex_bridge.py", "verify", "analyze"]], False),
    # 최종 산출물: 단계별 성패·소요·산출물 링크를 한 화면으로(reports/ops/pipeline_run_latest.html)
    "run_report": ([[PY, "scripts/pipeline_run_report.py"],
                    [PY, "-m", "scripts.build_terminal"]], False),   # + 대화형 터미널(reports/terminal/nexus_terminal.html)
    "tests": ([[PY, "-m", "pytest", "-q", "tests"]], True),
}
# 검증 컨테이너 역할(SPEC §3.8): Codex 검증 2개 작업만 노출하고, 자기 API 토큰을 하위 프로세스에 넘기지 않는다
ROLE = os.environ.get("NEXUS_ROLE", "runner")
if ROLE == "verifier":
    JOBS = {"codex_verify_data": ([[PY, "scripts/codex_verifier.py", "data"]], False),
            "codex_verify_semantic": ([[PY, "scripts/codex_verifier.py", "semantic"]], False),
            "codex_verify_investigate": ([[PY, "scripts/codex_verifier.py", "investigate"]], False)}
REPO = os.environ.get("NEXUS_REPO", "/repo")
RUNNER_TOKEN = os.environ.get("VERIFIER_TOKEN" if ROLE == "verifier" else "RUNNER_TOKEN", "")
LOG_DIR = Path(os.environ.get("JOB_LOG_DIR", str(Path(REPO) / "docker" / "logs")))
CHILD_ENV = {k: v for k, v in os.environ.items() if not (ROLE == "verifier" and k.endswith("_TOKEN"))}
TAIL_CHARS = 4000
ALERT_MAX_BYTES = 16384
_lock = threading.Lock()


def run_job(name: str) -> tuple[int, dict]:
    steps, stop_on_fail = JOBS[name]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{name}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    results = []
    with log_path.open("w", encoding="utf-8") as log:
        for argv in steps:
            t0 = time.time()
            proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, env=CHILD_ENV)
            log.write(f"$ {' '.join(argv)}\n{proc.stdout}{proc.stderr}\n")
            results.append({"step": " ".join(argv[1:]), "returncode": proc.returncode,
                            "seconds": round(time.time() - t0, 1),
                            "tail": (proc.stdout + proc.stderr)[-TAIL_CHARS:]})
            if proc.returncode != 0 and stop_on_fail:
                break
    failed = [r["step"] for r in results if r["returncode"] != 0]
    status = 500 if failed and stop_on_fail else 200
    body = {"job": name, "failed": failed, "log": str(log_path), "steps": results,
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    # 실행 결과를 로그 옆 JSON으로 남김 — 실행 보고서(run_report)가 단계별 성패·소요 시간을 읽음
    log_path.with_suffix(".json").write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return status, body


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        self._send(200, {"status": "ok", "jobs": sorted(JOBS)})

    def do_POST(self) -> None:
        # 작업 API 인증(SPEC §3.4): RUNNER_TOKEN이 설정돼 있으면 같은 토큰을 가진 요청만 실행 — 같은 네트워크의 다른 컨테이너 차단
        if RUNNER_TOKEN and not hmac.compare_digest(self.headers.get("X-Runner-Token", ""), RUNNER_TOKEN):
            return self._send(401, {"error": "[오류] 인증 토큰 없음 또는 불일치"})
        if self.path == "/alert":            # n8n 실패 알림 수신 — 크기 제한 후 로그에 한 줄씩 기록
            n = min(int(self.headers.get("Content-Length") or 0), ALERT_MAX_BYTES)
            raw = self.rfile.read(n).decode("utf-8", "replace")
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            with (LOG_DIR / "alerts.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "body": raw}, ensure_ascii=False) + "\n")
            print(f"[경고] 파이프라인 실패 알림 수신 — {raw[:300]}", flush=True)
            return self._send(200, {"status": "recorded"})
        name = self.path.removeprefix("/run/")
        if name not in JOBS:
            return self._send(404, {"error": f"[오류] 알 수 없는 작업: {name}"})
        if not _lock.acquire(blocking=False):
            return self._send(409, {"error": "[경고] 다른 작업이 실행 중입니다."})
        try:
            self._send(*run_job(name))
        finally:
            _lock.release()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
