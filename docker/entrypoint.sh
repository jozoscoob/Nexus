#!/bin/sh
# runner 시작 스크립트 — Codex 로그인 사본을 컨테이너 전용 위치로 복사한 뒤 작업 서버 실행.
# 호스트 auth.json은 읽기 전용 마운트 — 컨테이너가 고쳐 쓰지 않는다(토큰 값은 출력하지 않음).
CODEX_HOME="${CODEX_HOME:-/root/.codex}"
mkdir -p "$CODEX_HOME"
if [ -s /run/secrets/codex_auth.json ]; then
  cp /run/secrets/codex_auth.json "$CODEX_HOME/auth.json" && chmod 600 "$CODEX_HOME/auth.json"
  echo "[정보] Codex 로그인 사본 준비됨"
else
  echo "[정보] Codex 로그인 파일 없음 — Codex 단계는 건너뜀(OPENAI_API_KEY가 있으면 그것을 사용)"
fi
exec python /opt/jobs.py
