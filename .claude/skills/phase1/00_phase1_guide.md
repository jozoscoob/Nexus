# Phase 1 Guide — Foundation
> **실행 환경**: Claude Code & GitHub → 로컬 Docker(n8n → runner 컨테이너) → 저장소 parquet + DuckDB
> **목표**: 모든 분석의 토대가 되는 데이터 파이프라인 구축 및 G1 변수 풀 확정
> **총 예상 공수**: ~560h (보고 체계 포함)
> **Phase 2 진입 조건**: 1.3.5 통합 EDA 보고서 완료 + 1.4.7 G1 변수 풀 최종 문서화

---

## Phase 1 에이전트 로스터

> 이 파일을 로드하면 Phase 1 전체 컨텍스트를 확보합니다. 개별 에이전트 스킬 파일은 해당 작업 착수 직전에만 로드하세요 (WISC §Select 원칙).

| 에이전트 | 역할 | 모델 | 담당 WBS | 스킬 파일 |
|---|---|---|---|---|
| **C-01** | Senior PM | Opus 4.8 | 전체 오케스트레이션 | `common/01_senior_pm.md` |
| **C-02** | 시장 조사 전문가 | Perplexity Pro | 1.4.1 (시장 인텔리전스) | `common/02_market_research.md` |
| **C-04** | 데이터·ML 인프라 엔지니어 | Sonnet 4.6 | 1.1.x, 1.2.x | `.claude/agents/c04-document-intelligence.md` |
| **C-07** | 문서화·지식 관리자 | Haiku 4.5 | 1.1.9, 1.2.6, 1.3.5, 1.4.7 | `common/07_documentation_agent.md` |
| **C-08** | 데이터 품질 검증자 | Haiku 4.5 | 1.1.8, 1.2.5 | `common/08_data_validator.md` |
| **C-06** | EDA 에이전트 | Sonnet 4.6 | 1.3.1~1.3.4 | `common/06_eda_agent.md` |
| **C-03** | 데이터 사이언티스트 | Sonnet 4.6 | 1.5.1~1.5.4, 1.4.6 | `common/03_data_scientist.md` |
| **P1-01** | 원자재 분석가 | **Opus 4.8** | 1.4.1, 1.4.5 | `phase1/01_commodity_analyst.md` |
| **P1-02** | 지정학·무역 리스크 분석가 | **Opus 4.8** | 1.4.2 | `phase1/02_geopolitical_analyst.md` |
| **P1-03** | 농기상·기후 전문가 | **Sonnet 5** | 1.4.3 | `phase1/03_climate_specialist.md` |
| **P1-04** | 공급망·물류 분석가 | **Sonnet 5** | 1.4.4 | `phase1/04_supply_chain_analyst.md` |
| ~~P1-05~~ | ~~데이터 파이프라인 아키텍트~~ | *(폐기)* | 1.1.1, 1.1.4~1.1.6 → **C-04** | C-04와 역할 중복 — WBS 완료 후 통합 |

---

## 실행 환경 가이드

```
Claude Code & GitHub
  └─ 코드 작성, 스킬 파일, 스키마 설계 문서, GitHub Actions YAML, 보고서(Markdown)
  └─ 담당 작업: 1.1.1, 1.1.7, 1.1.9, 1.2.1~1.2.3, 1.2.6, 1.3.5, 1.4.x, 1.5.4

로컬 Docker (n8n → runner 컨테이너)
  └─ Python 실행, API 커넥터, great_expectations, EDA, 기준선 모델
  └─ 담당 작업: 1.1.2~1.1.6, 1.1.8, 1.2.5, 1.3.1~1.3.4, 1.5.1~1.5.3

저장소 parquet + DuckDB
  └─ 외부 데이터 저장·질의(ASOF JOIN) — 내부 ERP 데이터는 사용하지 않음(D-021)
```

---

## GitHub Secrets 현황 (2026-04-15 기준)

| 시크릿 명 | 용도 | 상태 |
|---|---|---|
| `PERPLEXITY_API_KEY` | 실시간 시장 조사 (C-02, P1-01, P1-02) | ✅ 등록 완료 |
| `GEMINI_API_KEY` | 대용량 문서 분석 | ✅ 등록 완료 |
| `OPENAI_API_KEY` | 구조화 추출 | ✅ 등록 완료 |
| `FRED_API_KEY` | Fed 금리, CPI 시계열 (1.1.2) | ✅ 등록 완료 |
| `EIA_API_KEY` | WTI/Brent 유가 (1.1.2) | ✅ 등록 완료 |
| `BOK_ECOS_API_KEY` | KRW/USD 환율 (1.1.2) | ✅ 등록 완료 |

---

## WBS 빠른 참조 — Phase 1 작업 현황

