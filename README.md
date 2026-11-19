# Project Nexus
## Imported Raw Material Supply Chain Intelligence Hub

> **North Star**: Maximize P&L by minimizing procurement risk from soybean oil supply chain volatility.
> **For AI agents**: Load §QR first, then load only the section(s) relevant to your task. Do not re-summarize this file.
> **Mutability notice**: Sections marked `[M]` contain data sources or methods subject to change without notice.

---

## §QR QUICK REFERENCE — Load This First

| Field | Value |
|---|---|
| **Target Commodity** | Soybean Oil (대두유) — crude and refined |
| **Import Origins** | USA · Argentina · Brazil · Vietnam |
| **Contract Basis** | CFR (Cost and Freight) — importer bears risk from origin port |
| **Typical Lead Time** | ~3 months (order → shipment → arrival) |
| **Decision Output** | Daily **Buy / Hold** procurement signal |
| **Signal Basis** | Bear (하락장) / Bull (상승장) regime + price band forecast |
| **Current Scope** | Soybean oil only — do NOT extend to other raw materials without explicit instruction |
| **Human Gate** | AI recommends; procurement team approves. No autonomous execution. |

### 프로젝트 차별점 (승인자 상시 원칙 — 2026-09-27)
> **대상 원료(대두유)의 시장·유통 구조를 공급·가격 예측에 통합한다.** G1의 목표는 실제 운영에서 **놓치기 쉬운 세부 요인·변수까지
> 찾아내 분석하고 정량 지표로 제시**하는 것이다. 따라서 G1 산출물은 ① 흔한 거시 동인(유가·환율)의 반복이 아니라 구조 요인
> (원산지 채널·압착 채산성·가공사 증설·정책 일정·물류 경로·경쟁 유지 수급)을 드러내야 하고, ② 같은 경로를 재는 변수는 묶어
> 한 번만 세며, ③ 각 변동·변인에는 정량 수치(분해 몫·편차·시차)와 날짜가 확인된 근거를 붙인다.

### Goal Labels (used throughout all project files)
> 2026-08-28 조정자 최종 재정립 반영 — 과거 연도 데이터의 하이브리드 분석(정량+정성)
> 위에서 단계별 목표를 구축하는 구매 의사결정 지원 솔루션.

| ID | Goal | Primary Output |
|---|---|---|
| **G1** | 가격 동인 변수 식별·순위 + **과거 유사국면 실측 참조** | 변수 중요도·자동 경보 + 특정 변수가 현재와 유사했던 과거 연도들의 이후 1주/1개월/3개월 **수급·가격 실측 분포**(예측 주장 아님 — A-191) → 주의 변수 통지 |
| **G2** | 퀀트 로직 기반 확률 가격밴드 | 1·5·20·60거래일(≈1일·1주·1개월·3개월) 확률 가격밴드 (P10/P50/P90 + 상승확률) |
| **G3** | 구매 시점·물량 **3-시뮬레이션** | ①현시점 구매 ②사전 그리드 대안 시점 ③분할 구매 — 각각 시장가 기준 근사 손익(**per-MT regret** · D-021: 회사 P&L 아님·물량은 런타임 입력) + 레짐 확률 |

---

## §1 Problem Statement

An F&B manufacturer importing soybean oil faces three structural procurement failures:

| Failure | Current State | Target State |
|---|---|---|
| **Volatility management** | Reactive — follows lagging news and free indices | Proactive — real-time structural break detection |
| **Decision basis** | Buyer intuition + subjective judgment | Quantitative models + objective data signals |
| **Lead-time risk** | Discovered post-facto | Anticipated 3 months ahead via predictive pipeline |

**Why the US and Argentina dominate**: Together they produce ~80% of global soybeans. Local policy shifts and crop conditions in these two origins directly set CFR import prices. Vietnam is included as a secondary origin for refined oil.

**Current trigger**: US–Iran conflict (Hormuz Strait) causing persistent disruption to global logistics — a real-time test case for this system.

---

## §2 Analytical Goals

> Goal IDs G1/G2/G3 are used as shorthand throughout CLAUDE.md, Skills.md, and all code modules. Always resolve ambiguous references against §QR.

