# Skills Index — Project Nexus
> Master routing map for all agent skills. Load this file to decide which agent to activate.
> Full skill definitions: `.claude/skills/<tier>/<agent>.md`
> Project context: `README.md §QR` · Operating rules: `CLAUDE.md`

---

## Agent Roster & Model Assignment

### Tier 0 — Common Agents (Active Across All Phases)

| # | Agent | File | Primary Model | Secondary LLM | Core Purpose |
|---|---|---|---|---|---|
| C-01 | Senior PM | `common/01_senior_pm.md` | Claude Opus 4.8 | — | Orchestration, WSJF prioritization, Korean status reports |
| C-02 | Market Research Specialist | `common/02_market_research.md` | Claude Opus 4.8 | Perplexity Pro | Real-time intelligence, NotebookLM hub |
| C-03 | Data Scientist | `common/03_data_scientist.md` | Claude Opus 4.8 (thinking) | — | G1/G2/G3 model execution, statistical analysis |
| C-04 | Document Intelligence & Infrastructure | `.claude/agents/c04-document-intelligence.md` | Claude Sonnet 5 | — | PDF/Excel ingestion (MinerU·opendataloader), local Docker pipelines (n8n), GitHub Actions |
| C-05 | Code Reviewer (QA/QC) | `common/05_code_reviewer.md` | Claude Haiku 4.5 | — | Style/security/correctness gating (fast, deterministic) |
| C-06 | EDA Agent | `common/06_eda_agent.md` | Claude Sonnet 5 | — (Gemini 배제, C-012) | Statistical profiling, anomaly flagging |
| C-07 | Documentation & Knowledge Manager | `common/07_documentation_agent.md` | Claude Haiku 4.5 | — | MEMORY.md, reports, stakeholder docs |
| C-08 | Data Quality Validator | `common/08_data_validator.md` | Claude Haiku 4.5 | — | DQSOps 5-dimension scoring, schema enforcement |

### Tier 1 — Phase 1: Foundation Agents

| # | Agent | File | Primary Model | Secondary LLM | Core Purpose |
|---|---|---|---|---|---|
| P1-01 | Commodity Analyst | `phase1/01_commodity_analyst.md` | Claude Opus 4.8 | Perplexity Pro | Price fundamentals, supply/demand balance |
| P1-02 | Geopolitical & Trade Risk Analyst | `phase1/02_geopolitical_analyst.md` | Claude Opus 4.8 | Perplexity Pro | Trade route risk, sanctions, conflict impact |
| P1-03 | Agrometeorologist / Climate Specialist | `phase1/03_climate_specialist.md` | Claude Sonnet 5 | Perplexity Pro | ENSO, crop yield, AA protocols, agromet bulletins |
| P1-04 | Supply Chain & Logistics Analyst | `phase1/04_supply_chain_analyst.md` | Claude Sonnet 5 | Perplexity Pro | BDI, CFR optimization, ABCD value chain, 3-month lead-time |
| P1-05 | News & Sentiment Analyst | `phase1/05_news_sentiment.md` | Claude Sonnet 5 | — | FinBERT sentiment scoring, GDELT, GAIN report analysis |

### Tier 2 — Phase 2: Modeling Agents

| # | Agent | File | Primary Model | Secondary LLM | Core Purpose |
|---|---|---|---|---|---|
| P2-01 | Commodity Financial Risk Manager | `phase2/01_risk_manager.md` | Claude Opus 4.8 | — | PaR, VaR, hedging P&L, capital exposure |
| P2-02 | FID / Pricing & Regime Analyst | `phase2/02_fid_pricing_analyst.md` | Claude Opus 4.8 | — | Real-time Bear/Bull regime, futures pricing |
| P2-03 | S&OP Integration Lead | `phase2/03_sop_lead.md` | Claude Sonnet 5 | — | MPS ↔ procurement alignment, demand signal |
| P2-04 | NLP / Sentiment Analyst | `phase2/04_nlp_sentiment.md` | Claude Sonnet 5 | — | FinBERT scoring, news corpus, geopolitical index |
| P2-05 | Statistical Time Series Modeler | `phase2/05_statistical_modeler.md` | Claude Sonnet 5 | — | ARIMA, GARCH, SARIMAX, Granger causality |

### Tier 3 — Phase 3: Optimization Agents (extends Phase 2)

