#!/usr/bin/env sh
# 화면 품질 점검(impeccable 결정론적 검사기 — LLM·키·네트워크 전송 없음). 호스트에 Node가 없으므로 도커 Node로 실행.
# 사용: sh scripts/design_check.sh [대상 경로…]   (기본: G2·G1 화면 템플릿)
# 종료 코드: 0 = 지적 없음, 2 = 지적 있음(검토 대상), 1 = 대상 판독 실패.
set -e
VER="${IMPECCABLE_VERSION:-4.8.0}"   # 2주 이상 지난 고정 버전(승인 2026-11-19)
TARGETS="${*:-src/reporting/templates}"
exec docker run --rm -e NPM_CONFIG_UPDATE_NOTIFIER=false -e DO_NOT_TRACK=1 \
  -v "$(pwd):/repo" -w /repo node:22-slim npx -y "impeccable@${VER}" detect $TARGETS