### G1 — Variable Importance & Risk Alerts + 과거 유사국면 참조
Identify which macro/micro factors most influence soybean oil prices and build automated alert triggers when those factors breach thresholds.
**차별점(2026-09-27 승인자 상시 원칙)**: 시장·유통 구조(원산지 채널·압착·가공사·정책·물류·경쟁 유지)를 변수화해
실무에서 놓치기 쉬운 요인까지 정량 지표로 제시한다 — 위 §QR '프로젝트 차별점' 참조.
**유사국면 참조(2026-08-28 재정립)**: 실무자는 모든 변수를 상시 주시할 수 없으므로,
특정 변수의 상태가 현재와 유사했던 과거 연도들에서 이후 수급·가격이 어떻게 변했는지를
실측 분포로 제공해 참조하게 한다 — 과거 관측의 요약이며 전망 주장이 아니다(A-191).

### G2 — Price Band Forecasting `[M]`
1·5·20·60 거래일 지평의 **확률 가격밴드**를 산출한다. 출력은 점추정이 아니라
P10/P25/P50/P75/P90 · 50/80/95% 구간 · 상승확률 · 임계가격 초과확률이며,
구간의 실측 coverage를 레짐별로 함께 보고한다.

### G3 — Bear/Bull/Hold Regime Signal + 3-시뮬레이션 `[M]`
시장을 Bear/Neutral/Bull로 분류하되 **하드 라벨이 아닌 레짐 확률**로 출력하고,
G2 예측분포와 결합해 Buy/Hold를 제안한다.
**3-시뮬레이션(2026-08-28 재정립)**: 실무자의 "내 구매 시점·물량이 적절한가" 질문에
①현시점 구매 ②사전 고정 그리드 대안 시점(n주 전/후) ③분할 구매 — 3가지 시나리오의
근사 손익 분포(per-MT regret)로 답한다. G2 분위수 모델 가동 전에는 과거 실측 백테스트
서술까지만 제공한다(A-191).
> **D-021 경계**: 내부 구매량·재고·마진이 없으므로 실제 회사 P&L 최적화를 주장하지 않는다.
> 공개 시장가 기준 **market-cost proxy와 regret**로 대체한다.

---

## §3 Data Requirements `[M]`

> The variable lists below are the current best-estimate pool. Additions and removals are expected as the project progresses. Treat them as a starting set, not a fixed schema.

### 3.1 External Data

| Category | Variables |
|---|---|
| **Global Economy / Trade** | Fed funds rate, global CPI, KRW/USD FX rate, WTI/Brent crude oil price, BDI (Baltic Dry Index), SCFI (Shanghai Containerized Freight Index) |
| **Geopolitical / Policy** | US–China trade tensions, Trump-era tariff schedules, Hormuz Strait / Black Sea conflict intensity indicators |
| **Climate / Agriculture** | ENSO index (El Niño / La Niña phase), USDA WASDE crop yield data, origin-country weather anomalies (US, Argentina, Brazil, Vietnam), EPA Renewable Fuel Standard (RFS) |
| **Domestic Korea** | BOK base rate, domestic CPI, total soybean oil import volumes, substitute oil prices (palm oil, sunflower oil), domestic RFS biodiesel blend mandate (2030 target: 5%), government grain strategic reserve policy |

### 3.2 Internal Data — ⛔ EXCLUDED (MEMORY D-021)

> **결정 D-021 (2026-07)**: 내부 S&OP/ERP 데이터는 **가용량 부족 + 더미 비중 과다**로
> **분석에 일절 사용하지 않는다**. 아래 표는 *참고용 도메인 목록*일 뿐이며, G1/G2/G3의 학습·검증·
> 피처 어디에도 투입되지 않는다. 모든 모델링은 **외부 파이프라인 데이터 전용**(구 "Phase B 내부검증"
> 설계는 폐기). 상세: `.claude/rules/modeling.md`.

| Domain | Key Data Points (참고용 — 미사용) |
|---|---|
| **S&OP** | Soybean oil input per SKU (kg/unit), Master Production Schedule (MPS), forecast vs. actual MAPE, seasonality coefficients, portfolio demand forecast (planned vs. executed) |
| **Procurement** | Order history (qty · contract unit price · order date · ETA), crude vs. refined import ratio and price delta, CFR freight change history, lead-time variance (contracted vs. actual), hedging P&L vs. market spot price at receipt, supplier offer price vs. market benchmark |
| **Supply / Logistics** | Monthly inventory levels (crude / refined), inventory turnover (monthly consumption basis), inbound lead-time actuals (order → shipment → arrival by stage) |

---

## §4 Analytical Methodology `[M]`

> All method selections are preliminary and subject to change. Do NOT treat a listed method as a committed implementation until it appears in the corresponding `src/` module.

### 4.1 Methods by Goal

> 2026-08-12 개정 — 근거: `docs/research_desk/2026-08/model_strategy_2026_08_12/`.
> 단일 모델을 미리 확정하지 않고 **Champion–Challenger**로 운영한다.

