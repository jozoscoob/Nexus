# Project Nexus — Full Project WBS
> **Version**: 1.6 · **Date**: 2026-05-26 · **Owner**: C-01 Senior PM
> **Format**: Phase → Deliverable → Task (Verb + Noun, 8–80h, agent assigned)
> **Status key**: ⬜ 미시작 · 🔄 진행중 · ✅ 완료 · 🚫 블로커
> **Note**: Methodology and data sources are `[M]` — subject to change. Task durations are estimates; revise after each phase kickoff.

---

## Summary: Effort Estimate by Phase

| Phase | 핵심 목표 | 예상 공수 (h) | 담당 주요 에이전트 |
|---|---|---|---|
| Phase 1 — Foundation | 데이터 파이프라인 + EDA + G1 변수 풀 | ~520h | C-04, C-06, P1-01~05 |
| Phase 2 — Modeling | G1 알림 + G2 가격 밴드 + G3 레짐 감지 | ~640h | C-03, P2-01~05 |
| Phase 3 — Optimization | 구매 최적화 + DSS + P&L 시뮬레이터 | ~480h | P3-01~06 |
| Phase 4 — Productionize | 자동화 파이프라인 + 대시보드 + ERP 연동 | ~320h | C-04, P3-02 |
| Phase 5 — Governance | 모델 모니터링 + KPI + 최종 문서화 | ~240h | C-07, C-03 |
| **Total** | | **~2,200h** | |

---

## Phase 1 — Foundation (~520h)
*목표: 모든 분석의 토대가 되는 데이터 파이프라인 구축 및 G1 변수 풀 확정*

