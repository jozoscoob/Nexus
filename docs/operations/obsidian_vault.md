# Obsidian 볼트 연동 — 시맨틱 레이어·비정형 문서 보기 (2026-11-19)

> 승인자 지시: 시맨틱 레이어·온톨로지·문서 판독 결과를 Obsidian으로 직관적으로 다룬다(볼트: Google Drive 'Obsidian Vault').
> 2차 지시(같은 날 밤): 매일 07:00 KST 자동 복사, 비정형·반정형 자료(문서 포함) 전부 대상, 문서마다 요지·분류를 볼트에 저장.
> 원칙: **정본은 저장소**(YAML·문서 원본) — 볼트는 읽기용 보기다. 볼트에서 고친 내용은 다음 내보내기에서 사라진다.

## 흐름

```
src/semantic/*.yaml · docs/** · data/raw/**/Summary · References · docx · 일별 다이제스트·신호
   │  runner 작업 vault_export
   │    1) validate_semantic_layer.py --strict   — 실패하면 내보내지 않음
   │    2) export_obsidian_vault.py (+ export_vault_documents.py) → data/vault_view/Nexus (gitignore)
   ▼
호스트 작업 스케줄러 'Nexus Vault Sync' — 매일 07:00 KST (scripts/vault_daily_sync.ps1)
   │    runner에 내보내기 요청(다른 작업 중이면 1분 간격 최대 45분 대기) → sync_obsidian_vault.ps1(robocopy /MIR)
   ▼
Google Drive 'Obsidian Vault/Nexus'  ←  Obsidian(데스크톱·모바일)에서 열람·그래프 보기
   ▲
AI 어시스턴트: MCP 'nexus-vault'(mcpvault, 읽기 전용) — runner 안의 같은 보기를 검색·열람
```

같은 내보내기는 n8n '02 정제'·'00 시연'·'주간 정비'에서도 실행된다(볼트 보기 갱신). Drive 복사는 호스트 작업만 한다.

## 대상 자료와 볼트 구성 (2026-11-19 실측)

| 폴더 | 원천 | 형태 | 건수 |
|---|---|---|---|
| `용어/`·`인과/`·`노드/`·`분류/` | 시맨틱 레이어 YAML | 위키링크 노트 | 244 · 24 · 81 · 9 |
| `문서/연구/` | docs/research_desk(references 제외) | **문서 카드**: 분류 · 추출 요지 · 목차 · 원문 | 128 |
| `문서/운영/` · `문서/의사결정 원장/` | docs/operations·architecture · docs/memory_archive | 문서 카드 | 7 · 8 |
| `문서/docx/` | 시장 구조 보고서·관세청 기술문서(docx) | 본문 추출 카드 + 원본 첨부 | 2 |
| `비정형 요약/GAIN·FAO/{연도}/` | data/raw/**/Summary(USDA GAIN·FAO AMIS 문서 요약) | 요약 + 신호 태그·방향 frontmatter, 신호 색인 | 약 2,175 |
| `문헌 요약/` | references 요약 | 요약 | 68 |
| `문헌/G2 금융공학 방법`·`G3 관점` | data/raw/References 논문 | 첫 쪽 초록 발췌 카드 + 원본 첨부 + 적용 판정 문서 링크 | 16 · 10 |
| `일별/다이제스트`·`일별/신호` | 일별 비정형 다이제스트 · 일별 신호 CSV(반정형) | 원문 · 월별 표 | 2 · 3 |
| `문서 분류/` | 위 문서 카드 | 분류 허브(G1·G2·G3·시장 구조·공급망·정책·데이터·인프라·의사결정) | 10 |
| `첨부/` | 참고문헌 PDF·논문 PDF·docx | 원본 | 63 · 26 · 2 |

볼트 전체: 노트 약 2,800개 · 약 170 MB. **GAIN·FAO 원본 PDF(2,234건·약 1.6 GB)는 복사하지 않음** — 문서마다 요약이 이미 있고, 원본까지 넣으면 Drive 용량과 Obsidian 색인 부담이 커짐(필요하면 범위 확장 가능).

## 문서 요지·분류 방법 (D5)