| Goal | Champion (현행) | Challenger (게이트 통과 후 비교) | 정성 계층 |
|---|---|---|---|
| **G1** | Elastic Net + LightGBM/XGBoost + SHAP·Permutation + Granger·국소투영 | — | P1-05 ABSA 사건 신호(evidence 필수) |
| **G2** | SARIMAX + Quantile LightGBM + EGARCH-X → **EnCQR** 구간 보정 | GRU/LSTM · N-BEATSx/N-HiTS · TFT · PatchTST · Chronos | 사건 더미(중복 병합·vintage 보존) |
| **G3** | Markov Switching/HMM 레짐 확률 + G2 분포 결합 | — | 시나리오 분석 · HITL 게이트 |

**예측 지평**: 1 · 5 · 20 · 60 거래일 **직접 예측**(재귀는 보조 실험).
**Baseline 필수**: last value · seasonal naive · ETS — 이를 못 이기면 승격 없음.

### 4.2 Methodology Taxonomy

```
Analysis Framework
├── A. Quantitative                              ← Automate first (pipeline-native)
│   ├── A-1. Statistical time series   SARIMAX · Markov RS · EGARCH-X
│   ├── A-2. Machine learning          Elastic Net · LightGBM/XGBoost · Quantile GBM
│   ├── A-3. Deep learning (challenger) N-BEATSx/N-HiTS · GRU/LSTM · TFT · PatchTST
│   └── A-4. Uncertainty quantification EnCQR · GARCH · Monte Carlo
└── B. Qualitative                               ← Phased automation; manual override retained
    ├── B-1. NLP / text analysis       ABSA(P1-05) · FinBERT · LDA
    ├── B-2. Event encoding            Geopolitical dummies · ENSO phase
    └── B-3. Expert judgment layer     Human-in-the-Loop · scenario definition
```

> ⚠️ **VMD/EMD 제외**(2026-08-12): 전체 시계열 일괄 분해는 미래 정보를 과거 fold로 유입시킨다.

### 4.3 시점 정합성(as-of) — 모든 모델 공통 하드 제약

```text
모델의 t일 입력값 = available_at ≤ t 를 만족하는 가장 최근 값
```

모든 피처에 `event_time` · `release_time` · `available_at` · `source_vintage`를 둔다.
WASDE·PSD 등 월·연간 자료는 **기간 말이 아니라 실제 발표일 이후에만** 모델이 볼 수 있다.
개정치는 덮어쓰지 않고 vintage별로 적재한다. 상세: `.claude/rules/modeling.md`.

---

## §5 Expected Outcomes

### Quantitative / Financial
| Outcome | Mechanism |
|---|---|
| Raw material cost reduction | Data-driven buy timing replaces intuition-based purchasing |
| KPI achievement | Proactive buy success rate + target cost reduction rate (targets TBD with stakeholders) |
| Safety stock cost reduction | Forecast-linked hybrid inventory model prevents excess stockpiling |
| Cash flow risk reduction | Scenario-based positioning buffers against price extremes |

### Operational
| Outcome | Mechanism |
|---|---|
| Reactive → Proactive paradigm | Structural break detection replaces lagging news-following |
| Decision transparency | Shared quantitative signals align S&OP, Procurement, Finance |
| Lead-time preparedness | 3-month horizon risk anticipation including Hormuz / logistics shock scenarios |

### Integration Targets
- **Dashboard**: Daily Buy/Hold signal + key price drivers → leverage in spot contract negotiations
- **ERP/S&OP linkage**: External shock detection → real-time simulation of impact on MPS and material requirements → enterprise-wide control tower function

---

## §6 Domain Glossary

> All AI agents operating in this project must resolve domain terms against this table before generating output. Do NOT infer meanings from general knowledge when a project-specific definition exists here.