### 1.1 External Data Pipeline (~160h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 1.1.1 | Design DW Raw Schema for External Indicators (SQL DDL) | C-04 | 16h | ✅ |
| 1.1.2 | Implement Economic Indicators API Connector (Fed, CPI, FX, WTI) | C-04 | 24h | ✅ |
| 1.1.3 | Implement Shipping Index Connector (BDI, SCFI via Perplexity) | C-04 | 16h | ✅ |
| 1.1.4 | Implement WASDE/USDA Crop Data Connector (FAS PSD) | C-04 | 24h | ✅ |
| 1.1.5 | Implement ENSO/Weather Anomaly Connector (NOAA CPC · ECMWF ERA5) | C-04 | 16h | ✅ |
| 1.1.6 | Implement Geopolitical Index Connector (GPR Index · Hormuz Monitor) | C-04 | 24h | ✅ |
| 1.1.7 | Implement Production & Agromet Connector (NASS · FAOSTAT · NASA POWER · Perplexity) | C-04 | 24h | ✅ |
| 1.1.8 | Validate External Pipeline Data Quality (pytest + GE) | C-08 | 8h | 🔄 |
| 1.1.9 | Document External Data Schemas in data/schemas/ | C-07 | 8h | ✅ |
| 1.1.10 | Implement Commodity Prices & Drought Connector (CBOT · ARS · CPO · USDM) | C-04 | 16h | ✅ |
| 1.1.11 | Implement Korea Customs HS 1507 Import Stats Connector (data.go.kr · Comtrade) | C-04 | 16h | ✅ |
| 1.1.12 | Implement Pipeline Quality PDF/HTML Report Generator | C-04 | 8h | ✅ |
| 1.1.13 | Implement G1 Variable Importance Analysis — LASSO + Structural Break Thresholds | C-03 | 32h | 🔄 |
| 1.1.14 | Add C-06 EDA Validation Gate to GitHub Actions Pipeline | C-04 | 8h | ✅ |
| 1.1.15 | Add C-08 DQSOps Data Quality Gate to GitHub Actions Pipeline | C-08 | 8h | ✅ |
| 1.1.16 | Implement LLM Model Monitor + Health Check Workflow | C-04 | 8h | ✅ |
| 1.1.17 | Implement Ralph Loop Auto-Issue Workflow (pipeline-failure-loop) | C-04 | 4h | ✅ |
| 1.1.18 | Implement Granger Causality Analysis — G1 Extension (2020~last year, by year) | C-03 | 16h | 🔄 |
| 1.1.19 | Implement Pipeline Quality Tests (tests/test_pipeline_quality.py) | C-08 | 8h | 🔄 |
| 1.1.20 | Extend Climate Connector — Open-Meteo 12 Production Regions (ERA5-Land daily) | C-04 | 16h | 🔄 |
| 1.1.21 | Fix BDI Historical Range (2020-01-01~) via TE getMarketsHistorical | C-04 | 4h | ✅ |
| 1.1.22 | Fix GPR openpyxl Bug + Introduce BACKFILL_MODE Pattern (A-030~A-032) | C-04 | 4h | ✅ |
| 1.1.23 | Refactor Historical Backfill Workflow — Add C-08→C-06→G1 Pipeline | C-04 | 8h | ✅ |
| 1.1.24 | AIS Strait Tanker Monitoring Connector — Hormuz·Malacca·Panama (Phase A) | C-04 | 16h | 🔄 |
| 1.1.25 | Parquet→Excel Export Utility (src/pipeline/export_data.py) | C-04 | 4h | ✅ |
| 1.1.26 | G1 Analysis Multi-Format Output — PDF + Markdown (all reports) | C-03 | 8h | ✅ |
| 1.1.27 | Hormuz Monitor Tech Analysis + Nexus Application Design (C-01/C-03/P-02) | C-01 | 4h | ✅ |
| 1.1.28 | Fix BDI TE SDK → Direct REST API (A-034: getMarketsHistorical 미존재 + pandas 2.0 호환) | C-04 | 4h | ✅ |
| 1.1.29 | Fix wasde_connector.py run() HISTORICAL_START_YEAR 미독취 (A-035) | C-04 | 2h | ✅ |
| 1.1.30 | PDF 한국어·영어 분리 출력 체제 구축 (generate_research_pdf.py --lang ko/en/both) | C-04 | 8h | ✅ |
| 1.1.31 | C-05 Automated Code Reviewer (QA/QC) 에이전트 신설 — Claude Haiku 4.5 | C-01 | 8h | ✅ |
| 1.1.32 | 2020~2025 역사 위기 분석 수정 보고서 (C-02×P-02 패널, Case D 미·중 관세 9/10) | C-02 | 16h | ✅ |
| 1.1.33 | GeoIntel 커넥터 신규 — USGS 지진·NOAA 기상·GDELT·NASA FIRMS + 복합 지수 0-100 | C-04 | 16h | ✅ |
| 1.1.34 | C-04 Document Intelligence 에이전트 신설 — PDF/XLSX 문서 수집 파이프라인 설계 | C-01 | 8h | ✅ |
| 1.1.35 | P1-05 News & Sentiment 에이전트 신설 — FinBERT Phase B 설계, Phase A Perplexity 프록시 | C-01 | 8h | ✅ |
| 1.1.36 | 전 에이전트 LLM 모델 업데이트 (Opus 4.8 / Sonnet 4.6 / Haiku 4.5-20251001) | C-01 | 2h | ✅ |

> **P1-05 역할 변경**: 폐기(Data Pipeline Architect)에서 신설(News & Sentiment Analyst)로 재지정.
> **Session 12–18 추가 (1.1.10~1.1.19)**: commodity_connector, customs_connector, report_generator, G1 LASSO, C-06/C-08 게이트, LLM 모니터, Ralph Loop, Granger 분석, GE 테스트.
> **Session 19 추가 (1.1.20~1.1.21)**: Open-Meteo 12개 생산지역 기후 커넥터 확장, BDI 히스토리 범위 수정.
> **Session 20 추가 (1.1.22~1.1.27)**: GPR 버그수정+BACKFILL_MODE, 백필 워크플로우 C-08→G1 파이프라인, AIS 해협 탱커 모니터, Excel 내보내기, G1 PDF+MD, Hormuz Monitor 분석.
> **Session 21 추가 (1.1.28~1.1.32)**: BDI REST API 교체, WASDE HISTORICAL_START_YEAR 수정, PDF KO/EN 분리, C-05 에이전트, 역사 분석 수정 보고서.
> **Session 23 추가 (1.1.33~1.1.36)**: GeoIntel, C-04/P1-05 에이전트 신설, LLM 모델 전면 업그레이드.

