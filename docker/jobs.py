"""n8n → 파이프라인 작업 실행 엔드포인트 (D-053).

POST /run/<job> 로 정해진 작업만 실행한다(임의 명령 불가). 한 번에 하나만 실행.
subprocess는 파이프라인 단계 오케스트레이션 용도이며 데이터 접근은 각 스크립트의 SDK가 담당한다.
"""
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PY = sys.executable
CONNECTORS = ["economic", "climate", "gpr", "wasde", "production", "commodity", "customs"]
MANUAL_PARSERS = ["ingest_te_xlsx", "ingest_wasde_xlsx", "ingest_psd_data", "ingest_gats_data",
                  "ingest_ice_volumes", "ingest_nasa_power_xlsx", "ingest_customs_gw_uploads",
                  "ingest_fx_brl_usd_xlsx", "ingest_enso_oni_xlsx"]

# 작업명 → (단계 목록, 실패 시 중단 여부). 수집은 비치명, 마트·게이트는 fail-closed(A-108).
JOBS: dict[str, tuple[list[list[str]], bool]] = {
    "databento": ([[PY, "scripts/ingest_databento_bo.py"]], True),
    "collect_free": ([[PY, f"src/pipeline/connectors/{c}_connector.py"] for c in CONNECTORS], False),
    "manual_parsers": ([[PY, f"scripts/{s}.py"] for s in MANUAL_PARSERS]
                       + [[PY, "-m", "src.features.structural_indicators"]], False),
    "mart": ([[PY, "scripts/data_readiness.py"],
              [PY, "-m", "src.features.build_feature_mart", "--self-test"],
              [PY, "-m", "src.features.build_feature_mart"],
              [PY, "scripts/validate_asof.py"]], True),
    "baseline": ([[PY, "-m", "src.evaluation.band_backtest"]], True),
    "tests": ([[PY, "-m", "pytest", "-q", "tests"]], True),
}
REPO = os.environ.get("NEXUS_REPO", "/repo")
LOG_DIR = Path(REPO) / "docker" / "logs"
TAIL_CHARS = 4000
_lock = threading.Lock()


def run_job(name: str) -> tuple[int, dict]:
    steps, stop_on_fail = JOBS[name]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{name}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    results = []
    with log_path.open("w", encoding="utf-8") as log:
        for argv in steps:
            t0 = time.time()
            proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
            log.write(f"$ {' '.join(argv)}\n{proc.stdout}{proc.stderr}\n")
            results.append({"step": " ".join(argv[1:]), "returncode": proc.returncode,
                            "seconds": round(time.time() - t0, 1),
                            "tail": (proc.stdout + proc.stderr)[-TAIL_CHARS:]})
            if proc.returncode != 0 and stop_on_fail:
                break
    failed = [r["step"] for r in results if r["returncode"] != 0]
    status = 500 if failed and stop_on_fail else 200
    return status, {"job": name, "failed": failed, "log": str(log_path), "steps": results}


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
