# 로컬 실행 스택 (Docker + n8n) — D-053

개인 노트북에서 G2 Preview 파이프라인을 돌리는 최소 구성. GitHub Actions 대체.

| 구성 | 역할 |
|---|---|
| `runner` | Python 3.11 + 고정 의존성(`requirements.txt`). `POST /run/<작업>`으로 정해진 작업만 실행 |
| `n8n` | 수동 버튼·평일 06:00 KST 스케줄로 runner 작업을 순서대로 호출 (`http://localhost:5678`) |

작업: `databento` · `collect_free`(무료 커넥터 7종, 비치명) · `manual_parsers` · `mart`(준비도·마트·as-of 게이트, 실패 시 중단) · `baseline` · `tests`

## 처음 한 번
1. Docker Desktop(WSL2) 설치 확인.
2. 저장소를 **로컬 디스크**에 clone(Google Drive 스트리밍 폴더는 Docker 마운트가 느리거나 깨질 수 있음).
3. 저장소 루트에 `.env` 작성(커밋 금지 — gitignore 등록됨):
   ```
   DATABENTO_API_KEY=
   FRED_API_KEY=
   USDA_NASS_API_KEY=
   USDA_FAS_API_KEY=
   DATA_GO_KR_SERVICE_KEY=
   EIA_API_KEY=
   ```
4. `docker compose -f docker/compose.yml up -d --build`
5. 워크플로우 가져오기: `docker compose -f docker/compose.yml exec n8n n8n import:workflow --input=/workflows/g2_preview.json`
6. `http://localhost:5678`에서 계정 생성 → 워크플로우 열기 → **수동 실행**.

Databento 노드는 비활성 상태로 들어있다 — 인출 상한 승인(DQ-40) 후 켠다.
로그는 `docker/logs/`(커밋 안 함), 응답 JSON에 단계별 결과·마지막 출력이 담긴다.

## n8n 워크플로우 (2026-11-19)
- 파이프라인 전체를 n8n 워크플로우 4종으로 정의: 일일(화~토 06:00)·주간 정비(일 07:00)·Databento 유료(수동)·실패 알림.
  원본 `docker/n8n/nexus_*.json`(생성기 `scripts/build_n8n_workflows.py`), 설명·Codex 연동 계약·API 키 조사는 `docs/operations/n8n_workflows.md`.
- 가져오기(키 불필요): `docker compose -f docker/compose.yml exec n8n n8n import:workflow --input=/workflows/nexus_daily.json` — 파일별로.
- 실패 알림은 runner `/alert` → `docker/logs/alerts.jsonl`. API 키·비밀번호는 README가 아니라 gitignore된 `.env`에만 둔다.