### 1.1.4x — 외부 문서 수집 파이프라인 (USDA FAS GAIN/GATS)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 1.1.40 | Design GAIN Report ingestion schema (data/schemas/gain_reports.yaml) | C-04 | 4h | 🔄 |
| 1.1.41 | Implement GAIN PDF → parquet connector (scripts/ingest_gain_reports.py) | C-04 | 16h | ⬜ |
| 1.1.42 | Implement GATS Excel → parquet connector (scripts/ingest_gats_data.py) | C-04 | 12h | ⬜ |
| 1.1.43 | Validate GAIN/GATS data quality via C-08 DQSOps | C-08 | 8h | ⬜ |
| 1.1.44 | Add GAIN/GATS ingestion to historical_backfill.yml | C-04 | 4h | ⬜ |

> 사용자가 USDA FAS GAIN 보고서(.pdf) 및 GATS 무역 통계(.xlsx)를 공유 예정 → 1.1.40 착수 준비 완료

### 1.2 Internal Data Pipeline — 전략적 보류 (Strategic Deferral)
> **C-01 결정 (2026-06-16)**: 내부 조달 데이터는 G1/G2/G3 모델 입력에서 전략적으로 제외.  
> 사유: ①선택 편향(과거 행동 복제) ②제약 오염(솔루션 공간 축소) ③월별 집계→일별 보간 허위 정밀도 ④경쟁 비교 불가.  
> 내부 데이터 역할: Phase B 사후 검증(post-hoc validation)만. 재검토 시점: G2 모델 6개월 운영 후.  
> 상세 근거: `docs/research_desk/c01_internal_data_exclusion_decision_2026_06_16.md`

| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 1.2.1 | Design DW Schema for S&OP Data | C-04 | 16h | ⏸ 전략적 보류 |
| 1.2.2 | Design DW Schema for Procurement History | C-04 | 16h | ⏸ 전략적 보류 |
| 1.2.3 | Design DW Schema for Inventory and Logistics | C-04 | 16h | ⏸ 전략적 보류 |
| 1.2.4 | Implement DW ERP Sync Pipeline | C-04 | 40h | ⏸ 전략적 보류 |
| 1.2.5 | Validate Internal Pipeline Data Quality | C-08 | 8h | ⏸ 전략적 보류 |
| 1.2.6 | Document Internal Data Schemas | C-07 | 8h | ⏸ 전략적 보류 |

### 1.3 EDA & Data Quality Reports (~72h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 1.3.1 | Execute EDA on External Price Indicators | C-06 | 16h | ⬜ |
| 1.3.2 | Execute EDA on Climate and Crop Data | C-06 | 16h | ⬜ |
| 1.3.3 | Execute EDA on Internal S&OP Data | C-06 | 16h | ⬜ |
| 1.3.4 | Execute EDA on Procurement and Logistics Data | C-06 | 16h | ⬜ |
| 1.3.5 | Compile Integrated EDA Summary Report | C-07 | 8h | ⬜ |

### 1.4 G1 Variable Pool Definition (~120h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 1.4.1 | Collect Global Market Intelligence Brief | C-02 | 24h | ⬜ |
| 1.4.2 | Analyze Geopolitical and Trade Risk Landscape | P1-02 | 24h | ⬜ |
| 1.4.3 | Analyze Climate and Crop Risk Landscape | P1-03 | 16h | ⬜ |
| 1.4.4 | Analyze Supply Chain and Logistics Risk | P1-04 | 16h | ⬜ |
| 1.4.5 | Identify Top 20 Candidate Price Variables | P1-01 | 24h | ⬜ |
| 1.4.6 | Score Variables by Data Availability and Predictive Value | C-03 | 8h | ⬜ |
| 1.4.7 | Document Final Variable Pool and Rationale | C-07 | 8h | ⬜ |

### 1.5 Baseline Model Benchmarks (~40h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 1.5.1 | Implement Seasonal Naive Price Baseline | C-03 | 8h | ⬜ |
| 1.5.2 | Implement Last-Value Naive Baseline | C-03 | 8h | ⬜ |
| 1.5.3 | Compute Baseline Performance Metrics (MAPE, RMSE, DA) | C-03 | 16h | ⬜ |
| 1.5.4 | Review Baseline Code Quality | C-05 | 8h | ⬜ |

---

## Phase 2 — Modeling (~640h) `[M]`
*목표: G1 변수 중요도 엔진, G2 가격 밴드 예측, G3 레짐 감지 모델 구축*

