# n8n 워크플로우 — 파이프라인 전체 재구성 (2026-11-19)

> 요청(승인자): 지금까지의 작업 전체를 n8n 워크플로우로 재설계(Codex 연동 포함)하고, 컨테이너 실행 때마다 n8n API 키를 새로
> 만들고 문서를 갱신하는 자동화가 가능한지 조사.
> 도식: `docs/architecture/n8n_pipeline.drawio` (draw.io로 열기 — 인프라 상세 없음).
> 워크플로우 원본: `docker/n8n/nexus_*.json` — 생성기 `scripts/build_n8n_workflows.py`(손으로 고치지 말고 생성기를 고친다).

## 1. 구성

n8n은 일정과 순서만 맡고, 실제 일은 runner 컨테이너의 정해진 작업(`docker/jobs.py`)이 한다. 각 단계는 `POST http://runner:8000/run/<작업>`.

| 워크플로우 | 실행 시점 | 단계(순서) |
|---|---|---|
| Nexus 일일 파이프라인 | 화~토 06:00 KST(미국 장 마감 후) + 수동 | 무료 커넥터 수집 → TE 시세 갱신 → Codex 비정형 크롤러 → 일별 비정형 다이제스트 → 마트·게이트 → 기준선 성적표 → 해상 경로·G2 화면 → 테스트 → Codex 교차검증 → 결과 점검 |
| Nexus 주간 정비 | 일 07:00 + 수동 | TE 시세 공백 복구 → 수동 업로드 파서 → 마트·게이트 → 기준선 성적표 → 해상 경로·G2 화면 → Obsidian 볼트 보기 내보내기 → 결과 점검 |
| Databento 유료 수집(수동) | 수동만(유료 — 실행 전 비용 확인) | Databento 수집 → 마트·게이트 → 결과 점검 |
| Nexus 실패 알림 | 위 워크플로우가 멈출 때(오류 워크플로우) | 실패 노드·오류 메시지를 알림 기록으로 |

- '무료 커넥터 수집'은 경제·기후·지정학·작황·생산·상품·관세청·COT·GeoIntel·해운·PortWatch·해사 경보 12종을 한 번에 돈다(각 커넥터 실패는 비치명).
- 마트·게이트·기준선·테스트는 실패 시 그 작업 안에서 멈춘다(fail-closed). 나머지는 실패해도 다음 단계로 간다.
- GitHub Actions는 `docs/operations/actions_scope.md`에 남긴 4종(PR 검사·이슈→보드·위키·교차검증)만 유지한다.

## 2. 실패 알림

- 각 작업 노드는 오류를 던지지 않고 응답(상태 코드·실패 단계·로그 경로)을 그대로 넘긴다.
- 마지막 '결과 점검' 노드가 실패 단계를 모으고, 실패가 있을 때만 runner `/alert`로 보낸다 → `docker/logs/alerts.jsonl`에 한 줄씩 기록.
- 워크플로우 자체가 멈추면(타임아웃·노드 오류) '오류 워크플로우'가 같은 곳으로 기록한다.
- 메일·메신저 알림이 필요하면 '실패 알림 기록' 노드 뒤에 해당 노드를 붙인다(자격 증명은 n8n 화면에서만 입력 — 저장소에 넣지 않음).

## 3. Codex 연동 계약 (`scripts/codex_bridge.py`)

승인자가 Codex로 만드는 도구를 파이프라인에 끼우는 자리. 도구가 완성되기 전에는 두 단계 모두 **건너뜀(성공)** 으로 끝난다.

| 단계 | 설정(로컬 `.env`) | 동작 |
|---|---|---|
| Codex 비정형 크롤러 | `CODEX_CRAWLER_CMD` — 실행 명령 | 명령 실행 → `data/processed/unstructured_crawl_*.parquet` 최신 파일의 계약 검증. 위반이면 실패 → 알림 |
| Codex 교차검증 | `CODEX_VERIFY_CMD`(선택) — 없으면 `codex exec --sandbox read-only` | 오늘 생성된 보고서·화면·처리 데이터 목록을 넘겨 읽기 전용 점검 → `reports/ops/codex_verify_YYYY-MM-DD.md` |

