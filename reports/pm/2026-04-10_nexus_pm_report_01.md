# Nexus PM 보고서 — 2026-04-10 — Session 01
> **에이전트**: C-01 Senior PM (Claude Sonnet 4.6)
> **컨텍스트 재구성 완료**: README.md §QR ✅ · MEMORY.md ✅ · CLAUDE.md §6 ✅ · git log ✅

---

## 1. 전체 진행률

| Phase | 상태 | 완료 작업 | 전체 작업 | 진행률 |
|---|---|---|---|---|
| Phase 1 — Foundation | 🟡 준비중 | 0 | 31 | 0% |
| Phase 2 — Modeling | 🔴 미시작 | 0 | 30 | 0% |
| Phase 3 — Optimization | 🔴 미시작 | 0 | 18 | 0% |
| Phase 4 — Productionize | 🔴 미시작 | 0 | 10 | 0% |
| Phase 5 — Governance | 🔴 미시작 | 0 | 9 | 0% |
| **전체** | 🟡 | **0** | **98** | **0%** |

**인프라 준비 현황** (분석 작업 전 선행 완료 항목):

| 항목 | 상태 |
|---|---|
| GitHub 리포지토리 생성 및 Claude Code 연동 | ✅ |
| CLAUDE.md, README.md, MEMORY.md, Skills.md 구축 | ✅ |
| `.claude/rules/` 경로별 규칙 파일 생성 | ✅ |
| `.claude/skills/` 공통 에이전트 8종 정의 | ✅ |
| `src/utils/` LLM 라우터 + 3종 API 클라이언트 구축 | ✅ |
| GitHub Secrets: PERPLEXITY_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY | ✅ |
| WBS 전체 초안 및 Phase 1 상세 WBS 작성 | ✅ |
| 키 보관소 키 등록 | 🚫 블로커 (B-001) |

---

## 2. WBS 현황 — Phase 1 우선 착수 대상 작업

| WBS ID | 작업명 | 담당 에이전트 | 상태 | 예상 공수 | 선행 조건 |
|---|---|---|---|---|---|
| 1.1.1 | Design DW Raw Schema for External Indicators | C-04 + P1-05 | ⬜ | 16h | — |
| 1.1.2 | Implement Economic Indicators Connector (Fed, CPI, FX, WTI) | C-04 | ⬜ | 24h | 1.1.1 완료 |
| 1.4.1 | Collect Global Market Intelligence Brief | C-02 | ⬜ | 24h | — (병행 가능) |
| 1.2.1 | Design DW Schema for S&OP Data | C-04 | ⬜ | 16h | — (병행 가능) |
| 1.1.3 | Implement Shipping Index Connector (BDI, SCFI) | C-04 | ⬜ | 16h | 1.1.1 완료 |

> **병행 가능 작업**: 1.1.1, 1.2.1, 1.4.1은 선행 조건 없음 → 즉시 동시 착수 가능.

---

## 3. 블로커 & 에스컬레이션

| # | 블로커 내용 | 유형 | 해결 경로 | 담당 | 우선순위 |
|---|---|---|---|---|---|
| B-001 | 키 보관소에 LLM API 키 미등록 — 사내 노트북에서 클라우드 Studio 접속 후 수행 필요 | 🟠 환경 | 클라우드 Cloud Shell에서 `az keyvault secret set` 3건 실행 (Step 3 절차서 참조) | 인간 (PM) | 높음 |
| B-002 | 사내 ERP → DW 직접 연동 IT 부서 승인 미확보 (WBS 1.2.4) | 🟣 결정 | IT 부서 협의 착수 필요 — HITL 에스컬레이션 | 인간 (구매/IT) | 높음 |
| B-003 | BDI 직접 API 유료 — Baltic Exchange 구독 미확보 | 🟣 결정 | (A) Baltic Exchange 구독 예산 승인 또는 (B) Perplexity C-02 수집으로 대체 | 인간 (PM) | 중간 |
| B-004 | Phase 1 에이전트 (P1-01~P1-05) 스킬 파일 미작성 | 🟡 의존성 | `.claude/skills/phase1/` 파일 작성 후 착수 가능 — 다음 세션 우선 처리 | C-01 → 다음 세션 | 중간 |

---

## 4. 전략적 우선순위 (WSJF Top 3)

*WSJF = (Business Value + Time Criticality + Risk Reduction) ÷ Job Size (1pt ≈ 8h)*

| 순위 | WBS ID | 작업명 | BV | TC | RR | Size (pt) | WSJF | 근거 |
|---|---|---|---|---|---|---|---|---|
| 🥇 1 | B-001 해결 | 키 보관소 LLM API 키 등록 | 9 | 10 | 8 | 0.5 | **54.0** | 미완료 시 모든 에이전트의 API 호출 불가 — 전체 프로젝트 차단 리스크 |
| 🥈 2 | 1.1.1 | Design DW Raw Schema for External Indicators | 8 | 9 | 7 | 2 | **12.0** | 1.1.2~1.1.6 모든 API 커넥터의 선행 조건 — 조기 완료 시 파급 효과 최대 |
| 🥉 3 | 1.4.1 | Collect Global Market Intelligence Brief (C-02 via Perplexity) | 7 | 6 | 5 | 3 | **6.0** | 선행 조건 없음; 병행 가능; G1 변수 풀 정의에 필수 인텔리전스 기반 제공 |

**4위 참고**: B-002 (IT 협의 착수) — WSJF 5.5 — 협의 지연 시 Phase 1 완료 일정 최대 4주 지연 가능.

---

## 5. HITL 결정 필요 항목

- [ ] **[B-001] 키 보관소 키 등록**: 사내 노트북에서 클라우드 Cloud Shell 접속 후 3개 API 키 (`PERPLEXITY_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`) 등록. Step 3 절차서 참조.
- [ ] **[B-002] 사내 ERP 연동 방식 결정**: (A) IT 부서 DW 전용 계정 요청 vs. (B) 주간 CSV 수동 추출 임시 방안 중 선택. IT 담당자와 협의 착수 시점 확정 필요.
- [ ] **[B-003] BDI API 조달 결정**: Baltic Exchange 구독 예산 승인 여부 확인. 미승인 시 Perplexity C-02 수집으로 대체 진행.
- [ ] **[향후] Phase 1~5 KPI 목표 수치 확정**: 현재 WBS에 "원가 절감률 목표", "선제 구매 성공 횟수" 등 정량적 KPI 미확정. 이해관계자(구매팀, 재무팀)와 협의 후 README.md 및 WBS에 반영 필요.

---

## 6. 다음 세션 시작점

1. **B-001 해결 여부 확인**: 키 보관소 등록 완료 시 → `src/utils/` 패키지 테스트 즉시 착수 (llm_health_check 워크플로우 실행)
2. **Phase 1 전문 에이전트 스킬 파일 작성**: `.claude/skills/phase1/` 내 P1-01~P1-05 파일 5개 작성 — 이후 1.4.1 (C-02), 1.4.2 (P1-02), 1.4.3 (P1-03) 병행 착수 가능
3. **WBS 1.1.1 착수 (C-04)**: DW Raw Schema 설계 → DDL 스크립트 작성 → `data/schemas/` YAML 파일 생성