### 2.1 G1 Variable Importance Engine (~120h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 2.1.1 | Implement LASSO Feature Selection Pipeline | C-03 | 24h | ⬜ |
| 2.1.2 | Implement XGBoost Variable Importance Model | C-03 | 24h | ⬜ |
| 2.1.3 | Generate SHAP Explanations and Bar Charts | C-03 | 16h | ⬜ |
| 2.1.4 | Implement Random Forest MDI as Alternative | C-03 | 16h | ⬜ |
| 2.1.5 | Validate Results with Granger Causality Tests | C-03 | 24h | 🔄 |
| 2.1.6 | Review and Merge G1 Model Code | C-05 | 16h | ⬜ |

### 2.2 G1 Automated Alert System (~80h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 2.2.1 | Define Alert Thresholds per Variable (2σ rule) | P2-01 + C-03 | 16h | ⬜ |
| 2.2.2 | Implement Alert Detection Pipeline | C-04 | 24h | ⬜ |
| 2.2.3 | Implement Korean-Language Alert Message Generator | C-03 | 16h | ⬜ |
| 2.2.4 | Configure Alert Dispatch via GitHub Actions | C-04 | 16h | ⬜ |
| 2.2.5 | Test Alert System with Historical Shock Events | C-08 | 8h | ⬜ |

### 2.3 G2 Price Band Forecasting Model (~200h) `[M]`
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 2.3.1 | Implement VMD Signal Decomposition (trend/cycle/noise) | C-03 | 24h | ⬜ |
| 2.3.2 | Implement GARCH/EGARCH Volatility Model (arch / rugarch) | P2-05 | 32h | ⬜ |
| 2.3.3 | Implement LSTM/GRU Sequence Model | C-03 | 40h | ⬜ |
| 2.3.4 | Implement TFT Multi-Horizon Forecasting | C-03 | 40h | ⬜ |
| 2.3.5 | Implement CQR Prediction Interval Layer (mapie) | C-03 | 24h | ⬜ |
| 2.3.6 | Run FinBERT Sentiment Scoring on News Corpus | P2-04 | 24h | ⬜ |
| 2.3.7 | Validate G2 Model Against Baselines (walk-forward CV) | C-03 | 8h | ⬜ |
| 2.3.8 | Review G2 Model Code | C-05 | 8h | ⬜ |

### 2.4 G3 Regime Detection Model (~160h) `[M]`
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 2.4.1 | Implement SARIMAX with Macro Covariates (FX, BDI, ENSO) | P2-05 | 32h | ⬜ |
| 2.4.2 | Implement Markov Regime Switching Model (2–3 states) | P2-05 | 32h | ⬜ |
| 2.4.3 | Implement TFT Multi-Horizon Regime Probability | C-03 | 40h | ⬜ |
| 2.4.4 | Implement ENSO Phase Encoding and Geopolitical Dummies | P2-04 | 24h | ⬜ |
| 2.4.5 | Validate G3 Regime Labels Against Historical Market Events | P2-01 | 24h | ⬜ |
| 2.4.6 | Review G3 Model Code | C-05 | 8h | ⬜ |

### 2.5 Integrated Model Validation (~80h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 2.5.1 | Compile G1/G2/G3 Validation Report | C-07 | 16h | ⬜ |
| 2.5.2 | Register All Production Models in 클라우드 학습 환경 Registry | C-04 | 24h | ⬜ |
| 2.5.3 | Conduct Human Review of Model Outputs (HITL Gate) | C-01 → Human | 40h | ⬜ |

---

## Phase 3 — Optimization (~480h)
*목표: 구매 의사결정 지원 시스템, 안전 재고 모델, P&L 시뮬레이터 구축*

### 3.1 Procurement Optimizer (~120h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 3.1.1 | Define Procurement Optimization Constraints | P3-03 + P2-03 | 24h | ⬜ |
| 3.1.2 | Implement LP/MIP Procurement Optimizer (PuLP) | P3-05 | 40h | ⬜ |
| 3.1.3 | Implement Sensitivity Analysis on Forecast Error | P3-05 | 32h | ⬜ |
| 3.1.4 | Validate Optimizer Against Historical Procurement Records | P3-05 + C-08 | 24h | ⬜ |

### 3.2 Safety Stock Model (~80h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 3.2.1 | Implement Forecast-Linked Safety Stock Calculator | P3-05 | 32h | ⬜ |
| 3.2.2 | Integrate Safety Stock with S&OP Lead Time Data | P2-03 | 24h | ⬜ |
| 3.2.3 | Validate Safety Stock Model Against Inventory History | C-08 | 24h | ⬜ |

