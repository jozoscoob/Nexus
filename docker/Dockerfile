# Nexus 로컬 실행 이미지 (D-053: 개인 노트북 Docker + n8n)
# 1단계: Codex CLI 설치 — 공식 Node 이미지에서만 npm 사용(apt nodejs/npm 의존성 수백 개 회피)
FROM node:22-slim AS codex
# mcpvault: Obsidian 볼트 뷰 읽기 전용 MCP(MIT, stdio) — AI 어시스턴트가 docker exec로 실행
RUN npm install -g @openai/codex@0.166.0 @bitbonsai/mcpvault@0.18.3 && npm cache clean --force

FROM python:3.11-slim
# libgomp1: lightgbm 런타임
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
# Codex CLI(승인자 지시 2026-11-19 — 파이프라인 Codex 단계): node 실행 파일 + 패키지만 복사
COPY --from=codex /usr/local/bin/node /usr/local/bin/node
COPY --from=codex /usr/local/lib/node_modules/@openai/codex /usr/local/lib/node_modules/@openai/codex
COPY --from=codex /usr/local/lib/node_modules/@bitbonsai/mcpvault /usr/local/lib/node_modules/@bitbonsai/mcpvault
RUN ln -s /usr/local/lib/node_modules/@openai/codex/bin/codex.js /usr/local/bin/codex \
    && ln -s /usr/local/lib/node_modules/@bitbonsai/mcpvault/dist/server.js /usr/local/bin/mcpvault
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY docker/jobs.py /opt/jobs.py
COPY docker/entrypoint.sh /opt/entrypoint.sh
WORKDIR /repo
ENV PYTHONPATH=/repo PYTHONUNBUFFERED=1 CODEX_HOME=/root/.codex
EXPOSE 8000
CMD ["sh", "/opt/entrypoint.sh"]
