# Skills.md — Project Nexus
> This file is the **human-readable index** of all agent roles in the project.
> For full skill definitions, routing logic, and model assignments: → `.claude/skills/INDEX.md`
> For agent invocation patterns: each skill file in `.claude/skills/<tier>/` contains the full process.

---

## Why a Separate Folder per Phase?

Loading all agent definitions into a single context is a primary cause of **context rot** — the degradation of model reasoning as irrelevant rules compete for attention tokens. The folder structure below ensures:

- A Phase 1 data-ingestion session loads only Phase 1 + Common agent skills
- A Phase 3 procurement optimization session loads only Phase 3 + Common + relevant Phase 2 outputs
- Phase 3 agents explicitly reference which Phase 2 agents they extend (see INDEX.md inheritance map)

```
.claude/skills/
├── INDEX.md              ← Agent roster, model assignments, LLM routing, NotebookLM registry
├── common/               ← All phases — load whenever active
│   ├── 01_senior_pm.md
│   ├── 02_market_research.md
│   ├── 03_data_scientist.md
│   ├── 05_code_reviewer.md
│   ├── 06_eda_agent.md
│   ├── 07_documentation_agent.md
│   └── 08_data_validator.md
├── phase1/               ← Foundation: pipelines, variable identification, G1 setup
│   ├── 01_commodity_analyst.md
│   ├── 02_geopolitical_analyst.md
│   ├── 03_climate_specialist.md
│   ├── 04_supply_chain_analyst.md
│   └── 05_pipeline_architect.md
├── phase2/               ← Modeling: G1 alerts, G2 price band, G3 regime
│   ├── 01_risk_manager.md
│   ├── 02_fid_pricing_analyst.md
│   ├── 03_sop_lead.md
│   ├── 04_nlp_sentiment.md
│   └── 05_statistical_modeler.md
└── phase3/               ← Optimization: Buy/Hold signal, procurement execution support
    ├── 01_dss_analyst.md
    ├── 02_control_tower.md
    ├── 03_procurement_negotiator.md
    ├── 04_scenario_planner.md
    ├── 05_procurement_optimizer.md
    └── 06_executive_reporter.md
```

---

## Consolidated Role List (Revised)

> Revisions from original list: 6 added, 2 consolidated, 2 renamed for clarity. See justifications below.

### Common Agents (8 roles)

| ID | Role | Change from Original |
|---|---|---|
| C-01 | Senior PM | ✓ Unchanged |
| C-02 | Market Research & Intelligence Specialist | ✓ Unchanged; designated NotebookLM hub owner |
| C-03 | Data Scientist | ✓ Unchanged; G1/G2/G3 model execution |
| C-04 | Document Intelligence & MLOps | ↩ Renamed — scope clarified (document extraction + local pipeline operations) |
| C-05 | Code Reviewer (QA/QC) | ✓ Unchanged; two-pass model (Haiku → Sonnet) |
| C-06 | EDA Agent | ✓ Unchanged |
| C-07 | **Documentation & Knowledge Manager** | ➕ Added — MEMORY.md and NotebookLM archive ownership needs a dedicated agent |
| C-08 | **Data Quality Validator** | ➕ Added — great_expectations gate is distinct from EDA's exploratory role |

### Phase 1 Agents (5 roles)

| ID | Role | Change from Original |
|---|---|---|
| P1-01 | Commodity Analyst | ✓ Unchanged |
| P1-02 | Geopolitical & Trade Risk Analyst | ↩ Renamed — "Trade Risk" added to reflect tariff/sanction scope |
| P1-03 | Agrometeorologist / Climate Risk Specialist | ✓ Unchanged |
| P1-04 | Supply Chain & Logistics Analyst | ↩ Renamed — logistics scope made explicit |
| P1-05 | **Data Pipeline Architect** | ➕ Added — external API ingestion design is distinct from C-04 ML infrastructure |