| Term | Definition in This Project |
|---|---|
| **Bear (하락장)** | Market regime where soybean oil price is in sustained decline; triggers **Hold** signal |
| **Bull (상승장)** | Market regime where soybean oil price is in sustained rise; triggers **Buy** signal |
| **Hold** | Procurement posture: delay purchasing and wait for a better price entry point |
| **Buy** | Procurement posture: execute purchase now at current market price |
| **CFR** | Cost and Freight — supplier covers cost + shipping to destination port; importer bears risk from origin port onward |
| **S&OP** | Sales & Operations Planning — cross-functional process aligning production, sales, and supply |
| **MPS** | Master Production Schedule — month-level production plan per SKU |
| **MES** | Manufacturing Execution System — real-time production tracking system |
| **Lead Time** | ~3 months from purchase order to warehouse arrival (order → shipment → customs → arrival) |
| **Safety Stock** | Minimum buffer inventory held to cover demand spikes or supply delays |
| **BDI** | Baltic Dry Index — global bulk shipping cost indicator; proxy for logistics cost |
| **SCFI** | Shanghai Containerized Freight Index — container shipping cost indicator |
| **ENSO** | El Niño–Southern Oscillation — climate pattern; La Niña phase historically reduces South American soy yields |
| **RFS** | Renewable Fuel Standard — US EPA policy mandating biofuel blend ratios; increases soybean oil demand |
| **WASDE** | World Agricultural Supply and Demand Estimates — USDA monthly global crop report |
| **PaR** | Price-at-Risk — VaR equivalent for commodity price exposure |
| **VMD** | Variational Mode Decomposition — 비정상 시계열 분해법. **2026-08-12 기본 구성 제외**(전체 일괄 분해 시 미래 정보 누수) |
| **CQR** | Conformal Quantile Regression — distribution-free prediction interval method |
| **TFT** | Temporal Fusion Transformer — attention-based multi-horizon time series model |
| **FinBERT** | BERT variant fine-tuned on financial text; used for news/report sentiment scoring |
| **Structural Break** | Sudden, permanent shift in a time series' statistical properties (e.g., post-sanction price regime change) |

---

## §7 Scope Boundaries

| In Scope | Out of Scope |
|---|---|
| Soybean oil (대두유) — crude and refined | Other raw materials (future project extension) |
| Import origins: US, Argentina, Brazil, Vietnam | Domestic Korean sourcing |
| CFR contract-based procurement decisions | Futures/derivatives trading execution |
| AI-generated Buy/Hold recommendations | Autonomous procurement decisions (human approval required) |
| Local pipeline (Docker + n8n, parquet + DuckDB; optional Oracle Cloud Free Tier host) | Enterprise data platforms or internal company systems |

---

## §8 Documentation Architecture

> This repository uses a **layered documentation hierarchy** so that AI agents load only the context relevant to their current task — preventing context rot and minimising token cost.

### 8.1 File Responsibilities

| File | Location | Loaded By | Purpose |
|---|---|---|---|
| [`README.md`](./README.md) | Root | Humans + agents (discovery) | Project mission, data inventory, goals, glossary, scope. The entry point. |
| [`CLAUDE.md`](./CLAUDE.md) | Root | Claude Code (every session) | Persistent agent operating rules: session protocol, hard constraints, code style, WISC/HITL. **≤ 120 lines.** |
| [`AGENTS.md`](./AGENTS.md) | Root | All coding assistants | Tool-agnostic instructions valid for any AI assistant (Copilot, Gemini, etc.). |
| [`Skills.md`](./Skills.md) | Root | On-demand (`/skill-name`) | Sub-agent definitions: PM, Data Engineer, Forecasting, Risk Analyst, Optimizer, Reporting, Code Reviewer. |
| [`llms.txt`](./llms.txt) | Root | External LLM ingestion | Structured URL manifest for semantic discovery by external agents. |
| [`G1/G2 Preview Release Gates`](./docs/operations/g1_g2_preview_release_gates.md) | `docs/operations/` | Operators + reviewers | Canonical target, fail-closed CI, 로컬 스냅샷 매니페스트, Preview 완료 기준. |

### 8.2 Path-Scoped Rules

Detailed, module-specific rules live in `.claude/rules/` and are loaded **only when the agent is working in the corresponding directory**. This keeps `CLAUDE.md` concise while ensuring full context is available when needed.

| Rule File | Loaded When Working In | Contents |
|---|---|---|
| `.claude/rules/modeling.md` | `src/forecasting/`, `notebooks/` | G1/G2/G3 method details, model validation protocol, baseline comparison rules |
| `.claude/rules/libraries.md` | Any `src/` or `notebooks/` | Full approved library list with version pins (Python + R) |
| `.claude/rules/data_pipeline.md` | `src/pipeline/` | DuckDB/parquet patterns, API retry logic, schema conventions |
| `.claude/rules/testing.md` | Any test file | pytest, great_expectations, time-aware split rules |

### 8.3 Memory Files

| File | Purpose |
|---|---|
| [`MEMORY.md`](./MEMORY.md) | Agent auto-memory: append learnings and resolved blockers after each session |
| Git log | Long-term decision history — run `git log --oneline -20` to reconstruct prior context |
