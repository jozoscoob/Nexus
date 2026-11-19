# Obsidian 볼트 연동 — 시맨틱 레이어·문헌 요약 보기 (2026-11-19)

> 승인자 지시: 시맨틱 레이어·온톨로지(.md)·문서 판독 결과를 Obsidian으로 직관적으로 다룬다. 볼트는 Google Drive 'Obsidian Vault'.
> 원칙: **정본은 저장소 YAML**(`src/semantic/*.yaml`) — 볼트는 읽기용 보기다. 볼트에서 고친 내용은 다음 내보내기에서 사라진다.

## 흐름

```
src/semantic/entities.yaml · ontology.yaml · references/summaries/*.md
   │  runner 작업 vault_export (n8n 주간 정비 마지막 단계, 일 07:00)
   │    1) validate_semantic_layer.py --strict  — 실패하면 내보내지 않음
   │    2) export_obsidian_vault.py             → data/vault_view/Nexus (gitignore)
   ▼
호스트 scripts/sync_obsidian_vault.ps1 (robocopy /MIR — 볼트 안 'Nexus' 폴더만)
   ▼
Google Drive 'Obsidian Vault/Nexus'  ←  Obsidian(데스크톱·모바일)에서 열람·그래프 보기
   ▲
Claude: MCP 'nexus-vault'(mcpvault, 읽기 전용) — runner 안의 같은 보기를 검색·열람
```

## 볼트 구성 (2026-11-19 첫 내보내기 기준)

| 폴더 | 내용 | 건수 |
|---|---|---|
| `Nexus 홈.md` | 목차·건수·편집 규칙 | 1 |
| `용어/` | entities.yaml 용어 — 별칭에 국문명·약어·동의어·TERM-ID(그래서 `[[TERM-041]]`도 연결됨) | 244 |
| `인과/` | ontology.yaml 인과 사슬(원인→경로→결과·시차·근거·지표) | 24 |
| `노드/` | 인과 DAG 노드 — 들어오고 나가는 사슬(그래프 보기용) | 81 |
| `분류/` | 용어 분류 허브 | 9 |
| `문헌 요약/` | references 요약(원문·전문 변환본은 저작권상 내보내지 않음) | 68 |

위키링크는 용어 표준명·TERM-ID·인과 ID·노드명과 1:1로 맞춘다. 태그: `nexus/용어`·`nexus/인과`·`nexus/status/validated` 등.

## 설계 판단

| 쟁점 | 판단 | 근거 |
|---|---|---|
| 볼트 직접 쓰기 vs 보기 복사 | 보기 복사 | Docker는 Google Drive for Desktop 가상 드라이브(G:)를 마운트하지 못함(실측: 컨테이너 쓰기가 호스트에 안 보임). 호스트 복사가 유일한 무설정 경로 |
| 사용자 노트 보호 | 볼트 안 `Nexus/` 폴더만 관리 | 관리 표지 `.nexus_managed`가 없는 폴더는 덮어쓰지 않음(내보내기·동기화 양쪽 검사) |
| 볼트 → YAML 역반영 | 하지 않음 | 정본 단일화. 수정은 YAML에서 하고 검증기 통과 후 다시 내보냄 |
| Claude 접근 | mcpvault 0.18.3 읽기 전용 | 아래 보안 점검 |
| n8n Google Drive 노드 | 보류(결정 필요) | Google OAuth 자격증명을 n8n 화면에서 등록해야 함 — 호스트 복사로 충분하면 불필요 |

## mcpvault 점검 (도입 전)

| 항목 | 결과 |
|---|---|
| 라이선스 | MIT |
| 버전 | 0.18.3 (2026-10-31 — 2주 이상 경과판 고정. 최신 0.18.4는 11-14) |
| 의존성 | 4개(yaml·trash·gray-matter·@modelcontextprotocol/server) |
| 통신 | stdio 전용 — 네트워크 포트 없음, 텔레메트리 언급 없음 |
| 경로 안전 | 볼트 밖 경로·심볼릭 링크 탈출 차단, 점파일·`.obsidian`·`.git` 제외, `.md` 등 확장자만 |
| 쓰기 | `--read-only`로 쓰기·삭제 도구 전부 숨김 — 실측 노출 도구 11개 전부 읽기(read_note·search_notes 등) |
| 실행 위치 | runner 이미지에 설치(호스트 Node 불필요). `.mcp.json`의 `nexus-vault` = `docker exec -i docker-runner-1 mcpvault /repo/data/vault_view/Nexus --read-only` |

## 운영

- 내보내기: n8n 주간 정비(일 07:00) 마지막 단계 또는 수동 `POST /run/vault_export`.
- 볼트 반영: `powershell -ExecutionPolicy Bypass -File scripts\sync_obsidian_vault.ps1`(볼트 자동 탐색, 또는 `-VaultDir`·`OBSIDIAN_VAULT_DIR`).
- 첫 반영 완료: 2026-11-19, 노트 427개.
- 참고 자료: mcpvault 저장소 확인. wikidocs 안내문은 접속이 거부(403)되어 보지 못했고, 블로그·영상 안내는 위 설계에 필요한 사실(경로·인증)이 저장소 문서로 충분해 대조하지 않음.

## 결정 필요

1. 호스트 동기화 자동화: Windows 작업 스케줄러에 `sync_obsidian_vault.ps1` 등록(일 07:30)할지, 필요할 때 수동 실행할지.
2. n8n Google Drive 노드 경로(OAuth 등록) — 호스트 동기화로 충분하면 불필요.
3. 범위 확장: 연구 문서(`docs/research_desk`)·G2/G3 논문 요약까지 볼트에 넣을지(현재는 시맨틱 레이어 + references 요약).
