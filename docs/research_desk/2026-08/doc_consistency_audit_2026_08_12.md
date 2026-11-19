# 문서 정합성 감사 — 미갱신·중복 문서 전수 점검 (Req 3)

**작성일**: 2026-08-12 · **작성**: C-01
**범위**: `CLAUDE.md` · `README.md` · `.claude/rules/*` · `.claude/agents/*` · `.claude/skills/*` ·
`docs/research_desk/2026-08/*` · `data/raw/**/README.md`
**기준**: 2026-08-12 모델 전략 패키지 · D-021 · C-012/C-013(Gemini 배제) · L-012/M-006(모델 승급) ·
A-062(GPR 임계) · A-094~A-100(장애 수정)

---

## 1. 이번 감사에서 **갱신한** 문서 (13종)

| 문서 | 미갱신 내용 | 조치 |
|---|---|---|
| `CLAUDE.md` §1 | 목표 정의가 구식(G2=가격밴드 일반). D-006 잔존 | Champion–Challenger·1·5·20·60일 지평·as-of 규칙·D-021 명시 추가 |
| `README.md` §QR·§2·§4 | G1=LASSO, G2=VMD-LSTM, G3=TFT+Monte Carlo | Champion/Challenger 표로 교체, VMD 제외 경고, as-of §4.3 신설, G3에 D-021 경계 |
| `README.md` 용어집 | VMD를 사용 기법으로 서술 | "2026-08-12 기본 구성 제외" 명기 |
| `.claude/rules/modeling.md` G1 | LASSO·RF MDI·LDA 중심 | Elastic Net + LightGBM/XGBoost + Permutation + 국소투영 |
| `.claude/rules/modeling.md` G2 | VMD→GARCH→LSTM/TFT→CQR | SARIMAX + Quantile LightGBM + EGARCH-X + **EnCQR**, Challenger 분리 |
| `.claude/rules/modeling.md` G2 제약 | D-006(“Phase B 내부검증”) 잔존 | D-021로 통일 — 사후 검증에도 내부 데이터 미사용 |
| `.claude/rules/modeling.md` 공통 | "ARIMA/GARCH 전 항상 IQR 캡핑" | **데이터 오류·정상 노이즈에만** 적용으로 개정(충격 캡핑은 꼬리위험 학습 방해) |
| `.claude/rules/modeling.md` 검증 | "최소 24개월" 단일 기준 | 유효 시계열 길이·독립 충격 수·레짐별 사례 수 기준으로 대체, stress slice·lockbox 추가 |
| `.claude/rules/libraries.md` | `vmdpy` 승인 상태 | 제외 사유 주석 + duckdb·darts·neuralforecast·supabase·neo4j 신규 등재, mapie 용도 EnCQR로 갱신 |
| `.claude/agents/c03-data-scientist.md` | LASSO·Bayesian·TCN-XGBoost·GPR 0.022·DW 내부데이터 | **전면 재작성** — G1/G2/G3 전 목표 소유, 승격 규칙, 진입 게이트, 실험 카드, 금지 해석 |
| `.claude/skills/common/03_data_scientist.md` | LASSO·TCN 하이브리드·GPR 0.022·DW 내부데이터 | Elastic Net+Permutation+국소투영, 승격 규칙, D-021 정합, GPR P90 |
| `.claude/skills/phase1/00~04` · `INDEX.md` | 모델 표기 Opus 4.7 · C-04 sonnet-4-6 | L-012·M-006 반영(Opus 4.8 / Sonnet 5) — **잔여 0건** |
| `.github/workflows/llm_health_check.yml` | Gemini 점검 스텝·google-genai 의존성 | 제거(C-012 이행 완료 → C-013) |

---

## 2. **중복** 판정과 처리

| 대상 | 판정 | 처리 |
|---|---|---|
| `library_program_inventory_2026_08_11.md` ↔ `integration_setup_guide_2026_08_12.md` | **중복 아님** | 전자=현행 재고 목록, 후자=신규 도입 대상과 설치 절차. 후자 서두에 역할 분담 명시 |
| `session43_report_2026_08_11.md` ↔ `session45_failure_rootcause_2026_08_12.md` | **중복 아님** | 서로 다른 장애 세트. 단 session43의 CDS 진단(“안 쓰는 문 두드림”)은 session45 A-100이 **정정·확장**함 |
| `data/processed/gain_summaries/` 이중 생성 | **중복** | 제거 완료(요약은 Summary 폴더 v2로 단일화) |
| `.claude/agents/` 사용자 업로드 참고 문서 3종 | **원본 보존** | `Enterprise Semantic Architecture` · `Dual-Agent Guide` · `C-04 Role Framework`는 조정자 제공 원문이라 **편집하지 않는다**. 이들이 권고한 Gemini 채택은 C-010에서 이미 기각·대체됨(기록으로만 유지) |

---

## 3. 미갱신 → **의도적으로 유지**한 항목 (근거 포함)

| 항목 | 유지 사유 |
|---|---|
| `.claude/rules/data_pipeline.md`의 DW 패턴 | DW는 **도입 보류**이지 금지가 아니다. 향후 재검토 시 참조용으로 유지하되, 내부 데이터 용도는 D-021로 이미 차단 |
| `README.md` §3.2 내부 데이터 표 | 이미 "⛔ EXCLUDED (D-021)" 경고와 함께 **참고용**으로 명시됨 — 삭제하면 왜 제외됐는지 맥락이 사라진다 |
| 아카이브(`docs/memory_archive/*`) | 과거 기록은 **내용 무변경** 원칙(조정자 지시). 갱신 대상 아님 |
| `.claude/skills/phase2·phase3` | 해당 Phase 미착수 — 착수 시점에 전략 패키지 기준으로 개정 |

---

## 4. 남은 정합성 리스크 (다음 세션 처리 대상)

| 항목 | 내용 | 우선도 |
|---|---|---|
| `src/forecasting/variable_importance_g1.py` | ElasticNetCV·Granger·GPR P90은 반영됐으나 **국소투영·permutation importance·horizon×레짐 분해 미구현** | 높음(G1 8/31) |
| `data/schemas/*.yaml` (8종) | `available_at` · `release_time` · `source_vintage` 필드 부재 — 모델 진입 게이트 미충족 | **최상**(모든 모델의 선행 조건) |
| `src/risk/` | G3 레짐·의사결정 미구현(디렉터리 부재) | 중(G2 이후) |
| WBS xlsm | 신규 항목(1.1.53 비정형 시계열·Champion 전환·Supabase) 미반영 | 중 |

> **C-01 판단**: `data/schemas` as-of 필드 보강이 **최우선**이다. 조사 패키지 §7이 명시한 대로
> `available_at`이 없으면 어떤 모델도 투입할 수 없고, 이는 G1 8/31 마감의 선행 조건이다.