### Phase 2 Agents (5 roles)

| ID | Role | Change from Original |
|---|---|---|
| P2-01 | Commodity Financial Risk Manager | ✓ Unchanged |
| P2-02 | FID / Pricing & Regime Analyst | ↩ Renamed — "Regime" added to clarify G3 Bear/Bull contribution |
| P2-03 | S&OP Integration Lead | ↩ Renamed — "Integration" clarifies cross-department bridging role |
| P2-04 | **NLP / Sentiment Analyst** | ➕ Added — FinBERT + news corpus work is a full standalone role, not a sub-task of Data Scientist |
| P2-05 | **Statistical Time Series Modeler** | ➕ Added — ARIMA/GARCH/SARIMAX specialization is distinct from general Data Scientist work |

### Phase 3 Agents (6 roles)

| ID | Role | Change from Original |
|---|---|---|
| P3-01 | DSS Analyst | ✓ Unchanged |
| P3-02 | 4PL Control Tower Manager | ✓ Unchanged; consumes Phase 2 Risk Manager + S&OP outputs |
| P3-03 | Strategic Procurement Negotiator / Buyer | ✓ Unchanged |
| P3-04 | Scenario Planning Expert | ✓ Unchanged; extends P2-05 Statistical Modeler |
| P3-05 | **Procurement Optimizer** | ➕ Added — LP/MIP quantity optimization is a dedicated technical role |
| P3-06 | **Executive Reporting Agent** | ➕ Added — C-suite and cross-department communication requires a dedicated translator |

---

## Google NotebookLM Integration Strategy

NotebookLM serves as the project's **persistent knowledge base layer** — a citable, searchable repository that agents draw from before generating outputs. This decouples long-term domain knowledge (market reports, policy documents, historical analyses) from the active agent context window.

### Why NotebookLM (not just Perplexity or RAG)?
| Capability | NotebookLM Advantage |
|---|---|
| Source citation | Every answer cites the exact uploaded document and page — critical for procurement audit trails |
| Audio summaries | Dense WASDE or EPA regulatory reports can be consumed as audio briefings |
| Persistent knowledge | Uploaded documents persist across sessions; Perplexity searches are ephemeral |
| Private documents | 외부 공개 보고서(WASDE·GAIN·EPA 등) 업로드용. ⛔ **내부 S&OP/조달 데이터는 분석 미사용**(MEMORY D-021) — 업로드·투입 금지 |

### Integration Workflow (Current — No Public API)
```
Step 1: Human uploads documents to named NotebookLM notebooks (see INDEX.md registry)
Step 2: Agent skill file specifies which notebook to query and what question to ask
Step 3: Human queries NotebookLM → pastes cited summary into agent context
Step 4: Agent processes NotebookLM output + current data → generates structured output
Step 5: C-07 Documentation Agent packages session outputs for NLM-06 archive upload
```

### When NotebookLM API Becomes Available
Replace Step 2–3 with a direct tool call in the agent's process block:
```python
# Future: direct NotebookLM API integration
notebooklm_response = call_notebooklm_api(
    notebook="NLM-01: Soybean Oil Market Intelligence",
    query=f"Latest supply/demand developments affecting soybean oil price, {current_date}"
)
```

### Named Notebooks (Maintained by C-02 + C-07)
| Notebook | Content | Primary Consumer |
|---|---|---|
| `NLM-01: Soybean Oil Market Intelligence` | Price reports, analyst research, CBOT data summaries | C-02, P1-01, P2-02 |
| `NLM-02: Geopolitical Risk Monitor` | News corpora, think tank briefs, conflict indices | P1-02, P2-01 |
| `NLM-03: Climate & Crop Outlook` | ENSO bulletins, WASDE reports, weather anomaly data | P1-03 |
| `NLM-04: Regulatory Environment` | EPA RFS, Korea RFS, tariff schedules, trade policy | C-02, P1-01 |
| `NLM-05: Supplier Intelligence` | Supplier profiles, offer price history, CFR benchmarks | P1-04, P3-03 |
| `NLM-06: Project Documentation Archive` | All reports, MEMORY.md snapshots, session summaries | C-01, C-07 |