| # | Agent | File | Primary Model | Secondary LLM | Core Purpose |
|---|---|---|---|---|---|
| P3-01 | DSS Analyst | `phase3/01_dss_analyst.md` | Claude Opus 4.8 | — | Decision synthesis, HITL interface, confidence scoring |
| P3-02 | 4PL Control Tower Manager | `phase3/02_control_tower.md` | Claude Sonnet 5 | — | End-to-end supply chain visibility, alert dispatch |
| P3-03 | Strategic Procurement Negotiator | `phase3/03_procurement_negotiator.md` | Claude Opus 4.8 | Perplexity Pro | Contract strategy, spot market leverage, BATNA |
| P3-04 | Scenario Planning Expert | `phase3/04_scenario_planner.md` | Claude Opus 4.8 | — | Monte Carlo, Bear/Bull/Neutral scenarios, stress tests |
| P3-05 | Procurement Optimizer | `phase3/05_procurement_optimizer.md` | Claude Sonnet 5 | — | LP/MIP, optimal buy quantity, multi-constraint solver |
| P3-06 | Executive Reporting Agent | `phase3/06_executive_reporter.md` | Claude Sonnet 5 | — | C-suite dashboards, KPI reports, Korean stakeholder briefs |

---

## Phase ↔ Goal Mapping

| Phase | Goals Served | Shared with Next Phase |
|---|---|---|
| Phase 1 | G1 (variable identification), data foundation | Risk scoring logic → Phase 2 |
| Phase 2 | G1 (alerts), G2 (price band), G3 (regime detection) | Model outputs → Phase 3 DSS input |
| Phase 3 | G3 (Buy/Hold signal), G2 (band → procurement range) | All model outputs consumed |

## Phase 2 → Phase 3 Inheritance Map
> Phase 3 agents extend Phase 2 agents; load the Phase 2 skill file first when noted.

| Phase 3 Agent | Extends / Consumes Output of |
|---|---|
| DSS Analyst (P3-01) | Risk Manager (P2-01) + FID Analyst (P2-02) + Scenario Planner (P3-04) |
| Scenario Planner (P3-04) | Statistical Modeler (P2-05) + Risk Manager (P2-01) |
| Procurement Optimizer (P3-05) | Risk Manager (P2-01) + S&OP Lead (P2-03) |
| Executive Reporter (P3-06) | All Phase 2 + Phase 3 outputs |

---

## NotebookLM Notebook Registry
> Each named notebook is maintained in Google NotebookLM. Agents reference notebooks by name.
> Upload frequency and responsible agent listed for each.

| Notebook Name | Domain | Responsible Agent | Upload Frequency |
|---|---|---|---|
| `NLM-01: Soybean Oil Market Intelligence` | Price, supply/demand | C-02 Market Research | Weekly |
| `NLM-02: Geopolitical Risk Monitor` | Trade routes, conflicts, sanctions | P1-02 Geopolitical Analyst | Daily |
| `NLM-03: Climate & Crop Outlook` | ENSO, WASDE, weather anomalies | P1-03 Climate Specialist | Monthly / event-driven |
| `NLM-04: Regulatory Environment` | EPA RFS, Korea RFS, tariffs, trade policy | C-02 Market Research | Monthly |
| `NLM-05: Supplier & Counterparty Intelligence` | Supplier profiles, offer benchmarks | P1-04 Supply Chain Analyst | Quarterly |
| `NLM-06: Project Documentation Archive` | All internal reports, decisions, MEMORY.md | C-07 Documentation Agent | After each session |

---

## LLM Routing Logic

```
Task Type                        → Best LLM
──────────────────────────────────────────────────────────
Strategic reasoning / orchestration → Claude Opus 4.8
Statistical modeling (thinking mode) → Claude Opus 4.8 (thinking)
Analysis (EDA, supply chain, climate) → Claude Sonnet 5
Code generation / pipelines         → Claude Sonnet 5
Style check / deterministic gate    → Claude Haiku 4.5-20251001
Real-time market research           → Perplexity Pro (sonar-pro)
Large document analysis              → Claude Sonnet 5 (Gemini 배제 — C-012; P1-05/06 secondary=gemini-3.1-pro는 C-010 예외)
PDF/Excel extraction                → C-04 (claude-sonnet-5)
```

---

## 외부 공개 도구 스킬 (승인자 지시 2026-09-28 — `.claude/rules/tooling.md`)

| 작업 유형 | 스킬 | 폴더 | 출처 |
|---|---|---|---|
| 코딩 | `ponytail` | `ponytail/` | DietrichGebert/ponytail (MIT) |
| 아키텍처·워크플로우 도식 | `drawio-skill` | `drawio-skill/` | Agents365-ai/drawio-skill (MIT) |
| 비정형 자료 작업의 코드 탐색 | `graft` | `graft/` (graft init 생성) | nanonets/Graft (MIT) |