**크롤러 산출 계약**
- as-of 5필드: `event_time`, `release_time`, `available_at`, `ingested_at`, `source_vintage` — `available_at ≥ event_time`, 미래 `available_at` 금지.
- 출처 4필드: `source_name`, `source_url`(결측 금지), `retrieved_at`, `content_sha256`(중복 판별).
- 봇 차단 사이트는 우회하지 않는다(공식 피드·공개 RSS만). 본문 전문 대신 요약·발췌를 저장한다(저작권).
- **runner 연동 완료(2026-11-19)**: 이미지에 Codex CLI 0.166.0 설치(공식 Node 이미지에서 다단계 복사). 호스트 `~/.codex/auth.json`을 읽기 전용으로 `/run/secrets/codex_auth.json`에 마운트하고, 시작 시 컨테이너 전용 `CODEX_HOME`으로 복사함(`docker/entrypoint.sh` — 값은 출력하지 않음). 실측: `codex exec --sandbox read-only` 최소 질의 성공.
- 주의: 컨테이너가 로그인 토큰을 갱신하면 데스크톱 앱 쪽 토큰이 무효가 될 수 있음(갱신 토큰 순환). 데스크톱 앱이 로그아웃되면 다시 로그인하고 runner를 재시작함. 반복되면 `OPENAI_API_KEY`(사용량 과금)로 전환하는 것이 대안.
- 다른 계정 파일을 쓰려면 `.env`에 `CODEX_AUTH_JSON=<경로>`를 둠(기본 `%USERPROFILE%\.codexuth.json`).

## 4. 가져오기·켜기

```bash
docker compose -f docker/compose.yml exec n8n n8n import:workflow --input=/workflows/nexus_daily.json
```
- 파일별로 가져온다(폴더 통째로 가져오면 예전 `g2_preview.json`까지 다시 들어와 중복이 생긴다).
- 가져온 워크플로우는 꺼진 상태 — n8n 화면에서 켠다. 2026-11-19에 4종을 가져와 두었다(꺼짐).
- runner의 `/alert` 수신과 Codex 작업은 runner 이미지 재빌드 후 동작한다(`jobs.py`가 이미지에 들어감).
- 예전 'Nexus G2 Preview 파이프라인'(g2-preview·nexusG2Preview01 2건)은 일일 파이프라인이 대신한다 — n8n 화면에서 삭제 권장.

## 5. API 키 자동 발급 조사 (요청 1.1)

**결론: 기술적으로는 가능하지만 권하지 않는다. 워크플로우 배포에는 API 키가 아예 필요 없다.**

| 확인 항목(n8n 2.22.6 실측) | 결과 |
|---|---|
| CLI로 API 키 생성 | 없음. `import/export:workflow`, `list/publish/unpublish:workflow`, `user-management:reset` 등만 있음 |
| 환경변수로 API 키 지정 | 없음. 환경변수로 관리되는 건 소유자 계정(`N8N_INSTANCE_OWNER_EMAIL`·`N8N_INSTANCE_OWNER_PASSWORD_HASH`·`N8N_INSTANCE_OWNER_MANAGED_BY_ENV`)·커뮤니티 패키지·로그 스트리밍·보안 정책 |
| 공개 API(`/api/v1`)로 키 생성 | 없음 — 공개 API를 쓰려면 이미 키가 있어야 함 |
| 내부 REST `POST /rest/api-keys` | 존재(키 생성·조회·삭제·범위 조회). 로그인 세션 필요 — 인증 없이 호출하면 401(실측) |

**가능한 자동화 경로**: 컨테이너 시작 후 보조 스크립트가 ① `POST /rest/login`(소유자 이메일·비밀번호) → ② 이전 자동 키 삭제 → ③ `POST /rest/api-keys`(이름·범위) → ④ 새 키를 gitignore된 `.env`에 기록.

**권하지 않는 이유**
1. 내부 REST는 문서화되지 않은 경로라 n8n 버전이 바뀌면 깨질 수 있다.
2. 소유자 비밀번호를 평문으로 `.env`에 둬야 한다(키보다 권한이 큰 비밀).
3. 시작할 때마다 키를 바꾸면 그 키를 쓰는 MCP 클라이언트 설정도 매번 바꿔야 한다.
4. **README에 키를 쓰면 저장소 커밋으로 유출된다** — 어떤 경우에도 README가 아니라 gitignore된 `.env`에만 둔다.

**권장**
- 워크플로우 배포·갱신은 키가 필요 없는 CLI `n8n import:workflow`로 한다(이번 작업에서 실측 성공).
- API 키는 화면에서 한 번 만들어 gitignore된 `.env`(또는 MCP 설정 파일)에 두고, 분기마다 손으로 교체한다.
- 그래도 자동 교체를 원하면 위 4단계를 별도 스크립트로 만들 수 있다(승인 후 — 소유자 비밀번호 보관 방식 결정 필요).