---

## LLM & Claude Model Selection by Agent

### Rationale Framework
| Model | Use When | Avoid When |
|---|---|---|
| **Claude Opus 4.6** | High-stakes strategic reasoning, multi-variable synthesis, final G3 procurement signals | Routine code generation — cost-inefficient |
| **Claude Sonnet 4.6** | Code generation, standard analysis, report writing, pipeline design | Need real-time web data |
| **Claude Haiku 4.5** | Pattern matching, style checks, formatting, deterministic rule-following | Complex multi-step reasoning |
| **Perplexity Pro** | Real-time commodity prices, news, regulatory updates, web-sourced intelligence | Long-document synthesis |
| **Gemini AI Pro** | Documents > 50 pages, multi-modal (chart + data), 2M-token context tasks | Code generation |
| **ChatGPT Team** | Structured table extraction, quick arithmetic validation | Complex reasoning or code |

### Agent Model Matrix

| Agent | Routine | Escalate To | Trigger for Escalation |
|---|---|---|---|
| C-01 Senior PM | Sonnet 4.6 | — | Never needs Opus |
| C-02 Market Research | Perplexity Pro | Gemini AI Pro | Document > 50 pages |
| C-03 Data Scientist | Sonnet 4.6 | Opus 4.6 | G3 final synthesis; Monte Carlo variance > 20% |
| C-04 Document Intelligence | Sonnet 4.6 | — | Code generation doesn't benefit from Opus |
| C-05 Code Reviewer | Haiku 4.5 | Sonnet 4.6 | Security review; logic-level analysis |
| C-06 EDA Agent | Sonnet 4.6 | Gemini AI Pro | Dataset > 1M rows |
| C-07 Documentation | Haiku 4.5 | Sonnet 4.6 | Stakeholder-facing executive briefs |
| C-08 Data Validator | Haiku 4.5 | — | Deterministic rules; Haiku is sufficient |
| P1-01 Commodity Analyst | Opus 4.6 | — | High interpretive stakes from session start |
| P1-02 Geopolitical Analyst | Opus 4.6 | Perplexity Pro | Real-time conflict/sanction events |
| P1-03 Climate Specialist | Sonnet 4.6 | Perplexity Pro | ENSO phase change events |
| P1-04 Supply Chain Analyst | Sonnet 4.6 | Perplexity Pro | BDI spike events |
| P1-05 Pipeline Architect | Sonnet 4.6 | — | Code-heavy; Opus not needed |
| P2-01 Risk Manager | Opus 4.6 | — | High-stakes financial quantification |
| P2-02 FID Pricing Analyst | Opus 4.6 | — | Real-time regime detection is critical |
| P2-03 S&OP Lead | Sonnet 4.6 | — | Communication + integration role |
| P2-04 NLP Analyst | Sonnet 4.6 | — | Language tasks; Sonnet excels |
| P2-05 Statistical Modeler | Sonnet 4.6 | — | Technical; R code generation |
| P3-01 DSS Analyst | Opus 4.6 | — | Highest-stakes decision synthesis |
| P3-02 Control Tower | Sonnet 4.6 | — | Operational monitoring |
| P3-03 Procurement Negotiator | Opus 4.6 | Perplexity Pro | Strategic reasoning + market intel |
| P3-04 Scenario Planner | Opus 4.6 | — | Complex probabilistic reasoning |
| P3-05 Procurement Optimizer | Sonnet 4.6 | — | Deterministic LP/MIP; code-heavy |
| P3-06 Executive Reporter | Sonnet 4.6 | Opus 4.6 | CEO/Board-level presentations |