### 3.3 DSS Interface and HITL Workflow (~160h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 3.3.1 | Design DSS Output Schema (Regime + Confidence + P&L + Action) | P3-01 | 24h | ⬜ |
| 3.3.2 | Implement G3 Signal → Buy/Hold Recommendation Pipeline | P3-01 | 40h | ⬜ |
| 3.3.3 | Implement HITL Approval Workflow | C-04 + P3-01 | 32h | ⬜ |
| 3.3.4 | Implement Korean-Language DSS Report Generator | C-07 | 24h | ⬜ |
| 3.3.5 | Conduct HITL Gate Review of DSS Output | C-01 → Human | 40h | ⬜ |

### 3.4 Monte Carlo P&L Simulator (~120h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 3.4.1 | Define Scenario Parameters (Bear/Bull/Neutral inputs) | P3-04 + P2-01 | 24h | ⬜ |
| 3.4.2 | Implement Monte Carlo Simulator (10,000 runs, numpy/scipy) | P3-04 | 40h | ⬜ |
| 3.4.3 | Implement HIGH UNCERTAINTY Flag (variance > 20%) | P3-04 | 16h | ⬜ |
| 3.4.4 | Validate Simulator Against Historical P&L Records | P2-01 | 40h | ⬜ |

---

## Phase 4 — Productionize (~320h)
*목표: 자동화 스케줄링, 대시보드, ERP/S&OP 연동*

### 4.1 Automated Pipeline Scheduling (~80h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 4.1.1 | Implement Daily Data Refresh GitHub Actions Workflow | C-04 | 32h | ⬜ |
| 4.1.2 | Implement Model Re-training Schedule (클라우드 학습 환경 Pipeline) | C-04 | 32h | ⬜ |
| 4.1.3 | Test End-to-End Pipeline Reliability | C-08 | 16h | ⬜ |

### 4.2 Buy/Hold Dashboard (~120h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 4.2.1 | Design Dashboard Layout and KPI Selection | P3-06 + P3-01 | 24h | ⬜ |
| 4.2.2 | Implement Plotly Dashboard for G2 Price Band | C-03 | 32h | ⬜ |
| 4.2.3 | Implement G3 Regime Signal Panel | C-03 | 32h | ⬜ |
| 4.2.4 | Implement G1 Variable Importance Alert Panel | C-03 | 32h | ⬜ |

### 4.3 ERP/S&OP Integration (~120h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 4.3.1 | Design Shock Detection → MPS Impact Simulation Flow | P3-02 + P2-03 | 40h | ⬜ |
| 4.3.2 | Implement Real-Time Shock Alert to S&OP System | C-04 | 40h | ⬜ |
| 4.3.3 | Conduct Integration UAT with S&OP Team (HITL) | C-01 → Human | 40h | ⬜ |

---

## Phase 5 — Governance (~240h)
*목표: 모델 드리프트 모니터링, KPI 보고 체계, 최종 문서화*

### 5.1 Model Monitoring & Drift Detection (~80h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 5.1.1 | Implement Model Performance Monitoring Pipeline | C-03 + C-04 | 40h | ⬜ |
| 5.1.2 | Define Drift Detection Thresholds and Alert Rules | C-03 + P2-01 | 24h | ⬜ |
| 5.1.3 | Implement Automated Retraining Trigger | C-04 | 16h | ⬜ |

### 5.2 KPI Reporting Framework (~80h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 5.2.1 | Define Procurement KPI Metrics with Stakeholders (HITL) | P3-06 + C-01 → Human | 40h | ⬜ |
| 5.2.2 | Implement Automated Monthly KPI Report Generator | C-07 | 40h | ⬜ |

### 5.3 Documentation & Handover (~80h)
| WBS ID | 작업명 | 담당 | 공수 | 상태 |
|---|---|---|---|---|
| 5.3.1 | Compile Final Technical Documentation | C-07 | 40h | ⬜ |
| 5.3.2 | Produce Executive Project Summary Report | P3-06 | 24h | ⬜ |
| 5.3.3 | Conduct Final Project Review (HITL) | C-01 → Human | 16h | ⬜ |
