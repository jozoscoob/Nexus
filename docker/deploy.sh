#!/bin/sh
# 상시 서버 코드 갱신 — 읽기 전용 배포 키로 git pull (SPEC §3.4)
# 실행: sudo sh /opt/nexus/docker/deploy.sh
#
# - 원문 PDF는 받지 않음(sparse checkout '!*.pdf' + blob 지연 받기) — 서버는 요약만 사용
# - 서버가 실행 중 갱신하는 추적 파일(data/·reports/의 일부)은 그대로 둔다. 같은 파일이 저장소에서도
#   바뀌었으면 fast-forward가 거부되어 아무것도 바꾸지 않고 중단한다(덮어쓰기 없음).
# - 이미지에 구워지는 파일이 바뀌면 재빌드, compose·프록시 설정이 바뀌면 재기동. 그 밖의 코드는 바인드 마운트라 즉시 반영.
set -eu
cd /opt/nexus
BRANCH=$(git symbolic-ref --short HEAD)
export GIT_SSH_COMMAND="ssh -i /home/ubuntu/.ssh/nexus_deploy -o IdentitiesOnly=yes -o UserKnownHostsFile=/home/ubuntu/.ssh/known_hosts"
git fetch -q origin "$BRANCH"
OLD=$(git rev-parse HEAD)
NEW=$(git rev-parse "origin/$BRANCH")
if [ "$OLD" = "$NEW" ]; then
  echo "[정보] 이미 최신 — $BRANCH @ $(git log -1 --format='%h %s')"
  exit 0
fi
CHANGED=$(git diff --name-only "$OLD" "$NEW")
if ! git merge -q --ff-only "origin/$BRANCH"; then
  echo "[오류] 서버에서 바뀐 추적 파일과 저장소 변경이 겹쳐 갱신을 중단함(아무것도 바꾸지 않음) — 위 목록 확인"
  exit 1
fi
echo "[정보] 바뀐 파일:"
echo "$CHANGED" | sed 's/^/  /'
if echo "$CHANGED" | grep -qE '^docker/(Dockerfile|jobs\.py|requirements\.txt|entrypoint\.sh)$'; then
  echo "[정보] 이미지 구성 변경 — 재빌드·재기동"
  docker compose -f docker/compose.yml up -d --build
elif echo "$CHANGED" | grep -qE '^docker/(compose\.yml|codex-proxy/)'; then
  echo "[정보] compose·프록시 설정 변경 — 재기동"
  docker compose -f docker/compose.yml up -d
fi
if echo "$CHANGED" | grep -qE '^docker/n8n/.*\.json$'; then
  echo "[경고] n8n 워크플로우 JSON 변경 — n8n 가져오기(import:workflow)·게시는 별도로 실행해야 반영됨"
fi
echo "[완료] $(git log -1 --format='%h' "$OLD") → $(git log -1 --format='%h %s')"