| WBS ID | 작업명 | 담당 | 실행 환경 | 상태 |
|---|---|---|---|---|
| 1.1.1 | 외부 지표 Raw 스키마 설계 | **C-04** | Claude Code | ✅ (data/schemas/*.yaml) |
| 1.1.2 | 경제 지표 커넥터 (Fed/CPI/FX/WTI) | C-04 | VS Code Web | ✅ |
| 1.1.3 | 해운 지수 커넥터 (BDI/SCFI) | C-04 | VS Code Web | ✅ |
| 1.1.4 | WASDE/USDA 작황 커넥터 | **C-04** | VS Code Web | ✅ |
| 1.1.5 | ENSO/기상 이상 커넥터 | **C-04** | VS Code Web | ✅ |
| 1.1.6 | 지정학 리스크 지수 커넥터 | **C-04** | VS Code Web | ✅ |
| 1.1.7 | API 재시도 로직 + Actions 스케줄 | C-04 | Claude Code | ✅ |
| 1.1.8 | 외부 파이프라인 품질 검증 | C-08 | VS Code Web | ⬜ |
| 1.1.9 | 외부 스키마 문서화 | C-07 | Claude Code | ⬜ |
| 1.2.1 | S&OP 스키마 설계 | C-04 | Claude Code | ⬜ |
| 1.2.2 | 구매 이력 스키마 설계 | C-04 | Claude Code | ⬜ |
| 1.2.3 | 재고·물류 스키마 설계 | C-04 | Claude Code | ⬜ |
| 1.2.4 | ERP 동기화 파이프라인 구현 | C-04 | — | ⛔ 폐기(D-021 내부 데이터 미사용) |
| 1.2.5 | 내부 파이프라인 품질 검증 | C-08 | VS Code Web | ⬜ |
| 1.2.6 | 내부 스키마 문서화 | C-07 | Claude Code | ⬜ |
| 1.3.1 | 외부 가격 지표 EDA | C-06 | VS Code Web | ⬜ |
| 1.3.2 | 기후·작황 EDA | C-06 | VS Code Web | ⬜ |
| 1.3.3 | 내부 S&OP EDA | C-06 | VS Code Web | ⬜ |
| 1.3.4 | 구매·물류 EDA | C-06 | VS Code Web | ⬜ |
| 1.3.5 | 통합 EDA 보고서 | C-07 | Claude Code | ⬜ |
| 1.4.1 | 글로벌 시장 인텔리전스 브리프 | C-02+P1-01 | Claude Code+Perplexity | ⬜ |
| 1.4.2 | 지정학·무역 리스크 분석 | P1-02 | Claude Code+Perplexity | ⬜ |
| 1.4.3 | 기후·작황 리스크 분석 | P1-03 | Claude Code+Perplexity | ⬜ |
| 1.4.4 | 공급망·물류 리스크 분석 | P1-04 | Claude Code+Perplexity | ⬜ |
| 1.4.5 | 상위 20 변수 식별 및 순위 결정 | P1-01 | Claude Code | ⬜ |
| 1.4.6 | 변수 데이터 가용성·예측력 점수화 | C-03 | Claude Code | ⬜ |
| 1.4.7 | 최종 변수 풀 문서화 | C-07 | Claude Code | ⬜ |
| 1.5.1 | 계절 나이브 기준선 구현 | C-03 | VS Code Web | ⬜ |
| 1.5.2 | 전일 값 나이브 기준선 구현 | C-03 | VS Code Web | ⬜ |
| 1.5.3 | 기준선 성능 지표 산출 | C-03 | VS Code Web | ⬜ |
| 1.5.4 | 기준선 코드 품질 리뷰 | C-05 | Claude Code | ⬜ |
| **1.6.1** | **주간 외부 파이프라인 상태 보고** | C-08+C-07 | Claude Code | ⬜ |
| **1.6.2** | **월간 시장 인텔리전스 브리프** | P1-01+C-02 | Claude Code+Perplexity | ⬜ |
| **1.6.3** | **월간 Phase 1 진행 보고 (PM 보고서)** | C-01 | Claude Code | ⬜ |
| **1.6.4** | **분기별 변수 풀 및 기준선 검토** | P1-01+C-03 | Claude Code | ⬜ |

---

## Phase 1 의존성 구조

```
즉시 착수 가능 (선행 조건 없음):
  1.1.1 → 1.1.2, 1.1.3, 1.1.4, 1.1.5, 1.1.6 (1.1.1 완료 후)
  1.2.1, 1.2.2, 1.2.3 (병행 가능)

외부 파이프라인 완료 후:
  1.1.2~1.1.6 → 1.1.7 → 1.1.8 → 1.1.9
  1.1.8 → 1.3.1, 1.3.2 → 1.5.1, 1.5.2 (병행)

내부 파이프라인 완료 후 (IT 승인 필요):
  1.2.1~1.2.3 → 1.2.4 → 1.2.5 → 1.2.6

EDA 완료 후:
  1.3.1~1.3.4 → 1.3.5 → 1.4.1 → 1.4.2, 1.4.3, 1.4.4 → 1.4.5 → 1.4.6 → 1.4.7

보고 체계 (반복 주기):
  1.6.1: 매주 (1.1.7 이후부터)
  1.6.2, 1.6.3: 매월
  1.6.4: 분기별
```

---

## Phase 1 주요 블로커

| ID | 블로커 | 유형 | 담당 | 우선순위 |
|---|---|---|---|---|
| B-002 | 사내 ERP 연동 (1.2.4) | ⛔ 폐기 | — | D-021로 해소 |
| B-003 | BDI 직접 API 유료 — Baltic Exchange 구독 미확보 | 🟣 결정 | 인간 (PM) | 중간 |
| B-004 | ~~P1-03, P1-04, P1-05 스킬 파일 미작성~~ | ✅ 해소 | P1-03·P1-04 완성; P1-05 C-04 흡수로 폐기 | — |

---

## 이 파일 로드 방법

```
Phase 1 작업 시작 시:
  1. 이 파일 (phase1/00_phase1_guide.md) 로드 → 전체 컨텍스트 확보
  2. 해당 작업의 에이전트 스킬 파일만 추가 로드 (예: P1-01 작업 시 01_commodity_analyst.md)
  3. 관련 .claude/rules/ 파일 로드 (data_pipeline.md 또는 modeling.md)

모든 파일을 동시에 로드하지 마세요 — WISC §Select 원칙
```