- **분류**: 제목·본문 앞부분의 영역 키워드 빈도로 상위 3개 분류를 붙인다(G1 변인·유사국면 / G2 가격 범위·방법론 / G3 조달·시뮬레이션 / 시장 구조·가격 동인 / 공급망·해상 물류 / 정책·바이오연료 / 데이터·파이프라인 / 인프라·운영 / 의사결정·보고). 첫째 분류로 허브 노트에 묶음.
- **요지**: 규칙 기반 추출 — ①'결론:'으로 시작하는 줄 ②결론·요약·핵심 절 ③판정·권고 절 ④결정 필요 절 순으로 찾고, 없으면 첫 문단. LLM 요약이 아니므로 카드에 '추출 요지'로 표기한다.
- GAIN·FAO 요약은 기존 요약기의 신호 태그(재고·압착·바이오연료수요 등)와 방향(상방·하방 우세)을 태그로 올려 Obsidian 태그 검색·그래프로 묶인다.

## 설계 판단

| 쟁점 | 판단 | 근거 |
|---|---|---|
| 볼트 직접 쓰기 vs 보기 복사 | 보기 복사 | Docker는 Google Drive for Desktop 가상 드라이브(G:)를 마운트하지 못함(실측: 컨테이너 쓰기가 호스트에 안 보임) |
| 자동화 수단 | Windows 작업 스케줄러 | n8n 컨테이너도 G:를 보지 못함. n8n Google Drive 노드는 OAuth 등록이 필요해 불필요한 자격 증명이 늘어남 |
| 사용자 노트 보호 | 볼트 안 `Nexus/` 폴더만 관리 | 관리 표지 `.nexus_managed`가 없는 폴더는 덮어쓰지 않음(내보내기·동기화 양쪽 검사) |
| 볼트 → 저장소 역반영 | 하지 않음 | 정본 단일화. 수정은 저장소에서 하고 다시 내보냄 |
| 내보내기 실패 시 | 복사하지 않고 이전 보기 유지 | 검증 실패한 보기를 덮어쓰지 않음(로그: docker/logs/vault_daily_sync.log) |

## mcpvault 점검 (도입 전)

| 항목 | 결과 |
|---|---|
| 라이선스 | MIT |
| 버전 | 0.18.3 (2026-10-31 — 2주 이상 경과판 고정. 최신 0.18.4는 11-14) |
| 의존성 | 4개(yaml·trash·gray-matter·@modelcontextprotocol/server) |
| 통신 | stdio 전용 — 네트워크 포트 없음, 텔레메트리 언급 없음 |
| 경로 안전 | 볼트 밖 경로·심볼릭 링크 탈출 차단, 점파일·`.obsidian`·`.git` 제외, `.md` 등 확장자만 |
| 쓰기 | `--read-only`로 쓰기·삭제 도구 전부 숨김 — 실측 노출 도구 11개 전부 읽기 |
| 실행 위치 | runner 이미지에 설치(호스트 Node 불필요). `.mcp.json`의 `nexus-vault` = `docker exec -i docker-runner-1 mcpvault /repo/data/vault_view/Nexus --read-only` |

## 운영

- 자동: 작업 스케줄러 'Nexus Vault Sync' 매일 07:00 KST(첫 실행 2026-11-20). 볼트 경로는 작업 인수 `-VaultDir`로 전달(Drive 바로가기 대상은 목록 조회가 불안정해 자동 탐색이 0건이 될 수 있음 — 실측). 로그 `docker/logs/vault_daily_sync.log`. 2026-11-19 시험 실행: 노트 2,789개 반영.
- 수동: `powershell -ExecutionPolicy Bypass -File scripts\vault_daily_sync.ps1`(내보내기+복사) 또는 `scripts\sync_obsidian_vault.ps1`(복사만).
- 조건: Docker Desktop과 Google Drive for Desktop이 켜져 있어야 함(로그인 상태에서 실행). 07:00에 PC가 꺼져 있으면 켜진 뒤 실행(StartWhenAvailable).
- 참고 자료: mcpvault 저장소 확인. wikidocs 안내문은 접속이 거부(403)되어 보지 못했고, 블로그·영상 안내는 위 설계에 필요한 사실(경로·인증)이 저장소 문서로 충분해 대조하지 않음.
