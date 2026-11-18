# Market Structure & Price-Driver PDF Review (2026-11-17)

> Source folder: `data/raw/Market Structure (Production & Distribution)/PDF` (24 PDFs, untracked in git).
> Method: text extracted with pdfplumber (≤45 pages each), reviewed by three expert-lens panels using the repo's
> agent definitions. Nothing in the ontology, README or pipeline was changed — every item below is a **candidate**
> awaiting the owner's approval (and semantic-layer validation for ontology edges).
>
> Duplicates: *Competition in the Global Agricultural Value Chain* is byte-identical to
> `docs/research_desk/references/review_ABCD_competitiveness_oilseed_trading.pdf` (skipped).
> *China's financialized soybeans* is the same paper/version as `China_2023_financialized_soybeans_food_regime.pdf`
> (only the publisher's download stamp differs) — no new content; its summary skeleton can be filled from Part B §2.

## Synthesis — what Nexus actually needs (merged across panels)

| # | Item | Goal | Why it's needed | Source / cost | Evidence |
|---|---|---|---|---|---|
| 1 | Board crush & oil share from ZL/ZM/ZS (lagged, roll-safe) | G1, G2 | Meal is the one blocking data gap; crush composition shifted structurally after 2020 | yfinance now; Databento ZM/ZS already approved (not yet ingested) | Fousekis & Grigoriadis 2025 |
| 2 | Regime-aware SBO−palm spread (CE-015): quantile-dependent palm features, ≤20-day horizon, 175 threshold as context | G1, G2 | Palm and SBO fall together but rise separately (bull–bull coherency 0.15–0.17) — mean-reversion assumption is unsafe | data already held | Fousekis 2024 Table 1 p.6 |
| 3 | Origin crude-quality prior (BR vs US: FFA 1.32 vs 0.44%, P 220 vs 117 ppm, refining loss 1.50 vs 1.01%) → quality-adjusted origin spread | G2 landed cost, G3 spec | Part of the unexplained origin CIF gap is a quality/refining-cost gap | free (paper); validate vs customs CIF | Flores et al. JAOCS 2026 Table 3 p.4 (USSEC-funded — cite with caution) |
| 4 | Korea SBO import origin shares, HHI & dependency index | G1, G3 | Concentration risk of the buyer's own supply; data already collected | Korea Customs (held) | RCA / network papers |
| 5 | Policy step series with dates: Brazil biodiesel blend (B2→B15), Argentine export-tax rates, US RVO/45Z, China tariffs | G1 analogue, G2 breaks | Elasticities change by policy regime (SBO–crude 0.29→0.96→0.18); events = analogue windows | free (ANP/CNPE, Boletín Oficial, GAIN) | Biodiesel-crude 2022 p.11; Alves 2022 p.17; Haro Sly p.7 |
| 6 | Split CE-011 (US–China tariff) into US-ZL node vs importer/Argentine node | G1 semantics | Tariff removal raises US SBO (+5.49%) but lowers it in most importers — one edge gives the wrong sign | model results | China tariff/MFP 2022 p.7 |
| 7 | Brazil SBO exports by destination + domestic absorption (58→82%) | G1, G2 | Brazil's exportable surplus is shrinking — CE-023 needs numbers, not news | ComexStat (free, needs egress) | Alves p.8; RCA p.13 |
| 8 | Energy effects by regime (WTI/Brent/heating oil × policy regime) | G1 | Pooled energy importance is unstable | data held | Biodiesel-crude 2022 |
| 9 | Stress slices / analogue windows: 2008 AR tax conflict, 2018 US–China, 2018 BR trucker strike, 2020–21, Q2–Q3 2022 | G1, G2 | Coverage must be reported by regime; analogue reference needs dated episodes | derived | several |
| 10 | ZL term structure + futures-implied benchmark row; WASDE SBO price projection as free expectation proxy; COT managed-money z-score | G2 | Benchmarks the band against what the market already prices | Databento deferred months = new metered cost (estimate first); WASDE/COT free | Risk-premium 2025 |

**Do not use:** numeric decomposition shares in *Determinants of international trade in Brazilian soybeans*
(±700,000%+ — broken); numbers from the IntechOpen *Edible Oilseeds* chapter (self-contradictory); network
centrality as a model feature (descriptor only — persistence beats graph models in this domain).

**Needs owner approval / cost:** Databento ZL deferred months (metered), new free connectors needing egress/
licence checks (ComexStat, ANP/CNPE, CEPEA, Boletín Oficial), UN Comtrade subscription for multi-country scale,
every ontology/README change. Paid and not recommended now: Bloomberg forecasts, Kpler/Vortexa, Platts basis.

---
Full panel reports follow: Part A (price drivers), Part B (trade & networks), Part C (supply chain & technology).



---

# Project Nexus: Review of 8 "price driver" papers

Two lenses are applied throughout:
- **Commodity analyst lens (P1-01)**: domain meaning of the drivers and alert thresholds.
- **Quant data scientist lens (C-03)**: as-of availability, leakage, walk-forward validity, and whether a result changes the Champion stack (SARIMAX + Quantile LightGBM + EGARCH-X + EnCQR).

Prepared 2026-11-17 from the extracted `.txt` files only. No repo file was modified.

**Page locators**: "p.N" is the PDF page in the extracted text (the `--- page N ---` markers). Where the journal prints its own page number, it is added as "[j.NNN]". If a number could not be read cleanly from the extraction, the report says so. Repo cross-references are given as file path plus section, line, or MEMORY ID.

**Snapshot of repo state used for overlap checks** (read-only):
- `docs/research_desk/2026-08/data_requirements_by_phase_2026_08_29.md`
- `.claude/rules/modeling.md` (Data Sources table)
- `docs/research_desk/references/README.md`
- `src/semantic/ontology.yaml` (CE-003, CE-011, CE-015, CE-020, CE-022)
- `docs/research_desk/2026-11/g2_preview_plan_2026_11_16.md` (COT implemented on 11/16; ZM/ZS still a DATA GAP)
- `src/pipeline/connectors/cot_connector.py`
- `src/pipeline/asof.py` (TE_BRENT_/TE_WTI_/TE_HEATING_ have lag_days=1)
- `scripts/ingest_wasde_xlsx.py`

**None of the 8 papers is already listed** in `docs/research_desk/references/README.md`. Thematic overlaps are noted per paper below.

---

## Paper 1. Asymmetric Price Transmission Analysis of the International Soybean Market

**1. Citation.** Barboza Martignone, G.M., Paparas, D., Behrendt, K. *Agricultural Sciences* 14, 317–334 (2023), doi 10.4236/as.2023.143020.
- Data: Sep 2009 – May 2019 (p.1 [j.317]).
- Prices: CBOT soybean futures, Rotterdam, Paranaguá spot, Rosario spot and futures, China spot, Dalian futures (p.1; sources on p.3–4).
- Frequency is not stated explicitly. It is likely monthly: CBOT/Rotterdam come from the IMF, and the Phillips–Perron 1% critical value of −3.485 (p.8 Table 2) implies roughly 120 observations. This is an **inference**.
- The product is **soybeans, not soybean oil**.

**2. Core findings.**
- All series are I(1) by Phillips–Perron (p.8 Table 2).
- Pairwise Engle–Granger cointegration is incomplete. China Spot cointegrates only with Dalian and Rosario Spot. Rosario Futures cointegrates only with Rosario Spot, Dalian and Paranaguá (p.10 Table 6).
- BDS test: nonlinear dependence in most series. Rotterdam and Dalian are the exceptions (p.10–11 Table 7).
- TAR and MTAR models: **no asymmetric price transmission** in any market, including the government-intervened ones (China, Argentina). F-equal is below the critical value everywhere (p.12–15, Tables 8–13).
- Conclusion: intervention produces **structural breaks and a temporary loss or fading of cointegration, not asymmetry** (p.17 [j.333]).
- Price levels (p.7 Table 1):
  - Free markets average about 415–461 USD/t.
  - China (spot and Dalian) averages about 630 USD/t.
  - Rosario averages about 282–288 USD/t.
  - Column alignment in the extracted table is ambiguous, so which of 415/438/461 belongs to which free market is uncertain.

**3. What Nexus needs from it.**
- (a) Model AR export-tax changes and China tariff/floor-price events as **dated structural-break / regime dummies**, not as asymmetric (positive/negative split) error-correction terms.
- (b) For soybean oil, the analogous horizontal spreads are:
  - Argentina SBO FOB (Up River) minus CBOT ZL
  - Brazil Paranaguá SBO FOB minus ZL
  - Possible free sources, both **unverified**: Argentina MAGyP "precios FOB oficiales"; Bolsa de Comercio de Rosario.
  - USDA FAS *Oilseeds: World Markets and Trade* (already used, per references README) publishes monthly vegetable-oil prices.
- (c) Use the paper's "loss of cointegration after intervention" as an **alert semantic**: after a policy shock, origin basis risk widens.

**4. Rationale.**
- **G1**: improves the driver story for the origin channels (CE-003 Argentine export tax, CE-011 US–China tariff).
- **G3**: improves how the US vs AR purchase-origin alternatives are explained.
- Without it, the team might fit asymmetric ECMs on monthly origin spreads that have no empirical support. That overfits and makes the drivers unstable across folds.

**5. Priority / class.** **Background**; **Counter-example** to the prior that intervened origins transmit asymmetrically.

**6. Caveats.**
- Soybeans, not SBO.
- Pre-2019 sample: excludes the RD boom, the 2022 war and 2026.
- Engle–Granger has low power (the authors concede this, p.15–16).
- The breaks are full-sample Bai–Perron dates taken from a prior study. Using them as features would be look-ahead. Only ex-ante policy dates are safe.
- Monthly, about 120 observations (inferred).

**7. Repo overlap.**
- Same author group as `Heliyon_2024_soybean_quantile_VAR_connectedness.pdf` (references README).
- CE-003 and CE-011 in `src/semantic/ontology.yaml`.
- Stress slice "2018 US–China" in `.claude/agents/c03-data-scientist.md` §4.

**Lens discussion.**
- **P1-01**: Argentina is the largest SBO exporter (36% of 2021 export value, per Paper 4, p.5). Its retentions and FX controls matter more for SBO than for beans, so the null result on beans should not be read as "AR policy is irrelevant". Read it as "AR policy acts through breaks and decoupling, not asymmetry".
- **C-03**: Agreed. There is also no reason to add threshold/asymmetric terms in G2. Break dummies must be keyed to `release_time`/`available_at` of the decree, not to statistically detected break dates.
- **Joint conclusion**: Do not adopt TAR/MTAR. Adopt the interpretation (intervention leads to decoupling) and put dated policy events into the policy calendar.

---

## Paper 2. Biodiesel feedstock and crude oil price relationships: the effects of policy and shale oil expansion

**1. Citation.** Schaefer, K.A., Myers, R.J., Johnson, S.R., Helmar, M.D., Radich, T. *Agricultural and Resource Economics Review* 51, 222–239 (2022), doi 10.1017/age.2022.6.
- Monthly, Jan 2000 – Dec 2020 (p.6 [j.227]).
- EU models start Oct 2001 (p.8 [j.229]); EU N = 219 (p.17 Table A2).
- Extraction issue: p.6 says the sample "purposefully ends prior to the onset of COVID-19" but also states the range runs to Dec 2020. This inconsistency should be checked against the PDF.

**2. Core findings.**
- US partial long-run elasticities to WTI (p.16 Table A1; text p.10 [j.231]):
  - Baseline: soy oil 8.34, canola 6.97, corn oil 12.63.
  - The Energy Policy Act (Aug 2005) adds +1.32 for soy.
  - EISA (Dec 2007) adds +0.11, not significant.
- Shale shifter: a 1% increase in annual global crude production lowers the soy-oil response by about 0.2% (p.11 [j.232]; coefficient −0.002, p.16).
- **Total soy-oil/crude elasticity** (p.11 [j.232]):
  - About 0.29 in the early 2000s
  - About 0.96 after EPAct
  - About 0.18 by Jan 2015
- EU (p.12 [j.233]; p.17 Table A2):
  - Soy-oil elasticity to Brent fell from about 0.67 pre-2005 to 0.07 after the ILUC Directive (Oct 2015).
  - ILUC shift for soy: −0.47.
- Residual-based cointegration holds for all series (p.12 Table 2; US soy ADF −4.35).
- Results are robust to ±6-month shifts in policy timing (p.13 [j.234]).
- Feedstock shares:
  - US: soy 55%, corn oil 12%, canola 10% (p.4 [j.225]).
  - EU: canola 47%, palm 15%, soy 7% (p.3 [j.224]).

**3. What Nexus needs from it.**
- (a) Treat the energy→SBO link as **regime-dependent**: estimate rolling or regime-interacted coefficients rather than one constant.
- (b) Series:
  - WTI: FRED `DCOILWTICO` (EIA)
  - Brent: FRED `DCOILBRENTEU`
  - NY Harbor heating oil / ULSD: FRED `DHOILNYH`; verify the ULSD code. Repo note: `sbo_move_attribution_2026_09_27.md` §"핵심 변인 해석 규칙" already uses heating oil as the single energy representative.
  - Global crude production: EIA International Energy Statistics (free API), as a slow shifter.
- (c) **Dated policy dummies** with as-of = publication date: RFS milestones, the 2026-03-27 final RVO rule, 45Z, and half-RIN deferred to 2028 (per references README).
- (d) Method idea: a cointegrating regression with policy-interacted slopes plus a smooth shifter (Enders–Holt). Use it as a G1 robustness check next to local projections. For G2, feed `crude_return × policy_regime` interactions to Quantile LightGBM.

**4. Rationale.**
- **G1**: ranks energy correctly *conditional on regime*. A constant-coefficient ranking would over-weight energy in 2005–2014 and under-weight it in 2015–2020.
- **G2**: interaction features stabilise the quantile model across regimes.
- Without this, a full-sample Elastic Net/SHAP gives an averaged coefficient that is wrong in every regime. That breaks the sign/rank stability gate in `.claude/agents/c03-data-scientist.md` §4.

**5. Priority / class.** **Should**. **Adopt** (regime-interaction idea and policy dummies); **Cite-with-caution** for the numbers.

**6. Caveats.**
- Ends in 2020, **before the 2021+ renewable-diesel boom**. The repo already notes that coupling re-strengthened around 2020 (`domain_mechanisms_sbo_2026_08_13.md` l.36; CE-020 lag_basis "oil share 30%→40%+"). The paper's "shale offsets biofuel policy" result should **not** be extrapolated to now.
- Uses Decatur cash SBO, not ZL futures; monthly.
- **Leakage**: the annual crude-production shifter is matched to months "by calendar year based on contemporaneous monthly production" (p.8). In forecasting this is look-ahead; it must be lagged to the EIA release date.
- The partial elasticities (8.34 etc.) are not meaningful alone, because the shifter offsets them. Only the total elasticities should be quoted.

**7. Repo overlap.**
- CE-020 (validated) in `ontology.yaml`.
- `asof.py` energy lag rules (TE_BRENT_/TE_WTI_/TE_HEATING_ lag_days=1, M-014).
- farmdoc RFS Playbook series in references README.
- `sbo_move_attribution_2026_09_27.md`.

**Lens discussion.**
- **P1-01**: Energy via diesel/heating oil is one of the top SBO drivers in the RD era (July–Aug 2026 moves were attributed to diesel per `sbo_move_attribution_2026_09_27.md`). The paper's main value is showing that **policy regime changes the strength of the link**, which supports CE-020.
- **C-03**: The 0.29 → 0.96 → 0.18 path shows a coefficient that is not stable. Energy must not be promoted as a "core driver" from a pooled ranking. Before promotion require:
  - per-regime coefficients
  - fold-wise sign stability
  - a local-projection check
  - Also keep the sample-period caveat visible.
- **Joint conclusion**: Adopt regime-interacted energy features and dated policy dummies. Do not quote the 2015 "decoupling" as current.

---

## Paper 3. Consequences of Chinese tariff and US MFP payments on world soybean-complex markets

**1. Citation.** Baryshpolets, A., Devadoss, S., Sabala, E. *Journal of the Agricultural and Applied Economics Association* 1, 108–119 (2022), doi 10.1002/jaa2.12.
- Spatial-equilibrium (mixed complementarity) simulation of the bean/oil/meal complex.
- The calibration baseline year is **not stated in the main text** (it is in the Supporting Information appendix). It "assimilates" MFP payments (p.8–9 [j.115–116]), which suggests a 2018–2020 baseline. This is an **inference**.

**2. Core findings.**
- Context:
  - 25% Chinese tariff; US soybean exports to China were $12.22B, 57% of US exports in 2017 (p.1 [j.108]).
  - US production fell from 116.93 MMT (2017) to 96.67 MMT (2020) (p.1–2).
  - China's SBO consumption fell from 16.50 to 15.89 MMT (17/18 → 18/19); US SBO consumption rose from 9.70 to 10.38 MMT (p.2 [j.109]).
  - MFP paid $1.65/bu (2018) and $2.05/bu (2019) (p.2).
- Scenario 1, tariff removal (p.6–7 [j.113–114]):
  - US exports to China: +40.52 MMT (+174.77%).
  - US soybean price: +$66.35/MT (+19.98%).
  - US crush: −4.29 MMT (−7.29%).
  - **US soy-oil price: +5.49%**; US meal price: −2.49%.
  - China crush: +3.69 MMT (+4.03%).
  - **SBO prices fall in almost every other country, but rise in the US and Mexico** (p.7 [j.114]).
- Welfare:
  - World welfare: +$2.08B (p.8 [j.115]).
  - US soy-oil consumers: −$373M (p.7).
  - With MFP also removed: world welfare +$2.25B; China −$1.4B (p.10 [j.117]).
- Literature cited (p.3 [j.110]):
  - The tariff lowered the US soybean price by 65¢/bu and raised Brazil's by 95¢/bu (Adjemian et al. 2021).
  - Brazil and Argentina supplied 92% of Chinese imports in Jul–Dec 2018 (Hitchner et al. 2019).

**3. What Nexus needs from it.**
- (a) **Split CE-011 by price node.** A US–China tariff moves **CBOT ZL (the US SBO price) and non-US/importer SBO prices in opposite directions**:
  - A tariff means more US crush, so US SBO falls.
  - China crushes less, so China and the world importer SBO market tightens.
  - The current CE-011 (`ontology.yaml`, candidate, direction DOWN on SBO_INTL_PRICE) merges these two.
- (b) Mechanism indicators:
  - USDA FAS **ESR soybean export sales to China** (commodity 801, country 5700; already wired via `production_connector.fetch_fas_esr_*`, A-019).
  - **US monthly crush and SBO production**: USDA NASS *Fats & Oils* (free). WASDE `CRUSH` is already parsed (`scripts/ingest_wasde_xlsx.py` _ATTR_MAP).
  - Tariff event dates (USTR / MOFCOM) for the policy calendar, including the Phase One deal (Jan 2020).
- (c) For G3: a qualitative scenario prior that a tariff escalation **widens the US–AR SBO price spread**. That changes which origin is cheaper.

**4. Rationale.**
- **G1** (correct sign for a structural driver).
- **G3** (origin alternative).
- The Korean buyer imports from US, AR, BR and VN. Using CBOT ZL direction as a proxy for Korean CIF direction under a tariff shock gives the **wrong sign** for the AR/BR channels.

**5. Priority / class.** **Should**. **Adopt** as a structural sign prior (ontology refinement); **Background** for modelling.

**6. Caveats.**
- Comparative statics with linear demand: no time path and no lags, so it cannot be validated in a walk-forward.
- Simulates *removal*, not imposition; symmetry is assumed only through linearity.
- Bean-centred; SBO and meal are joint products in fixed proportion.
- Single calibration year, undisclosed in the main text.
- No leakage risk because it is not a feature, but **its numbers are not forecasts**.

**7. Repo overlap.**
- CE-011 in `ontology.yaml`.
- D-009 "Case D" (2024–25 US–China tariff, similarity 9/10) in `docs/memory_archive/2026-05.md`.
- `farmdoc_2024_US_Brazil_China_soybean_triangle_20yr.pdf` (references README; also used as CE-011 evidence per A-239 in `docs/memory_archive/2026-08.md`).
- `gpr_connector` US_CHINA_TARIFF_STATUS proxy (A-045).
- 2018 stress slice.

**Lens discussion.**
- **P1-01**: This is the most important driver insight in the batch for the Korean buyer. A US–China trade war is *bearish for ZL but potentially bullish for Argentine/Brazilian oil delivered to Asia*. CE-011 should get two outcome nodes, and the brief should show the US–AR spread.
- **C-03**: Agreed on the ontology, but an SEM cannot enter the model. Use it only as a sign prior for the CE edge, to be validated with local projections of ZL and of the AR/BR FOB series on tariff event dummies (2018-07, 2019-05, 2020-01, 2025). Until AR/BR FOB daily or monthly series exist, the split edge stays `candidate`.
- **Joint conclusion**: Refine CE-011 by origin and acquire the AR/BR SBO FOB series. Treat the paper's magnitudes as illustrative only.

---

## Paper 4. Evaluating the market positions of soybean oil-producing countries in the world market

**1. Citation.** Qanitha, M., Majiidu, M., Puwawangsa, H., Ekayani, M. *IOP Conf. Series: Earth and Environmental Science* 1379, 012027 (2024), VEGOIL-2023 conference.
- Data: 2020–2021 export values (OEC, Statista, USDA) plus interviews (p.2–3).
- Method: BCG matrix.

**2. Core findings.**
- World SBO export value was USD 17.1B in 2021 (p.5).
- Export shares (p.5; repeated p.7):
  - Argentina 36%
  - Brazil 12%
  - USA 5.26%
  - Netherlands 5.13%
  - Paraguay 4.1%
- Export-value growth 2020→2021 (p.7 Table 1): Argentina +51.0%, Brazil +163.4%, USA −12.9%, Netherlands +61.6%, World +59.9%.
- BCG placement (p.8–9): Argentina "cash cow"; Brazil and Netherlands "question marks"; USA and India "dogs".
- Brazil: SBO is more than 80% of biodiesel feedstock demand (p.8).
- US SBO consumption: about 11.6 MMT in 2022 (p.6).

**3. What Nexus needs from it.** Only the qualitative confirmation that **Argentina dominates SBO exports**. Better, volume-based sources already exist or are free:
- USDA PSD SBO `Exports` by country
- UN Comtrade HS 1507 export **quantities** (key already registered)
- GATS

No new series is needed.

**4. Rationale.** **G1** background for origin concentration. Without it, nothing is lost.

**5. Priority / class.** **Background**; **Cite-with-caution**.

**6. Caveats.**
- The abstract names India, the Netherlands, Brazil and USA as the focus, yet Argentina is the headline result (p.2 vs p.8).
- A "cash cow" is defined as slow growth (p.4), yet Argentina's growth was +51% (p.7). The method is applied inconsistently.
- Single-year, value-based shares in a year of sharp price inflation, so "growth" is mostly price, not volume.
- No statistics, no time series. Not usable for modelling.

**7. Repo overlap.**
- D-047 market-structure brief (`data/raw/Market Structure (Production & Distribution)/`).
- `Dynamics_2025_AEPP_grain_oilseed_trading_concentration.pdf` (references README), which is far stronger.
- Customs/GATS origin data.

**Lens discussion.**
- **P1-01**: The share numbers are consistent with known structure: AR first, BR second, US small because US oil goes to domestic RD. Of mild interest: Brazil's biodiesel draws more than 80% from SBO, which supports the existing "Brazil B15 erodes export surplus" item (CE-023 per A-199).
- **C-03**: Not evidence-grade. Do not cite numbers in user-facing output; cite PSD/Comtrade volumes instead.
- **Joint conclusion**: Background only.

---

## Paper 5. Food Inflation Examination through the Dynamic Nexus between Olive Oil and Substitutes

**1. Citation.** Kyriazis, N.A. *Economies* 12, 57 (2024), doi 10.3390/economies12030057.
- IMF global prices (USD/MT), monthly, Jan 1990 – Oct 2023, log differences (p.4).
- Method: TVP-VAR connectedness.

**2. Core findings.**
- Averaged connectedness (p.7 Table 2):
  - SBO receives **36.11** from palm, 15.28 from sunflower, 1.86 from olive.
  - Palm receives **36.07** from SBO.
  - Total Connectedness Index = 33.34.
  - NET: palm +2.44, olive +0.31, SBO +0.12, sunflower −2.87.
  - Olive oil is almost isolated (95.88 own share).
- Time profile:
  - SBO's outward joint connectedness rose to about 60% by 2005, fell to about 40% in the early GFC, rebounded to about 60%, and dipped slightly below 50% at the pandemic onset (p.7–8).
  - **SBO turns into a net absorber during COVID and the Russia–Ukraine war** (p.9).
  - Palm is a net transmitter before the GFC and a net receiver after it (p.9).
  - Sunflower's outward connectedness rose during the war to just under 40% (p.9).
- Descriptive: SBO has the lowest mean return but the highest risk-adjusted return of the four (p.4).

**3. What Nexus needs from it.**
- (a) Confirmation that the **SBO–palm pair is the dominant cross-oil link**, with sunflower second and rising in war time. This supports watching sunflower under Black Sea disruptions (CE-013/014).
- (b) A **long-history monthly backfill** of world vegetable-oil prices from the IMF series on FRED. Codes are believed correct but **must be verified**:
  - `PSOILUSDM` (soybean oil)
  - `PPOILUSDM` (palm)
  - `PSUNOUSDM` (sunflower)
  - `PROILUSDM` (rapeseed)
  - `POLVOILUSDM` (olive)
  - These extend SBO–palm spread episodes back to 1990 (the repo's TE oils start in 2010). That gives G1 analogue lookups more independent episodes (2007–08, 1990s). Use ALFRED realtime_start for as-of (D-029 pattern).
- (c) Optional Challenger-candidate idea: a rolling oil-complex connectedness index as a regime feature (G3) or volatility covariate (G2).

**4. Rationale.**
- **G1** analogue depth: more episodes means fewer "insufficient sample, withheld" outcomes in `analogue_g1.py`.
- Without (b), spread analogues rest on about 15 years containing only a handful of independent episodes.

**5. Priority / class.**
- Background overall; olive oil itself is irrelevant to Nexus.
- (b) FRED IMF backfill: **Should** / **Adopt**.
- (c) Connectedness index: **Challenger-candidate**, low priority.

**6. Caveats.**
- Monthly IMF benchmark prices, not ZL settlement; the SBO series specification should be checked on FRED.
- The full-sample averaged connectedness table is descriptive. A rolling TVP-VAR feature would need a one-sided Kalman filter only.
- No approved library: R `ConnectednessApproach` / Python equivalents are not in `.claude/rules/libraries.md`.
- Table 1 is partly garbled in the extraction.

**7. Repo overlap.**
- Olive oil (HS 1509) is explicitly **excluded** in `docs/research_desk/2026-08/customs_substitute_scope_2026_08_13.md` l.112.
- CE-015.
- `Heliyon_2024_soybean_quantile_VAR_connectedness.pdf`.
- TE's four oils (data_requirements §0).
- W0 Stage 2 wavelet-coherence plan in `docs/research_desk/2026-09/reference_period_calibration.md` §Stage 2.

**Lens discussion.**
- **P1-01**: Olive is out of scope. The useful signal is that in crises SBO **absorbs** rather than transmits. In 2020 and 2022 shocks entered through palm and sunflower, so supply news for those oils should be watched as leading context.
- **C-03**: That reading comes from a full-sample smoothed connectedness path on monthly data. It cannot be used as a lead-lag claim. The concrete value is the free 1990+ monthly backfill.
- **Joint conclusion**: Adopt the FRED IMF monthly oil prices for analogue history. Everything else is background.

---

## Paper 6. Quantile coherency of futures prices in palm and soybean oil markets

**1. Citation.** Fousekis, P. *Journal of Economics and Finance* 48, 129–141 (2024), doi 10.1007/s12197-023-09647-6.
- Daily futures, 1 Jan 2015 – 31 May 2023, from investing.com, in $/MT (p.5 [j.133]).
- **Contract specifications are not stated.** Presumably CBOT soybean oil and Bursa palm, converted.
- Returns are pre-filtered with ARMA-GARCH (p.5; p.12 Table 8).

**2. Core findings.** Quantile coherency (SBO quantile, palm quantile) at 1 week / 1 month / 12 months (p.6 [j.134] Table 1):

| Quantile pair | Market state | 1 week | 1 month | 12 months | Significance |
|---|---|---|---|---|---|
| (0.05, 0.05) | bear–bear | 0.239 | 0.488 | 0.506 | p < 0.01 |
| (0.50, 0.50) | normal–normal | 0.440 | 0.515 | 0.519 | p < 0.01 |
| (0.95, 0.95) | bull–bull | 0.149 | 0.169 | 0.175 | p ≈ 0.08 (10% level only) |

- **The two prices crash together more than they boom together.** Bear–bear exceeds bull–bull at the 1-month and 1-year scales (p.8 [j.136] Table 3; Table 4).
- Every long-run coherency is below 0.52, so the two markets are **not well integrated** (p.7 [j.135] fn.7).
- Most adjustment is done **within about 1 month**: medium vs long-run differences are small (p.1; p.7).
- Decoupling episodes (p.5 fn.4):
  - **Q2 2021**: US RD capacity concerns.
  - **Q2–Q3 2022**: after Indonesia's export ban of 28 Apr – 23 May.
- US exports no more than about 10% of its SBO (p.11 [j.139]).
- Policy outlook: ID/MY raise biodiesel mandates; the EU phases out palm biodiesel by 2030 (p.11).

**3. What Nexus needs from it.**
- (a) **Re-specify how the SBO−CPO spread alert (175 USD/MT; CE-015, `p101` and `c03` §1 tables) is interpreted.** In bull states palm does not follow SBO. A wide spread during an SBO-specific rally (RD demand, US policy) is therefore **not** evidence of imminent substitution or mean reversion. In bear states the two move together.
- (b) **Feature design for G2**: give Quantile LightGBM palm-return and spread features, and *expect* their importance to differ by quantile (strong for P10/P50, weak for P90). Check this per quantile rather than forcing a single coefficient.
- (c) **Horizon**: spread information should mainly matter at **h ≤ 20 trading days**. Little incremental value is expected at h = 60.
- (d) Add **named stress slices** to G2 evaluation: 2021-Q2 and 2022-Q2/Q3.
- (e) Data:
  - Daily palm: repo TE palm (`PLO:COM`, A-159) plus `DEXMAUS` if MYR conversion is needed.
  - Bursa FCPO official daily is paid (g2_additional_data_requirements B-4, about $25/month).
  - **investing.com must not be used** (ToS, A-012).

**4. Rationale.**
- **G1** (alert semantics).
- **G2** (asymmetric quantile features; regime coverage).
- **G3** (regime).
- Without it, the 175 threshold keeps firing in bull markets with a mean-reversion story the data do not support. The buyer could wait for a "substitution correction" that does not come, which is a costly error in the G3 "buy now vs later" decision.

**5. Priority / class.** **Must**. **Adopt** (interpretation rule, asymmetric features, stress slices). The method itself (quantile coherency) is **Background / Challenger-diagnostic**.

**6. Caveats.**
- Contemporaneous co-movement only, no lead-lag.
- Full-sample frequency-domain estimate: any threshold derived from it must be re-estimated inside training folds.
- Sample ends May 2023 and misses the 2024 inversion in which palm traded above SBO (farmdoc, references README).
- Contract specifications are unclear.
- Quantile coherency needs R `quantspec`, which is not on the approved list (`libraries.md`; CLAUDE.md §3.1 allows R only when Python lacks an equivalent).
- **Apparent tension with Heliyon 2024 QVAR**: that paper reports connectedness *rising* to 91% and 87% at the 0.1 and 0.9 quantiles. The measures differ: multivariate system connectedness of the soybean complex with international markets vs bivariate palm–SBO coherency. Both can be true, but they must not be cited interchangeably.

**7. Repo overlap.**
- CE-015 (candidate) in `ontology.yaml`.
- `farmdoc_2025_soy_palm_price_relationship.pdf`. A-201 injected the rule "no mean-reversion assumption; 175 only under regime awareness". **This paper is independent quantitative support for that rule.**
- `Heliyon_2024...` (contrasting tail result).
- `palm_crosscheck_structural_indicators_2026_09_28.md`.
- W0 Stage 2 wavelet coherence (`reference_period_calibration.md`).
- B-4 FCPO in `g2_additional_data_requirements_2026_09_09.md`.

**Lens discussion.**
- **P1-01**: Keep the 175 spread as a *context* indicator. Attach a regime tag: in a bull/RD-driven regime, the alert text should say substitution pressure is building but historically does not cap SBO rallies quickly. In a bear regime, a narrowing spread plus falling palm is a downside confirmation.
- **C-03**: Go further. Demote the fixed 175 alert until its predictive value is tested per regime with as-of data. Also require the quantile-specific importance check in the Quantile LightGBM experiment card.
- **Joint conclusion**: Adopt a regime-conditional interpretation now (low cost, high value). Promotion of the threshold as a *signal* waits for per-regime validation.

---

## Paper 7. Returns and volatility linkages in the US soybean industry: an empirical analysis across time and frequencies

**1. Citation.** Fousekis, P., Grigoriadis, V. *Modern Finance* 3(3), 133–149 (2025), doi 10.61351/mf.v3i3.355.
- Daily front-month futures ZS, ZM, ZL from Yahoo Finance, 1 Jan 2010 – 30 May 2025 (p.4 [j.136]).
- Method: Wavelet Local Multiple Correlation (WLMC).

**2. Core findings.**
- Definitions (p.4–5 [j.136–137]):
  - **Oilshare** = oil value / (oil + meal value), using 11 lb oil and 44 lb meal per bushel. The printed eq. 6 has a typo: "(oilshare)(0.11)" should read (oil price)(0.11).
  - **Crush spread** = meal×0.022 + oil×0.11 − soybeans/100, in $/bu.
- Oilshare history: 40–45% at the start, fell in 2012, **25–35% until 2020**, rose sharply in 2021–22, **about 40% since** (p.5 [j.137]).
- US SBO use: about 50% food/industrial, about 45% biodiesel, the rest exported (p.1 [j.133]). Crush yields about 80% meal / 20% oil (p.2).
- Correlations:
  - Trivariate WLMC is positive everywhere: about 0.8 at short scales and above 0.9 at long scales (p.9 [j.141]).
  - **Oil–meal** correlation was about 0.1 in 2014–2020 and has been negative recently, ranging from −0.5 to 0.8 at larger scales (p.9).
  - Meal–soy is mostly above 0.7 (p.9).
  - Correlations trend down, consistent with the shift to "crushing for oil" (p.10 [j.142]).
- Dominance: **soybeans are the dominant variable**, so oil and meal are weakly exogenous. Information flows from products to the input (demand-driven integration; Verleger hypothesis: the crush spread is predictive for soybeans) (p.10–11 [j.142–143]).
- Troughs in 2015, 2019 and 2022; peaks in 2017 and 2020 (p.9).
- Realized-volatility co-movement is high, with soybean RV dominant (p.11).
- Setup: 260-day Gaussian (two-sided) window; MODWT J=7, la8 filter (p.7–8 [j.139–140]).

**3. What Nexus needs from it.**
- (a) **Series**:
  - ZM=F and ZS=F daily from yfinance now (free; same pattern as ZL=F).
  - Settlement-grade versions from Databento ZM/ZS later (approved 9/1 but still a **DATA GAP** per `g2_preview_plan_2026_11_16.md` l.90).
- (b) **Features**, all lagged ≥ 1 day, with as-of rules matching ZL:
  - Board crush (¢/bu = ZL×11 + ZM×2.2 − ZS; the repo formula)
  - Oilshare
  - Oil–meal rolling correlation
- (c) **Yield-adjusted variant**: NOPA/NASS now show about 12 lb oil per bushel vs the fixed 11 (farmdoc RD-boom P2, references README). Compute an "actual-yield crush" from USDA NASS *Fats & Oils* monthly (crude oil produced ÷ beans crushed), as-of its release date.
- (d) **Oilshare regime indicator** (oil-led vs meal-led crush) for G3 regimes and G1 analogue conditioning.

**4. Rationale.**
- **G1**: the crush margin is the market's own summary of the soybean-oil demand regime. It is the "missing structural variable" named in data_requirements G1-1.
- **G3**: regime.
- **G2**: quantile features.
- Without ZM, the repo cannot build the variable that best represents the RD-era structure (farmdoc P2/P3 already identify it as the structural driver).

**5. Priority / class.**
- Data and features: **Must** / **Adopt**.
- WLMC method: **Background**. It is descriptive only, under the same restriction as PyWavelets in `.claude/rules/libraries.md` (post-hoc analysis only; no feature derivation).

**6. Caveats.**
- Contemporaneous, not lagged; the authors note delayed dependencies are not handled (p.14).
- **Two-sided window and MODWT are non-causal**, so WLMC values are not usable as features (same leakage class as VMD, M-010).
- Front-month Yahoo series include roll jumps (repo A-130 roll-day flag); the crush should be built from same-contract-month or roll-adjusted series.
- Paper's "ZL is weakly exogenous" means ZS is unlikely to lead ZL. The value of the crush variable is regime information, not lead-lag.

**7. Repo overlap.**
- `data_requirements_by_phase_2026_08_29.md` G1-1/G1-2.
- `g2_additional_data_requirements_2026_09_09.md` B-2.
- `g2_preview_plan_2026_11_16.md` l.78, l.90.
- farmdoc RD-boom P2/P3 (oil value share 25–35% → 35–50%; matches this paper's oilshare path).
- CE-020 lag_basis and CE-022 (`ontology.yaml`).
- `libraries.md` PyWavelets restriction.

**Lens discussion.**
- **P1-01**: Make the crush margin and oilshare a top-tier G1 variable and a G3 regime axis. A high oilshare means crushers run for oil, which means more SBO supply later (CE-022 mechanism) but strong current demand.
- **C-03**: Caution on circularity. Both crush and oilshare contain ZL itself. A same-day crush "explains" ZL mechanically. Require:
  - lagged construction
  - evaluation of **incremental** information beyond ZL's own lags (ablation in the walk-forward)
  - roll-safe contract matching
- **Joint conclusion**: Adopt the data and features immediately via yfinance and upgrade to Databento settlement. Report crush importance only from the ablation, not raw SHAP.

---

## Paper 8. Using Futures Prices and Analysts' Forecasts to Estimate Agricultural Commodity Risk Premiums

**1. Citation.** Cortazar, G., Ortega, H., Pérez, J.A. *Risks* 13, 9 (2025), doi 10.3390/risks13010009.
- Futures: weekly (Wednesday) CBOT settlements for corn, soybeans and SRW wheat. 2016–2020 in-sample, 2021 out-of-sample (p.8).
- Analyst forecasts: Bloomberg, 12–14 banks, averaged in 15-day maturity buckets (p.9).
- **No soybean oil.**

**2. Core findings.**
- Model: 5 factors (3 latent + 2 crop-year factors), Kalman filter / maximum likelihood (p.5–6).
- Futures-curve fit for soybeans, MAPE (p.11 Table 4; units appear to be %, which is an **inference**):

| Model | In-sample | Out-of-sample |
|---|---|---|
| 5F | 0.2135 | 0.4092 |
| 3F | 0.5314 | 1.0644 |
| 3F + seasonality | 0.3709 | 0.7562 |

- Expected-price (analyst) MAPE for soybeans: 4.21 in-sample, 14.48 out-of-sample (p.12 Table 6).
- Risk premiums:
  - **Soybeans: negative for maturities under 1 year, positive beyond 1 year and converging to about 2%** (p.15; p.17).
  - Annual premiums across grains range from about 0% to 14% in absolute value; corn smallest, wheat largest (p.14).
- Premium signs are cross-checked against CFTC COT net positions (p.16 Fig. 7).
- US crop year runs Sep–Aug for corn and soybeans (p.3).

**3. What Nexus needs from it.**
- (a) **ZL term structure features**: front vs next contract, and old-crop vs new-crop calendar spreads. The SBO marketing year is Oct–Sep. These act as a storage/convenience-yield signal (theory of storage, p.2). Only Databento provides deferred ZL months (all expiries via parent symbol). yfinance gives the front month only.
- (b) **A "futures-implied" reference for G2**: for h = 60, compare the G2 P50 to the deferred contract nearest to t+60, interpreted as a risk-neutral, not expected, price. Add it as a benchmark row next to the mandatory baselines (last value, seasonal naive, ETS).
- (c) **A free "expected price" proxy** instead of paid Bloomberg consensus: the USDA WASDE US soybean-oil season-average price projection, as-of its release date.
  - **Verify** that it is parsed. `scripts/ingest_wasde_xlsx.py` `_ATTR_MAP` maps only "Avg. Farm Price" (about l.77). The SBO price attribute label may differ; this is unverified.
- (d) The COT positioning sign is already implemented in `cot_connector.py` (managed money, producer, swap net positions).
  - Add a **managed-money net z-score** as a G2 volatility/quantile feature and a G1 context indicator.

**4. Rationale.**
- **G2**: calibrating the band against what the market itself prices.
- **G3**: the "buy later" simulation must not treat the futures forward as an unbiased expected price.
- Without (b) there is no external sanity check on P50 drift.
- Without (a) the model ignores the curve shape, which professional buyers watch (carry vs inverse).

**5. Priority / class.**
- (a) term structure and (d) COT: **Should** / **Adopt**.
- (b) futures-implied benchmark: **Should** / **Adopt** as an evaluation row.
- The 5-factor model itself: **Background**, not needed for the Champion stack.
- Bloomberg analyst data: **not recommended** (paid).

**6. Caveats.**
- Grains, not SBO. SBO has no harvest (continuous crush), so crop-year effects reach it only indirectly through beans and crush.
- Short sample (2016–2021).
- Analyst forecasts are noisy (14% out-of-sample MAPE).
- Kalman parameters are fitted on the full sample.
- Weekly data.
- Leakage:
  - Analyst and WASDE forecasts must use the vintage available at t (D-023).
  - Calendar spreads must be built from contracts actually listed at t, with roll dates known ex-ante.
- Pulling deferred months from Databento is extra metered usage beyond the approved ZM/ZS/options scope.

**7. Repo overlap.**
- `cot_connector.py` (implemented 11/16; `g2_preview_plan_2026_11_16.md` l.110).
- `JRD_2024_financialization_grain_price_volatility_KR.pdf` (COT rationale, references README).
- `c03-data-scientist.md` §5 baselines.
- `src/evaluation/band_backtest.py` (`g2_preview_feasibility_2026_09_14.md` l.31).
- `scripts/ingest_wasde_xlsx.py`.
- No existing repo work on ZL term structure was found (grep of docs/ and src/).

**Lens discussion.**
- **P1-01**: The curve matters to buyers. A steep inverse (front over deferred) signals current tightness and favours buying deferred. A carry signals comfortable stocks. This is a classic trader indicator that Nexus lacks.
- **C-03**: Useful, but it needs new metered Databento pulls and careful roll handling. The futures-implied forward is a *benchmark*, not a Champion component. Promotion of term-structure features follows the §4 rules like any other feature.
- **Joint conclusion**: Adopt term-structure features and the futures-implied benchmark, subject to a Databento cost estimate. Use WASDE SBO price projections as the free expectation proxy.

---

## (a) Ranked top-10 items across the 8 papers

| Rank | Item | Papers | Goal | One-line rationale |
|---|---|---|---|---|
| 1 | **Board crush and oilshare features** from ZL/ZM/ZS: yfinance ZM=F/ZS=F now, Databento settlement later. Lagged, roll-safe, plus a NASS actual-yield variant; promote only via ablation | 7 (3) | G1, G3, G2 | The RD-era structural variable the repo cannot yet build (ZM is a DATA GAP) |
| 2 | **Regime-conditional reading of the SBO−CPO spread / CE-015**: asymmetric (quantile-specific) palm features, information horizon ≤ 20 days, 175 threshold as context not trigger | 6 (5) | G1, G2, G3 | Palm does not follow SBO rallies; a fixed mean-reversion alert misleads timing decisions |
| 3 | **Split CE-011 by price node** (US ZL vs non-US/importer SBO), plus US–AR/BR SBO FOB spread series and ESR China export sales and NASS crush as mechanism indicators | 3 (1) | G1, G3 | A tariff shock moves ZL and Asian-delivered AR/BR oil in opposite directions |
| 4 | **Regime-interacted energy elasticity**: WTI/Brent/heating oil × dated policy regime; rolling/LP stability check before ranking | 2 | G1, G2 | The SBO–crude elasticity moved 0.29 → 0.96 → 0.18; a pooled coefficient is wrong in every regime |
| 5 | **Dated policy-event calendar** (AR export tax, CN tariffs, RFS/RVO/45Z) used as structural-break dummies with as-of = publication date, not asymmetric terms | 1, 2, 3 | G1, G2 | Interventions cause breaks and decoupling, not asymmetry; ex-ante dates avoid look-ahead |
| 6 | **Named G2 stress slices** 2021-Q2 (RD decoupling) and 2022-Q2/Q3 (Indonesia ban), plus regime-specific coverage | 6 | G2 | Documented palm–SBO decoupling episodes are where band coverage is most likely to fail |
| 7 | **ZL term-structure features** (front–next, old/new-crop spreads) and a **futures-implied benchmark** row for G2 | 8 | G2, G3 | The market's own risk-neutral curve is the natural external check on P50 drift and carry |
| 8 | **FRED IMF monthly oil prices 1990+** (verify codes PSOILUSDM/PPOILUSDM/PSUNOUSDM/PROILUSDM) for G1 analogue history | 5 | G1 | Triples the history for spread analogues; free; ALFRED gives as-of |
| 9 | **COT managed-money net z-score** as G2 volatility/quantile feature and G1 context (connector already exists) | 8 | G2, G1 | Positioning extremes reflect hedging pressure / risk premium; near-zero cost to add |
| 10 | **WASDE US SBO season-average price projection** as a free expected-price proxy (verify parser coverage) | 8 | G2, G3 | Replaces paid Bloomberg consensus; vintage-safe expectation benchmark |

---

## (b) Disagreements between the two lenses

1. **Energy as a "core driver"** (Paper 2). P1-01 wants diesel/crude near the top of G1 in the RD era. C-03 refuses a pooled ranking because the coefficient is regime-unstable and the paper ends in 2020. **Resolution**: per-regime coefficients and fold-wise sign stability before promotion.
2. **The 175 USD/MT spread threshold** (Paper 6). P1-01 keeps it as a context alert with a regime tag. C-03 wants it demoted from signal status until per-regime predictive tests pass. Both agree the mean-reversion story is invalid in bull states.
3. **SEM tariff results** (Paper 3). P1-01 wants CE-011 split and the US–AR spread shown in the brief now. C-03 accepts the split only as a `candidate` sign prior until local projections on AR/BR FOB series validate it. The SEM numbers never enter a model.
4. **Crush/oilshare importance** (Paper 7). P1-01 sees crush as a top driver. C-03 flags circularity (ZL is inside the crush formula) and demands lagged construction plus ablation-based incremental value, not raw SHAP.
5. **Term structure** (Paper 8). P1-01 treats carry/inverse as a primary buyer signal. C-03 treats it as a benchmark and feature candidate that needs metered Databento data, roll discipline, and the normal promotion gates.
6. **Asymmetry in intervened origins** (Paper 1). P1-01's prior was asymmetry for AR/CN. C-03 notes zero empirical support and rejects threshold ECMs. P1-01 accepts with the reinterpretation "breaks and decoupling".
7. **Tail co-movement** (Papers 6 vs Heliyon 2024, already in the repo). Weak bull-tail SBO–palm coherency vs high tail connectedness in a QVAR system. Not a lens disagreement as such, but both lenses insist the two results not be cited as equivalent.

---

## (c) Items needing paid data or approval

| Item | Why | Status / what is needed |
|---|---|---|
| Databento **ZM/ZS settlement** | Settlement-grade crush (rank 1) | Approved 2026-09-01, still not ingested (`g2_preview_plan_2026_11_16.md` l.90, D-3 cost cap proposal $25). yfinance can bridge without cost |
| Databento **ZL deferred contract months** | Term structure (rank 7) | **New scope**: needs a cost estimate and approval (metered usage beyond the approved ZM/ZS/options) |
| **Bloomberg analyst consensus** | Paper 8's expectation proxy | Paid. **Not recommended**; use WASDE projections (rank 10) |
| **Bursa FCPO official daily** | Exact palm futures for Paper 6 replication | Paid (B-4, about $25/month). Optional; TE palm daily already available |
| **investing.com** price data | Paper 6's source | Do not use (ToS risk, A-012) |
| **R `quantspec`** (quantile coherency), **ConnectednessApproach** (TVP-VAR), **VisualDom** (WLMC) | Replicating the papers' diagnostics | None is in `.claude/rules/libraries.md`. Approval is required to add them (and R is permitted only when Python lacks an equivalent, CLAUDE.md §3.1). Not needed for the adopted items |
| New free connectors (FRED IMF oils, EIA crude production, AR MAGyP FOB, NASS Fats & Oils) | Ranks 3, 4, 8 | Free. Source URLs for AR FOB are **unverified**. No firewall approval is needed under the current personal-laptop setup (CLAUDE.md §1), but each needs as-of rules in `asof.py` and a schema entry |
| Ontology changes (CE-011 split, CE-015 interpretation note, CE-020 regime note) | Ranks 2–5 | Per repo practice, causal-edge promotion needs domain validation (S-1) and `validate_semantic_layer.py --strict` |


---

# Project Nexus — Review of 8 trade / market-structure papers (soy complex)

Review date: 2026-11-17 · Reviewer: research sub-agent (read-only on repo)
Lenses (repo definitions): **C-02** Market Research & Intelligence (synthesis, market structure, source grading) · **P1-02** Geopolitical & Trade Risk (trade-policy pivots, chokepoints, US–CN tariff) · **P1-03** Agrometeorologist & Climate (ENSO, regional drought, yield revisions).

## Conventions

- **Locators.** `p.N` is the PDF page number of the extracted text, matching the `--- page N ---` markers in the .txt files. For Fares (J Agrar Change), the printed journal page is also given (`p.5/481`).
- **Source grade (R-018 §5).** All figures below are *published-paper* figures (공개). None of them are 실측 (measured) Nexus data.
- **"Nexus collects?"** is based on the connectors and config I inspected:
  - `customs_connector.py`: Korea Customs, HS 150710/150790 plus substitutes plus 120190/230400, by country, monthly. UN Comtrade is only a fallback, for Korea HS1507 imports.
  - `wasde_connector.py`: USDA PSD API plus the PSD oilseeds bulk CSV.
  - GATS: `GATS_US_SBO`, `GATS_US_RSBO`, `GATS_US_SBO_EXPORT_KOREA`.
  - `climate_connector.py`: Open-Meteo ERA5-Land for 23 regions (tier-1 includes BR Mato Grosso), plus NOAA ONI.
  - `asof.py` has release rules for `FAOSTAT_` and `COMTRADE_` prefixes.
  - **Not collected** (no connector found): Brazil ComexStat/Secex, Argentine INDEC, China GACC customs, CEPII-BACI, Trase.
- **Scope note.** Seven of the eight papers analyse **soybeans (beans)**, not soybean oil. Every transfer to SBO is labelled *direct* or *inference*.

---

## 0. Duplicate check — "China's financialized soybeans" vs repo `China_2023_financialized_soybeans_food_regime.pdf`

| Check | Repo copy | New copy |
|---|---|---|
| SHA-256 | `8aa9a6e5…` | `2bdc8260…` |
| Bibliographic | J Agrar Change 2023;23(3):477–499, DOI 10.1111/joac.12536 | identical (new p.1, p.1/477) |
| Dates | received 2021-11-19 · revised/accepted 2023-02-16 | identical |
| Pages | 23 | 23 |
| Difference | Publisher download watermark dated 2026-08-26 (institutional download stamp) | Watermark dated 2026-11-16 (no institution) |

**Verdict: same paper, same version of record.** The hash differs only because of the per-download watermark Wiley stamps on every page. No new content.

**Action:** do not register it as a new reference. One option is to keep the new copy as the archival copy, since its watermark carries no institution name. That is the approver's call.

The repo's `summaries/China_2023_financialized_soybeans_food_regime.md` is still a **skeleton**: its "핵심 주장 / Nexus 관련성 / 온톨로지" sections are marked "(미작성)". Section 2 below can fill it. The README line already records the key facts (41% non-China, one-third of crush capacity abroad, CIL shareholder structure).

---

## 1. Cordeiro Junior, dos Santos, Silva & Cordeiro — RCA of the soy complex, Brazil vs USA (1980–2024)

**1. Citation.** Rev. Gestão Social e Ambiental (RGSA) 19(8): e012929, 2025, DOI 10.24857/rgsa.v19n8-086. Data: the title says 1980–2024, but p.9 states the RCA series covers **1980–2023**. Sources: FAOSTAT, MAPA/Agrostat, Comtrade, IPEA, WTO (p.9).

**2. Core findings.**
- Balassa RCA = (X_ij/X_i)/(X_wj/X_w), computed for beans, meal and oil (p.8).
- Table 1 (p.14) compares mean RCA for 1980–93 with 2013–23. (The table's "ARB" column header is BRA.)

  | Product | Brazil | USA |
  |---|---|---|
  | Beans | 8.77 → 37.67 (+329.5%) | 6.56 → 4.30 (−34.5%) |
  | Meal | 30.14 → 20.12 (−33.2%) | 2.25 → 1.71 (−24.0%) |
  | **Oil** | **18.65 → 10.51 (−43.7%)** | **1.93 → 0.93 (−51.8%)** |

- **US SBO RCA has been below 1 since 2021 and falling**, attributed to biofuel demand pulling SBO into the domestic market (p.13, p.15).
- **Brazil SBO RCA has fallen since 2008, when the mandatory biodiesel blend started.** When the mandate was cut in 2020, crushers "relocated" oil to export and RCA rose. The 2022/23 crush expansion added export volume (p.13).
- The 1996 Kandir Law exempted primary/semi-processed exports from ICMS. That favoured bean exports over meal and oil (p.10, p.15).
- China's crush expansion cut its imports of Brazilian meal and oil over 2010–18 (p.11).
- The 2018 trucker strike delayed Brazilian flows and dented importer confidence (p.11–12).

**3. What Nexus needs.**
- **US SBO export share / RCA proxy:** US SBO exports ÷ world SBO exports. Sources: GATS (collected) and PSD world SBO trade (collected through the PSD bulk file). This is a derived indicator Nexus can compute now. It tracks CE-022.
- **Brazil SBO export volume and share.** PSD (collected, annual or monthly-updated MY). Monthly ComexStat NCM 1507.10/1507.90 by destination is free but **not collected**.
- **Brazil biodiesel blend % timeline** (ANP/CNPE). Free. Exists only as a news indicator (`BIODIESEL_MANDATE_NEWS`); there is no numeric series.

**4. Rationale.**
- **G1:** it supplies a structural, origin-channel variable (the US vs Brazil SBO export role), which the README "차별점" asks for.
- **Semantic layer:** it is direct, long-run evidence for CE-022 (US) and CE-023 (BR).

**5. Priority / class.** **Should · Adopt** (indicator concept plus evidence).
- **SBO relevance: direct.** Oil is one of the three products analysed.
- Annual, value-based RCA is a slow structural descriptor. It is not a 1–60-day feature.

**6. Caveats.**
- Lower-tier journal.
- Mixed sources: sector exports from FAOSTAT, totals from WTO/IPEA. This creates a consistency risk.
- RCA ignores tariffs, subsidies and FX misalignment, as the authors admit (p.8).
- Causal attributions (mandate, Kandir) are narrative and cite other papers. They are not estimated.

**7. Ontology candidates (evidence only, no new edge).**
- **CE-023 evidence:** "BR biodiesel blend ↑ → domestic SBO absorption → BR SBO export RCA ↓ (2008); blend cut 2020 → exports ↑" (p.13). This *supports* the edge's direction. It also matches the repo's own note that the effect is conditional on crush growth.
- **CE-022 evidence:** "US biofuel demand → US SBO RCA < 1 from 2021 → export availability ↓" (p.13).

**Lens discussion.**
- **C-02:** The best SBO-specific paper in the set. Use it as citable long-run evidence for both mandate edges. Also have Nexus build its own monthly US/BR/AR SBO export-share series rather than citing RCA levels.
- **P1-02:** The Kandir Law and China's tariff escalation (cheaper to import beans than oil) are policy levers, and they explain why Brazil sells beans to China and why Korea buys SBO mostly from AR/US. Watch for Kandir/ICMS reform or a Chinese tariff change as low-frequency regime events.
- **P1-03:** Climate plays almost no role. The paper mentions the 2004/05 Brazilian climate shortfall in passing (p.5). It has no use for weather models.
- **Joint conclusion:** Adopt as evidence for CE-022 and CE-023, and build the derived US-SBO-export-share indicator from GATS and PSD. Do not use RCA levels as model inputs.

---

## 2. Fares — China's financialized soybeans: fault lines of neomercantilism narratives (duplicate, see §0)

**1. Citation.** Fares, T. M., J. Agrarian Change 23(3):477–499, 2023 (SOAS). Data roughly 2009–2021 (Figures 1–10). Sources include BRIC Agri, Qichacha, Trase, China Lianhe credit reports and Fortune.

**2. Core findings.**

*China's domestic crush and import market*
- China's crush sector became over-capacity: beans going to crush fell from **75% to 64%** of supply between 2012 and 2018, while beans stockpiled or discarded rose 8 pp (p.5/481).
- By 2016 debt ratios were **81.27% (Beidahuang), 81.01% (COFCO) and 71.36% (Chinatex)**, against SASAC's 70% red line (p.5–6/481–482).
- COFCO replaced Sunrise as China's top soybean importer in 2013–17 and became the largest crusher from 2016 (p.11/487).

*COFCO's offshore footprint*
- **One-third of COFCO crush capacity (30 of 90 Mt) is abroad**, where it earns over half its income (p.12/488).
- In 2018, **41% of COFCO's Brazil and Argentina soybean exports went to the EU, ASEAN and other non-China destinations** (p.13/489).
- In 2013, Noble plus Nidera held **15% of Argentine soybean exports and 12.8% of Argentine crush capacity**, and 6.1% of Brazilian exports (Table 2, p.12/488).

*Financialization and listing*
- COFCO International (CIL) is incorporated in the Cayman Islands. Its shareholders are Rosy Wisdom 60%, the HOPU (Goldman-led) consortium 19%, IFC 9%, Temasek affiliate 9% and Standard Chartered 3% (p.14/490).
- **COFCO futures margin rose from RMB 2.87bn (2015) to 6.02bn (2019)**, while food manufacturing and sales income fell from 39.99bn to 25.75bn (Table 3, p.15/491).
- CIL joined the Covantis blockchain consortium with the ABCD traders in 2018 (p.15/491).
- China Agri withdrew from the HKEx in 2019 amid US trade tensions (p.18/494).

**3. What Nexus needs.**
- **China SBO net-trade position and crush utilisation.** PSD China SBO and soybean rows are collected via the bulk CSV. GACC monthly customs data is not collected.
- **COFCO entity attributes for the market-structure KB:** offshore crush share, non-China destination share, CIL ownership. These are entities.yaml/KB items, not time series.

**4. Rationale.** It improves **interpretation discipline** in the semantic layer and in P1-05/06. It is the academic basis for the repo's existing A-219 rule: separate state demand from commercial channels, and do not read COFCO buying as Chinese state stockpiling. It also bears on the CE-012 status review: China's crush over-capacity makes the "China as SBO exporter" regime plausible.

**5. Priority / class.** **Should (semantic rule) · Background.** It is already in the repo, so treat it as a duplicate.
- **SBO relevance: inference.** The paper is about bean crushing and corporate finance. The SBO link runs through China's crush output.

**6. Caveats.**
- Political-economy method, one author.
- Many numbers come from paid Chinese databases (BRIC, Qichacha, Cofeed) and cannot be re-verified for free.
- Data end around 2019–21, before COFCO's later restructurings.

**7. Ontology candidates.**
- **CE-012 caution evidence:** "COFCO purchase ≠ Chinese state demand: 41% of COFCO's South American exports go to non-China destinations (p.13/489)." Use it as a precondition check, not as an edge.
- **Supporting evidence for the repo's pending path** (CE-012 note): "China crush over-capacity (crush share 75→64%, p.5/481) → SBO surplus → Asian refined-oil exports → Korea CIF ↓." This is a candidate only; it needs P1-06 validation.

**Lens discussion.**
- **C-02:** High value as a reading rule. It also confirms COFCO behaves like an ABCD-style trader: multi-destination, financed and hedged. That is consistent with the D-047 brief and with Wilson et al. 2025 (COFCO first in CNF).
- **P1-02:** Disagrees mildly. State backing still matters in a shock: the 2025–26 "SOE buys US new crop vs commercial importers buy South American" split in the repo (CE-011 evidence) is a state-directed channel. Financialization does not remove political buying, so both channels must be modelled.
- **P1-03:** No climate content.
- **Joint conclusion:** Keep it as the source for the channel-separation rule. Complete the existing skeleton summary rather than adding a new reference.

---

## 3. Tixiliski — Chinese global agribusiness project in the Brazilian soybean commodity chain

**1. Citation.** Tixiliski, G. O., Brazilian Journal of Political Economy 44(2):340–356, 2024, DOI 10.1590/0101-31572024-3525. Qualitative and historical; investment data to about 2021 (AEI, CEBC, Red-ALC).

**2. Core findings.**
- China's agricultural outward FDI is only **1.3%** of its total outward FDI. It reached **US$27.9bn in 2016** (+36% vs 2005) (p.7).
- There were two phases: land grabs in 2000–12, then M&A from 2012 (p.7–8).
- In 2017 COFCO's profit was **US$200m vs Bunge's US$700m**, with **790m** in state subsidies in 2016 (p.8).
- Table 1 lists Chinese investment in the Brazilian soy chain totalling **US$6.04bn**, of which COFCO is 2.7bn and ChemChina 1.1bn (p.11).
- Land acquisitions were blocked by Brazil's 5,000 ha cap on foreign land purchases (p.12).
- COFCO in Latin America has 40 warehouses, 8 processing units and 8 ports. In Brazil it processes 1.4 Mt/yr, 70% of it in Mato Grosso (p.12).
- Chinese port investments:
  - **China Merchants Ports bought Paranaguá (TCP) for 925m (2017)**.
  - CCCC: US$240m at São Luís, and US$514m at the Babitonga terminal with a partner fund.
  - Hopefull: 120m terminal at São Francisco do Sul.
  - Together these give Chinese firms four major grain export points (p.13).

**3. What Nexus needs.**
- **Market-structure KB entities:** Chinese-controlled Brazilian export terminals (TCP Paranaguá/CMPorts; São Luís/CCCC; Babitonga; Hopefull SFS). The repo has only a generic "Santos/Paranaguá" port term (entities.yaml TERM-101).
- No time series.

**4. Rationale.** Background for the market-structure KB (origins BR → Korea). Paranaguá is a major soy-complex export port, so Chinese terminal control is a geopolitical node for P1-02's chokepoint thinking.

**5. Priority / class.** **Background · Cite-with-caution.**
- **SBO relevance: inference only.** The paper is about beans and investment.

**6. Caveats.**
- Qualitative; investment totals are compiled from three databases the author admits are contradictory (p.11).
- Numbers conflict with Fares. Tixiliski has **Noble Agri US$1.2bn and Nidera US$1.5bn (p.12)**. Fares has **US$1.5bn for 51% of Noble Agri plus US$750m for the remaining 49% (p.16–17/492–493)**.
- The "1.4 Mt/yr processing in Brazil" figure looks low against COFCO's own disclosures. Mark it `[UNVERIFIED-SINGLE-SOURCE]`.

**7. Ontology candidates.**
- Entity additions only, no causal edge: `PORT-PARANAGUA-TCP` (operator CMPorts, acquired 2017, p.13) and `PORT-SAOLUIS` (CCCC, p.13), linked to the COFCO/CN-SOE nodes.

**Lens discussion.**
- **P1-02:** Most interested of the three lenses. Chinese ownership of Brazilian export terminals is a latent leverage point, for example berth priority for China-bound cargo in congestion. There is no evidence of that behaviour in the paper, so it stays INFERENCE.
- **C-02:** Weak empirics; use it only to seed entity records, and verify against CMPorts and COFCO filings.
- **P1-03:** Not relevant.
- **Joint conclusion:** Background; use it for entities.yaml seeds after verification.

---

## 4. Figueira & Galache — Comparative competitiveness of soybean exports, BR/US/AR (CMS)

**1. Citation.** Rev. Economia e Sociologia Rural 61(1): e245403, 2023, DOI 10.1590/1806-9479.2021.245403. Data **2002–2017**, split into two periods, 2002–08 and 2009–17. Sources: FAOSTAT, SECEX, USDA GATS, MAGyP, INDEC.

**2. Core findings.**
- BR, US and AR together held **80.6% of world bean production and 87.9% of bean exports** over 2002–17 (p.2).
- Exports as a share of production:
  - Brazil: 37.93% → 59.49% (p.2)
  - USA: 36.57% → 46.34% (p.2)
  - **Argentina: 20.54% → 13.46%**, because it crushes at home (p.2)
- Argentina crushed **74.1% of its 2017 crop** (40.73 Mt; CONAB) (p.14).
- World bean imports rose from 56.8 to 148.3 Mt; **China's from 13.9 to 98.1 Mt** (+605.7%) (p.8).
- Brazil's share of China's imports rose from **29% to 44%** between the two periods (p.10, p.15).
- CMS decomposition (Table 2, p.12): the **competitiveness effect was +86.07 Mt for Brazil, −26.5 for the US and −98.19 for Argentina**.
- China's **tariff escalation** (lower import duty on beans than on meal and oil) plus Kandir favoured bean exports and hurt Brazilian meal and oil exports (p.13).
- The US has lower internal transport costs than BR/AR, and the gap widens with distance to port (p.14).
- Citing Rhoden et al. 2020 (p.14):
  - **Argentina ≈ 45% of world SBO exports**.
  - SBO export growth: AR +2.27%/yr, US +1.84%/yr, **BR −1.41%/yr (1998/99–2017/18)**.
- The authors warn explicitly that the bean result "should not be extended" to meal and oil (p.1, p.14).

**3. What Nexus needs.**
- **Argentina SBO export share and crush allocation** (PSD AR crush, SBO exports: collected). It is a key Korea origin.
- **China tariff structure, beans vs SBO** (MOFCOM schedule): a static policy fact, entered manually.

**4. Rationale.** Background for **G1 structural factors**. It explains why Korea's SBO origin mix is AR/US-heavy. Argentina's dominance means AR policy (export tax, CE-003) and AR weather are first-order for Korea CIF.

**5. Priority / class.** **Background · Cite-with-caution.**
- **SBO relevance: beans only**, by the authors' own statement. The SBO facts are second-hand (Rhoden).

**6. Caveats.**
- Internal inconsistencies:
  - Argentina's share of China's imports is **24%→10% on p.10 but 32%→10% on p.15**.
  - Argentina's world share is **12%→6% on p.11 but 14%→8% on p.15**.
  - China's 2002 imports are **13.9 Mt on p.8 but 23 Mt on p.15**.
- CMS is an accounting identity, not causal.
- The data end in 2017, before the trade war.

**7. Ontology candidates.**
- New candidate for P1-06 review: "**China tariff escalation (beans < SBO duty) → China crushes imported beans domestically → structurally low Chinese SBO imports / potential SBO surplus → Asian SBO balance looser → Korea CIF ↓ (long-run)**". Evidence: p.13; RCA paper p.11; Fares p.5/481. This is a low-frequency structural edge with a lag of quarters to years.

**Lens discussion.**
- **C-02:** Useful only for its Argentina-centric SBO facts and the tariff-escalation mechanism.
- **P1-02:** The tariff-escalation point matters for scenarios. If China cut SBO duty, or Argentina's export-tax differential (DET) narrowed, oil flows would shift.
- **P1-03:** The fact that Argentina holds about 45% of world SBO exports raises the weight of the AR Córdoba alert threshold in P1-03's table. A Pampas drought is an SBO-specific shock more than a bean shock.
- **Joint conclusion:** Background. Cite only the Argentina SBO concentration fact, and cite it with a secondary-source tag.

---

## 5. Ribeiro & da Silva Filho — Determinants of international trade in Brazilian soybeans and derivatives (CMS)

**1. Citation.** Contaduría y Administración 69(3):271–297, 2024, DOI 10.22201/fca.24488410e.2024.4863. Data **2000–2019**, UN Comtrade and ComexStat, in four sub-periods.

**2. Core findings.**
- Table 3 (p.13) gives destination growth of Brazilian SBO exports. Key markets are India, Iran (shown as "Will" in the table, an extraction or translation artifact; the text says Iran −100% in 2016/19), China, Bangladesh and Peru.
  - China: **+2219% (2000/04), then −84.96% (2012/15)**.
- Brazil's mandatory biodiesel blend went from **2% to 10% (2008–2018)**, reducing the oil share exported (p.13).
- CMS for SBO (Table 6, p.16): the world-growth effect is about 100–102% in every sub-period. The distribution and competitiveness effects swing between **−701,546 and +701,546** (2005/11). Meal (Table 7) reaches **±5,978,339%**.
- Aggregate soy complex (Table 8, p.17): world-growth effect 97.8–120.7%; competitiveness negative in three of the four sub-periods.
- EU tariffs on SBO (p.19): crude **3.8% (industrial) / 7.6%**; refined **6.1% / 11.4%**.
- From the literature: SBO export volumes are more sensitive to exchange-rate shocks than beans or meal (p.6).

**3. What Nexus needs.**
- **Brazil SBO exports by destination** (ComexStat monthly NCM 1507; **not collected**). This shows whether Brazilian oil competes for the South Asian demand (India, Bangladesh) that also prices Korean cargoes.
- **Brazil blend % series** (same as §1).

**4. Rationale.** It identifies who absorbs Brazil's SBO surplus. India's demand pull is a competing-buyer signal for Korea.

**5. Priority / class.** **Background · Counter-example (method).**
- **SBO relevance: direct** (it covers 1507), but the CMS results are numerically degenerate. Effects of hundreds of thousands of percent come from near-zero denominators. **Do not cite any CMS effect value.** Only the descriptive destination facts and the policy facts are usable.

**6. Caveats.**
- Degenerate decomposition.
- A table label is mistranslated ("Will").
- Value data only, no volumes.
- It ends in 2019.

**7. Ontology candidates.**
- **CE-023 evidence:** "blend 2%→10% (2008–2018) reduced the export share" (p.13).
- **CE-021 nuance:** "SBO exports are more FX-sensitive than beans" (p.6, literature claim). Grade: weak.

**Lens discussion.**
- **C-02:** A counter-example worth logging, in the same spirit as the repo's VMD-leakage paper (ApplSci 2025). Mechanical CMS on small or volatile flows gives meaningless shares.
- **P1-02:** The EU tariff schedule and Mercosur–EU agreement are relevant if that deal enters into force, because it could redirect Mercosur SBO towards the EU (p.19).
- **P1-03:** No climate content.
- **Joint conclusion:** Counter-example for method; keep two facts (the blend path and the SBO destination mix).

---

## 6. Wang, Liu, Wang & Li — Structural evolution of the global soybean trade network and implications for China

**1. Citation.** Foods 12(7):1550, 2023, DOI 10.3390/foods12071550. FAOSTAT Detailed Trade Matrix, HS1201, importer-reported; years **2000, 2005, 2010, 2015, 2020** (p.5).

**2. Core findings.**
- World bean trade grew from **48.1 to 165.0 Mt** (2000–2020), 6.4%/yr.
- Network size grew from **123 to 161 nodes and 660 to 1,010 edges** (Table 2, p.5).
- The network is small-world and scale-free (p.5–6). Its communities went from two to four (p.8).
- **China's closeness-centrality rank fell from 16th to 71st** (2000→2020), which the authors read as declining "anti-interference ability" (p.10).
- US share of China's imports: **52.0% (2000) → 35.1% (2013) → 18.9% (2018)**.
- Brazil: **64.3 Mt = 64.2% of China's 2020 imports** (p.10, p.12).
- BR+US+AR are **over 95% of China's imports** (p.10). The US and Brazil alone are over 85% (p.13).
- Targeted-removal scenarios on 2020 (Table 3, p.12):
  - Network efficiency is 0.302 at baseline, 0.305 with Brazil removed, **0.290 with the US removed** and 0.286 with both removed. The US carries network robustness.
  - China's closeness drops from 0.393 to about 0.37 under each removal.
- Russia supplied China **693 kt in 2020 (63% of Russian exports)** (p.14).
- China's 2019 soybean profit was **−1.48 RMB/kg** (p.14).

**3. What Nexus needs.**
- **Korea SBO import origin concentration:** HHI and top-2 share by month, built from Korea Customs 150710/150790 by country (**collected**). This is the Korea analogue of the paper's dependence analysis. It is cheap and directly relevant to G1/G3.
- **Global SBO trade matrix** (BACI or Comtrade HS1507, annual) to measure exporter concentration of SBO, not beans. Not collected. BACI is a free download.
- **2018 US–China tariff episode** as a dated G1 analogue window.

**4. Rationale.**
- **G1:** origin concentration is a structural factor of exactly the kind README §QR asks for, and it changes slowly enough to be an alert-board item.
- **G3:** origin-split P&L needs to know how concentrated Korea's actual sourcing is.

**5. Priority / class.** **Should · Adopt** (method and the 2018 analogue facts).
- **SBO relevance: beans.** Transfer is by method: apply the same dependence logic to Korea's SBO HS lines.

**6. Caveats.**
- Five snapshot years only.
- The "closeness = anti-interference" reading is the authors' interpretation.
- Node removal is a topological thought experiment with no prices or substitution.
- Per the repo's TGL 2023 precedent, network metrics should not be used as forecasting features. Use them as descriptors.

**7. Ontology candidates.**
- **CE-011 evidence:** "US share of China's imports 52.0%→35.1%→18.9% (2000/2013/2018) — tariff-driven reallocation to Brazil and Argentina" (p.12).
- Non-causal note for `non_causal_correlations` or methods: "Trade-network centrality is a structural descriptor, not a price driver (TGL 2023 precedent)."

**Lens discussion.**
- **P1-02:** The removal test is a clean way to talk about chokepoint and embargo risk. P1-02 wants a Korea version: what if the AR or US SBO channel is cut?
- **C-02:** Agrees. Implement it as simple shares and HHI on customs data, not as graph models.
- **P1-03:** The removal scenario is effectively a "Brazil drought" shock. Under compound risk (climate plus China concentration), China's demand shift onto the US is the price-transmission path to CBOT.
- **Joint conclusion:** Adopt the concentration and dependence indicators for Korea SBO, and the 2018 analogue.

---

## 7. Liu, Zhang, Failler & Wang — Dynamic evolution of agricultural trade network structures (global soybean, TERGM)

**1. Citation.** Systems 13(4):279, 2025, DOI 10.3390/systems13040279. CEPII-BACI HS120100, **2000–2022**. The paper says 126 economies (p.10) but builds a backbone of 77 economies with the top three dependency edges each (p.7). Statistics are computed every two years.

**2. Core findings.**
- **Trade-dependency (irreplaceability) index:** Bimtd_ij = R_ij²·(C_ri/C_pj), using standardized-HHI concentrations (eq. 1–2, p.7).
- Edges rose from **935 to 1,657**; density from 0.023 to 0.030 (Table 1, p.11).
- **In-degree (import) centralisation rose from 0.0144 to 0.0230, while out-degree (export) centralisation fell from 0.0410 to 0.0116.** Importers are concentrating and exporters dispersing (p.11).
- Mean dependency fell from 0.1721 to 0.1588, i.e. more substitutability (p.11).
- The core went from single-core to multi-core (p.14).
- Core coefficients (Table 2, p.15): USA 0.74–0.80, BRA 0.22–0.38, CHN rising to about 0.20–0.24. **Korea is semi-peripheral: 0.097 (2002), 0.134 (2007), 0.113 (2017), 0.119 (2018). Vietnam: 0.103 (2017), 0.102 (2022).**
- 2018 trade war: **US total bean exports −16.2%, to China −72.7%** vs 2017. US core status rose as it re-routed to Egypt, the Netherlands, Germany and Mexico (p.16).
- 2020: Argentine drought gave **−7% production and −33% bean exports** (BCBA); Brazil's exports rose **8.8%** on a bumper crop and currency depreciation (p.17).
- TERGM (Table 4, p.21; robustness Table 5, p.23):
  - **Stability 1.527 (p<0.001), i.e. strong path dependence** (p.22).
  - Reciprocity is positive.
  - Distance is negative and contiguity positive (+1.18 in model 4).
  - GDP is a positive sender and receiver effect.

**3. What Nexus needs.**
- **The dependency index (eq. 1), applied to Korea × origin for SBO HS lines**, using customs data (collected). It complements HHI by capturing how replaceable each origin is.
- **Event calendar entries** with dates: 2018 tariff (CE-011), 2020 AR drought (CE-006/009 family), 2020 BRL depreciation (CE-021).

**4. Rationale.**
- **G1 analogue reference:** 2018 and 2020 are documented regime episodes with quantified trade effects.
- The **path-dependence result (stability 1.53) supports Nexus's persistence-baseline doctrine** (C-014 §4 / TGL 2023): trade links are sticky, so "last value" is a strong baseline for origin shares.

**5. Priority / class.** **Should · Adopt (partial):** the dependency index, the event facts and the persistence support. Core–periphery mapping is Background.
- **SBO relevance: beans.** Transfer by method.

**6. Caveats.**
- Sample inconsistencies (77 vs 126 economies; about 165 backbone edges vs 935–1,657 in Table 1).
- The "Big Four short-selling Chinese soybeans (2003)" event (p.15) is a contested narrative. Cite with caution.
- TERGM explains edge formation, not prices.
- One unit error: China's 2022 imports are called "58.3% of the world's total soybean exports" (p.16).

**7. Ontology candidates.**
- **CE-011 evidence:** "2018: US exports to China −72.7%, total −16.2%; US re-routes to other buyers" (p.16).
- **CE-021 evidence:** "2020 BRL depreciation plus bumper crop → BR exports +8.8%" (p.17).
- New candidate: "**AR drought → AR bean exports −33% (2020) [crush and SBO exports also at risk] → AR SBO export availability ↓ → Korea CIF (AR channel) ↑**" (p.17 for beans). The SBO leg is INFERENCE and should be checked against PSD AR SBO 2020/21.

**Lens discussion.**
- **P1-02:** The 2018 episode shows US export *rerouting*. That matters for Korea: US product pushed out of China can become available to Korea at a discount (the CE-011 DOWN direction).
- **P1-03:** The 2020 Argentine drought numbers are a usable analogue. P1-03 wants them cross-checked with ERA5 soil moisture for AR Córdoba (already collected) to calibrate the alert threshold.
- **C-02:** Adopt the dependency index; treat the core-coefficient tables as descriptive colour only.
- **Joint conclusion:** Adopt the index and the event analogues; Background for TERGM structure.

---

## 8. Ali, Zhou, Cleary & Xie — The impact of climate change on China and Brazil's soybean trade

**1. Citation.** Land 11(12):2286, 2022, DOI 10.3390/land11122286. Historical FAOSTAT 1995–2020. Climate projections: ISI-MIP (CMIP5, five GCMs × two crop models, RCP2.6/8.5, no CO₂ fertilization), 2030 (average of 2020–39) vs 2011. Economic model: GTAP v9 recursive-dynamic.

**2. Core findings.**

*Trade structure*
- China takes about **64%** of its soybeans from Brazil; about **73%** of Brazil's soybean exports go to China (p.1).
- China's share of Brazilian exports peaked at **82.5% in 2018** (p.5).
- Brazil's exports rose from **3.48 to 82.95 Mt (1995–2020)**, and its global export share from **11.6% to 48.2%** (p.4).
- Exports as a share of Brazilian production: **20% (1990) → 65% (2019)** (p.11).

*Climate and model results*
- Projected Brazil yield change, 2030 (Table 1, p.6):

  | Statistic | RCP2.6 | RCP8.5 |
  |---|---|---|
  | Mean | −1.51% | −2.47% |
  | Median | −3.03% | −7.94% |
  | Minimum | −16.05% | **−17.66%** |
  | Maximum | +16.39% | +39.29% |

- In the extreme RCP8.5 case (Table 2, p.8):
  - Brazilian production **−13.06% (−19.3 Mt)** and exports **−15.25% (−13.0 Mt)**.
  - China's imports −9.94 Mt, imports from Brazil −14.2%, and Chinese soybean price only **+0.24%**.
  - Chinese welfare **−US$4.53bn** (p.9–10).
- China's virtual land imports from Brazil reached **19.63 Mha in 2020**, against Brazil's 37.19 Mha harvested area (p.1, p.11).

**3. What Nexus needs.**
- **Brazil yield-shock distribution** as a reference for G2 tail and stress scenarios. ISI-MIP data are free, but the right Nexus input is the **in-season** anomaly: Open-Meteo ERA5-Land for Mato Grosso, RS and others (collected), plus ONI (collected), plus Embrapa loss history (already in the repo).
- **China import share from Brazil**, monthly (GACC; not collected), to monitor the compound "BR shock → China turns to US" channel.

**4. Rationale.**
- **G2/G3 stress scenarios:** a −15% Brazil export tail is a plausible upper-tail supply scenario for the 60-day band and regime probabilities.
- **G1:** background for the BR weather → China → CBOT transmission story.

**5. Priority / class.** **Background · Cite-with-caution.**
- **SBO relevance: beans.** GTAP has a vegetable-oils sector, but no SBO results are reported. Any SBO price effect is inference.

**6. Caveats.**
- Only two RCPs. CMIP5 is outdated vs CMIP6. No CO₂ fertilization.
- **China's imports from other origins are held fixed** (p.8), which suppresses substitution. The tiny +0.24% price effect is therefore a model artifact, not evidence of low price sensitivity.
- The 2030 horizon is useless for 1–60-day forecasting.
- Internal inconsistency in virtual land: 3.57 Mha (2005) in the abstract (p.1) vs 15.5 Mha (2005) and 6.31 Mha (2010) in the text (p.11). Likely a typo.

**7. Ontology candidates.**
- **CE-009 (BR_HARVEST_WEATHER_SHOCK) context evidence:** "extreme yield shock −17.66% → exports −15.25%; the pass-through ratio of production to yield is about 0.74 because farmers adapt" (p.8). Grade: model-based, background.
- No new edge. The price magnitude must not be cited.

**Lens discussion.**
- **P1-03:** Rejects this as a forecasting input: wrong horizon, outdated scenarios, area-weighted national yield that hides the RS-vs-centre-west contrast Embrapa documents. Acceptable only as a long-run backdrop and as a sanity bound for tail scenarios.
- **P1-02:** Sees value in the **compound-risk framing**. With China 60–80% dependent on Brazil, a Brazilian weather shock becomes a geopolitical demand shock on the US crop, which is exactly when US–China tariff politics bite.
- **C-02:** Background; cite the trade-structure facts (64% / 73% / 82.5%), not the CGE magnitudes.
- **Joint conclusion:** Background, cite with caution. Use only the tail-yield range as a stress-scenario reference, and use in-season ERA5 data for anything operational.

---

## (a) Ranked top-10 concrete items

| # | Item | Source / Nexus status | Goal | Priority | One-line rationale |
|---|---|---|---|---|---|
| 1 | **Korea SBO import origin shares, HHI and dependency index** (monthly; 150710/150790 × country; TERGM eq.1) | Korea Customs: **collected**, derive only | G1, G3 | **Must** | Cheapest high-value structural indicator: it measures how exposed Korea's SBO supply is to one channel (Structural Evolution p.10–13; TERGM p.7). |
| 2 | **Brazil SBO monthly exports by destination** (ComexStat NCM 1507.10/1507.90) | Free; **not collected** (needs egress approval) | G1, CE-023 | **Must** | Brazil's exportable SBO surplus is the swing variable behind CE-023 (RCA p.13; Determinants p.13). |
| 3 | **Brazil biodiesel blend % series with effective dates** (ANP/CNPE) | Free; only a news indicator today | G1, CE-023 | Should | Turns CE-023 from a news trigger into a numeric dated policy variable; RCA p.13 shows both directions (2008 ↓ exports, 2020 ↑). |
| 4 | **US SBO export share of world SBO exports** (RCA proxy) | GATS + PSD: **collected**, derive only | G1, CE-022 | Should | Direct tracker of the "US SBO goes domestic" mechanism; US SBO RCA < 1 since 2021 (RCA p.13). |
| 5 | **Argentina SBO export share and crush allocation** | PSD **collected**; BCBA/BCR partly | G1, G2 | Should | Argentina is about 45% of world SBO exports (Comparative p.14, secondary); its 2020 drought cut bean exports 33% (TERGM p.17). That makes AR the first-order SBO origin risk for Korea. |
| 6 | **China channel separation: SOE vs commercial; China SBO net trade** | PSD China rows collected; GACC not collected | Semantic, CE-011/012 | Should | COFCO sends 41% of its South American exports to non-China buyers (Fares p.13/489) and China has crush over-capacity (p.5/481), so Chinese buying ≠ state demand and China can become an SBO exporter. |
| 7 | **2018 US–China tariff episode as a G1 analogue window**, with dated event dummies | Event calendar exists (`market_event_calendar.yaml`) | G1, CE-011 | Should | Quantified: US share of China's imports 52%→18.9% (Structural p.12), US exports to China −72.7%, total −16.2% (TERGM p.16). |
| 8 | **Brazil logistics-disruption events** (2018 trucker strike) as analogue and candidate edge | Event calendar; no connector needed | G1, G3 | Should | Documented export delays and lost importer confidence (RCA p.11–12). It is a non-weather Brazilian supply shock missing from the CE list. |
| 9 | **Brazil yield-shock tail range for G2/G3 stress scenarios** (ISI-MIP min −16 to −18%; production/yield pass-through about 0.74) | ISI-MIP free; operational input = ERA5-Land BR + ONI (**collected**) | G2, G3 | Background | Gives a literature-anchored bound for the upper-tail supply scenario (Climate p.6, p.8), but it must not be used as a feature. |
| 10 | **Market-structure KB entities: Chinese-controlled Brazilian export terminals and COFCO/CIL ownership** | entities.yaml has only a generic Santos/Paranaguá term | Semantic / KB | Background | TCP Paranaguá (CMPorts, 925m, 2017), São Luís/Babitonga (CCCC) (Tixiliski p.13); CIL shareholders (Fares p.14/490). These are P1-02 leverage nodes on the BR→Asia route. |

## (b) Disagreements among the lenses

1. **What network metrics are for.** P1-02 reads centrality and closeness as geopolitical leverage and embargo exposure. C-02 and P1-03, following the repo's TGL 2023 precedent (persistence beats GNNs), allow them only as **descriptors**, never as G2 features. **Resolution:** compute simple shares, HHI and the dependency index on customs data. No graph models.
2. **The China narrative.** P1-02 leans to the state-strategic reading (Tixiliski; the SOE purchases in the 2025–26 vintage). C-02 leans to Fares's financialization reading. **Resolution:** keep both channels explicit (the A-219 rule). Never infer state stockpiling from aggregate Chinese buying.
3. **The climate–trade paper.** P1-03 rejects it as an input (2030 horizon, CMIP5, no CO₂, fixed other-origin imports). P1-02 values its compound-risk framing. C-02 keeps only the trade-structure facts. **Resolution:** Background; tail range used for stress scenarios only.
4. **RCA and CMS papers.** C-02 wants RCA as a structural indicator. P1-03 notes it is annual and value-based, so it cannot inform 1–60-day horizons. **Agreed:** the Determinants CMS values are degenerate (a counter-example).
5. **Direction of CE-023.** The RCA paper supports "mandate ↑ → exports ↓" (2008) and "mandate ↓ → exports ↑" (2020). The repo's own 2026 evidence (Argus: exports rose under B15) shows the effect is conditional on crush growth. **Resolution:** keep the edge as a candidate with a crush-growth condition, and measure it with items #2 and #3.
6. **Weight of Argentina vs Brazil in Korea risk.** P1-03 would raise AR Córdoba alert weight because of SBO concentration. C-02 warns that the 45% figure is second-hand (Rhoden via Figueira p.14) and must be re-verified with PSD before reweighting.

## (c) Items needing paid data or approval

| Item | Why |
|---|---|
| New egress domains: comexstat.mdic.gov.br (BR exports), cepii.fr (BACI), GACC (China customs), ANP/CNPE (blend schedule) | All free, but each needs egress or allow-list approval and as-of registration (`available_at`). |
| UN Comtrade at scale (multi-reporter HS1507 matrix) | Free preview is capped at 500 records per call; bulk needs a subscription key (premium is paid). BACI is the free alternative, with an annual lag. |
| Chinese crush and ownership data behind Fares (BRIC Agri, Qichacha, Cofeed) | Paid or Chinese-registration databases. Do not try to replicate; cite as published. |
| GTAP database (to reproduce the climate–trade CGE) | Paid licence. Not recommended. |
| Vessel-level origin flows (Kpler/Vortexa) to check Korea origin shares below monthly totals | Paid, already pending as a data gap (C-02 Data Gaps). |
| Ontology changes (new candidate edges: China tariff escalation → SBO surplus; BR logistics disruption; AR drought → SBO availability) and all evidence additions to CE-011/021/022/023 | Need **P1-06 domain validation** under S-1. Everything in this report is candidate status only. |
| Replacing the repo's Fares PDF with the new copy, and filling its skeleton summary | Approver decision (reference-archive policy). |


---

# Project Nexus — Review of 7 Supply-Chain / Processing Papers (Structure batch)

Reviewer lenses: **P1-04 Supply Chain & Logistics Analyst** (CFR optimisation, chokepoint/freight, ABCD supplier monitoring, Brazil–US CFR spread alert >USD 20/MT, lead times) and **C-04 Document Intelligence** (extraction fidelity, provenance/EvidenceSpan, unit normalisation, no imputation, D-021 external-only, SBO scope lock, source grade).
Date: 2026-11-17. Inputs: extracted .txt in `scratchpad/pdftext/structure/` (7 files only). Repo read-only. No files under `docker/` and no `.mcp.json` were opened.

Page locators = **PDF page** (the `--- page N ---` markers), plus table/figure IDs. Where the journal's printed page differs this is noted. Numbers marked *(derived)* are my arithmetic, not the paper's.

## 0. Repo context checked (overlap and gaps)

| Topic | What Nexus already has (file) | Overlap with this batch |
|---|---|---|
| Crude SBO specs | NOPA crude degummed **FFA max 0.75%, P max 0.02% (=200 ppm)**; FOSFA 51 FFA max 1% (`docs/research_desk/2026-08/competitive_differentiation_2026_08_14.md` §3b) | Flores et al. gives the **first measured origin values** to compare against these limits |
| "Brazilian crude has higher FFA/P" | Stated without a measured source (`extraction_technology_by_country_2026_08_25.md` §핵심 결론) | Flores et al. quantifies it (but for beans crushed at destination) |
| Extraction technology / oil yield | Extraction report (solvent standard, 99% yield); farmdoc RD-boom P1–P3 (oil yield ~20%, oil share of crush value 35–50%) | Cravotto et al. largely overlaps; new items are limited to cost, capex, residual oil and hexane regulation |
| AR export tax | CE-003 (validated), Decreto 423/2026 schedule (beans 24%→15%, crude SBO/meal 22.5%→14%, refined 13.5%); indicator only `ARG_EXPORT_TAX_SENTIMENT` (`src/semantic/metrics.yaml`) | Haro Sly adds historical step events (2008, 2015) usable as G1 analogue dates; no **rate time series** exists in Nexus |
| BR biodiesel | CE-023 candidate (B15→B16), indicator `BIODIESEL_MANDATE_NEWS` only | Alves et al. adds domestic-absorption shares and blend history (B2→B12) |
| Concentration | `ontology.yaml` concentration block: shipment CR4 (AEPP 2025), BR trading shares 2020 (Transparency 2021) | Haro Sly adds AR **crush-capacity** concentration (different basis) |
| Routes | RT-USG-KR (Panama), RT-SANTOS-KR, RT-ROSARIO-KR (Malacca), RT-CN-KR; no Arco Norte | Aguiar adds Arco Norte→Panama→Asia as a route class (mostly beans) |
| Free BR/AR price/flow sources | CEPEA crude SBO and AR MAGyP official FOB listed as **unimplemented** free alternatives (`docs/research_desk/2026-09/free_alternatives_inventory_2026_09_14.md` §5). No connector in `src/pipeline/connectors/` for CEPEA, ABIOVE, ANP, ANTAQ, Comex Stat, CIARA, BCR | Alves et al. (the CEPEA team) supports implementing CEPEA |
| Japanese trading houses | Not in `entities.yaml`/`ontology.yaml` (no Mitsui/Mitsubishi/Sojitz/Marubeni) | Miranda covers them |

None of the 7 papers is already cited in `docs/` or `src/` (grep on author names/DOIs returned nothing).

---

## Paper 1 — Aguiar, "A 'Guerra das Rotas' da soja" (Portuguese)

**1. Citation.** Diana Aguiar (UFBA). *Estudos Sociedade e Agricultura* 32(2), e2432206, published 20 Dec 2024, DOI 10.36920/esa32-2_st02 (p.1, p.32). Data: USDA PSD and Comex Stat 2001–2021, ANTAQ 2010–2020, fieldwork 2014–2019 in western Pará, Bahia and Maranhão (p.6, p.8, p.16). Method: political-economy and qualitative (documents, field notes, news alerts).

**2. Core findings (translated).**
- World soy trade (beans plus processed) grew **145%** from 2001 to 2021, reaching **223 Mt in 2020/21**. Brazil supplied **58%** of the increase, and its share of world trade rose from **28% to 45%** (p.8).
- The EU took **68%** of Brazilian soy exports in 2001. China took **58.6%** in 2021 (p.8).
- As soy moved north ("tropicalisation"), production areas got further from Santos and Paranaguá. New Arco Norte routes go to northern Atlantic ports and then **through the Panama Canal to China** (p.8, p.10).
- Port throughput growth 2014–2020: Itaituba **+990%**, São Luís **+714%**, Santarém **+440%**, against Santos **+77%** and Paranaguá **+96%** (p.11).
- Route expansion was driven by traders building private ports ahead of public works, using existing roads. Cargill opened Santarém in **2003**, before BR-163 paving. Amaggi started Itacoatiara in **1997** (p.15). A dispute over paving the last **172 km** of BR-163 to Santarém was framed as an attempt to isolate Cargill's port (p.17).
- Priority logistics projects have been "basically the same" in PAC, PIL and PPI for 20 years. Many never left paper or have dragged on for years, giving "low predictability" (p.6). Rail projects largely stalled, and trucks on poor roads remain dominant (p.15).
- A Rabobank note (2016) is quoted: marginal gains from new ports are quickly erased by the extra production they induce, causing new saturation (p.23).
- Brazil ranked **56th** in the World Bank LPI in 2018 (p.24).

**3. What Nexus needs from it.** Route structure, not numbers: (a) an **Arco Norte → Panama → Asia** corridor class next to the existing Santos/Rosario → Malacca routes; (b) a rule that **infrastructure announcements are not capacity**, in the same family as DJVE≠shipment and capacity≠throughput; (c) port-level throughput by cargo type. Free sources: **ANTAQ Estatístico Aquaviário** (port × cargo, monthly) and **Comex Stat** (HS 1507 by port of exit and destination). Nexus has neither connector. Panama is already monitored through `AIS_PANAMA_*`.

**4. Rationale.** Panama restrictions (for example a drought draft limit) currently affect only RT-USG-KR in the ontology. If Brazilian cargo to Asia increasingly transits Panama, Panama risk also touches the BR channel and Brazil's bean/oil FOB spreads. This matters for G3 origin choice and route lead time, and for the P1-04 chokepoint alert. It does not touch G2 (CBOT).

**5. Priority / classification.** **Should (low)** / **Background**. The Rabobank saturation point is a **Counter-example** to any naive "port build → lower freight → lower FOB" edge. Beans vs oil: the paper's port and route numbers are about the "complexo soja", essentially grain terminals. It gives **no evidence that crude SBO tankers load at Arco Norte ports**. Brazil's SBO export terminals are not discussed.

**6. Caveats.** Critical-geography essay with an advocacy stance. Gráfico 1 values (p.16) cannot be read from the extracted text. Port growth percentages are cited without a cargo breakdown.

**Lens views.**
- *P1-04:* wants an `RT-ARCONORTE-ASIA` route candidate with `transits: [WP-PANAMA]` and the AIS Panama alert linked to the BR channel. Treats the "announcement ≠ capacity" rule as useful for news triage of Ferrogrão/FICO headlines.
- *C-04:* the paper has no SBO-specific data, and the port figures are aggregates without a cargo field. A route needs an SBO-specific EvidenceSpan (ANTAQ cargo = "óleo de soja") before registration. The Portuguese quotes are translated here, and the exact-quote field should keep the original text.
- *Joint conclusion:* register only as a **candidate route with a DATA GAP flag** until ANTAQ or Comex Stat shows HS 1507 loadings at northern ports. Adopt the interpretation rule now (cost-free).

**7. Ontology candidates.**
- `CAND-R1` PANAMA_TRANSIT_RESTRICTION → Arco Norte cargo to Asia rerouted or delayed → BR-origin freight and lead time ↑ → Korea CIF (BR channel) **UP, small**. Evidence: p.10 (route), p.11 (northern port growth). Status: candidate, beans-dominant, DATA GAP for SBO.
- Interpretation rule (not an edge): "Logistics project listed in PAC/PIL/PPI ≠ capacity in service" (p.6, p.15). Counter-example note on port saturation (p.23).

---

## Paper 2 — Miranda, "Agronegócio da soja no Cerrado: empresarização e transnacionalização" (Portuguese)

**1. Citation.** Roberto de Sousa Miranda (UFAPE). *Ágora* (Santa Cruz do Sul) 27(1), 2025, DOI 10.17058/agora.v27i1.20444 (p.1). Received June 2025. Data: Balsas (south Maranhão) 1977–2024. Sources are IBGE SIDRA (to 2022/2024), regional press, municipal records and semi-structured interviews with pioneer and PRODECER farmers (p.4–5). C-04 note: the header says pp. 192–214 but the printed page numbers are 114–128, so the citation pagination is inconsistent.

**2. Core findings (translated).**
- Soy area in Balsas: **7,113 ha (1988) → 34,820 (1998) → 110,505 (2008) → 209,081 ha (2018)** (p.3).
- Maranhão state averages: 1980s area **9,560 ha** and output **14,849 t**; 2011–2022 area **967,997 ha** and output **≈2.78 Mt** (p.12).
- The federal Northern Export Corridor (1990) and the Carajás and Norte-Sul railways drove expansion. The first soy ship left São Luís for Spain on **7 Jul 1992** (p.8–9).
- PRODECER (Japan–Brazil) colonists each received **483 ha** and **US$1.2 M**, with a collective **~70,000 t** silo (p.10). The cooperative collapsed in the 2000s because colonists sold directly to the traders that financed them (**Bunge, Cargill, Ceagro, Multigrain**) (p.11).
- Bunge (which bought CEVAL in 1997) did not build a crusher in Balsas because it could not get tax exemptions. It went to Piauí instead (p.13). Cargill opened a receiving unit in Balsas in **1996**. Algar Agro crushes at **Porto Franco**, which is rail-linked to Itaqui (p.13). ADM later bought Algar Agro (p.14, note 8).
- Japanese trading houses: **Mitsubishi** took 20% (2012) and then 60% more (2013) of Ceagro, renamed Agrex. **Mitsui** reached 100% of Multigrain in 2013. **Sojitz** bought **43.13%** of CGG Trading in 2017. CGG's stake in the Itaqui grain terminal went to IG4 Capital in 2020 (p.14). The author reads this as Japan counter-balancing Chinese land acquisition (p.15).
- Traders control production indirectly through crop finance, input sales and offtake (p.15).

**3. What Nexus needs.** Market-structure KB items: (a) **Japanese sogo shosha** as origination and trading actors in Brazil's north-east frontier (MATOPIBA), who compete with Korean buyers for Asia-bound cargo and may also sell to Korea; (b) crush location follows **state tax incentives** (Piauí vs Maranhão), so crush capacity is policy-sensitive; (c) the Itaqui/TEGRAM export corridor. Free sources: company filings (Mitsui, Mitsubishi, Sojitz annual reports), IBGE PAM (area/production), ABIOVE (crush capacity by state). Nexus has none of these entities.

**4. Rationale.** Only the G1/KB "market structure" narrative and supplier mapping (ABCD+) benefit. It has no bearing on G2. It is marginal for G3 (origin alternatives).

**5. Priority / classification.** **Background** / **Cite-with-caution** (ownership facts dated 2012–2020). Beans vs oil: almost entirely about beans and grain handling. The only oil link is Porto Franco crushing (p.13).

**6. Caveats.** Single-municipality case study. Interview-based. Corporate ownership may have changed since 2020 and needs verification against current filings.

**Lens views.**
- *P1-04:* add Mitsui, Mitsubishi and Sojitz as `TradingHouse` entities with "Brazil MATOPIBA origination" footprints. Japanese buyers compete with Korea for Asian destination cargo.
- *C-04:* the paper is a 2025 synthesis of 2012–2020 press reports. Entity registration requires a primary source (company 10-K or annual report) as `source_ref`. Inconsistent pagination means exact-quote anchors must use PDF pages.
- *Joint conclusion:* KB note only. Register entities after primary-source verification. No causal edge.

**7. Ontology candidates.** None causal. KB facts: `CAND-KB1` Japanese trading houses (Mitsubishi/Agrex, Mitsui/Multigrain, Sojitz/CGG) in Brazilian origination (p.14). `CAND-KB2` crush siting follows state tax incentives (p.13). Labels: INFERENCE until verified.

---

## Paper 3 — Khan et al., "Edible Oilseeds: Historical Perspectives, Recent Advances, and Future Directions"

**1. Citation.** Amna Khan, Azmat Ali Awan, Muhammad Yasin, Aasia Ramzan, M. W. A. Cheema, Akhtar Jan (Pakistan Oilseed Department and others). Chapter in *Edible Oilseeds Research – Updates and Prospects*, IntechOpen, © 2024, DOI 10.5772/intechopen.115045 (p.1, p.14). Data: literature review with mixed vintages (2008/09 to 2020). No primary data.

**2. Core findings.**
- Soy ≈ **20%** oil (p.2), **18–23%** oil (p.4). Soy = **69%** of world protein meal (p.2).
- Soy = **57%** of oilseed output (p.4) **vs 61%** in 2020, when 341.76 Mt was produced (p.8). The two figures are inconsistent.
- Production shares: US ≈ **32%**, Brazil **31%**, Argentina **19%**, China **6%**, India **4%** (p.5). Elsewhere the US is given as **38%** (p.9).
- Soy = **80–85%** of oilseed trade volume. Palm oil = **60–70%** of vegetable-oil trade (p.10, with 2008 figures).
- Breeding and CRISPR (FAD2 edits for high oleic) are aimed mainly at Brassica (p.11–13).

**3. What Nexus needs.** Essentially nothing that Nexus lacks. Every number is better sourced from USDA PSD/WMT, which Nexus already ingests. High-oleic soybean is mentioned only generically. The extraction report already notes US high-oleic varieties.

**4. Rationale.** None for G1–G3.

**5. Priority / classification.** **Background — do not cite numbers** (effectively a reject). Not a counter-example, just low-grade.

**6. Caveats.** Internal contradictions (57 vs 61%; 32 vs 38%). An OCR or typesetting artefact "1823% oil" (p.8). An editorial copy-paste artefact, "For this special issue of plants, we are calling for research…" (p.11). Stale 2008 trade data.

**Lens views.**
- *P1-04:* no supply-chain content of value.
- *C-04:* source-grade failure. Add to the "low-grade, do-not-cite" list, like `ML_2025_WCO` in the references README.
- *Joint conclusion:* archive only. Record the honest classification in the references README if it is filed.

**7. Ontology candidates.** None.

---

## Paper 4 — Flores, Pope & Doehring, "Influence of Whole Soybean Composition on Extracted Soybean Oil Composition by Origin"

**1. Citation.** Iván Flores, Micah Pope, Todd Doehring (Centrec Consulting Group). *Journal of the American Oil Chemists' Society* 2026; 103:3–11, DOI 10.1002/aocs.70026. Received May 2025, accepted Sep 2025, open access CC-BY. **Funded by the US Soybean Export Council (USSEC)** (p.1). Data: **304 matched** bean and crude degummed SBO samples (315 per dataset before matching). Samples came from **one crushing facility in an unnamed Asian destination market** that processes US and Brazilian beans separately, over MY 2022/23–2023/24 (p.2; endnotes p.9). PDF p.1–9 = journal pp. 3–11.

**2. Core findings.**
- Beans, Brazil vs US (Table 2, p.3): oil **20.03% vs 19.43%**, moisture **12.20% vs 10.80%**, heat damage **0.37% vs 0.07%**, splits **9.11% vs 11.32%**, protein the same (34.59 vs 34.58, not significant).
- Crude degummed oil, Brazil vs US (Table 3, p.4):
  - **FFA 1.32% vs 0.44%** (Brazil range 0.90–1.70)
  - **NOL (refining loss) 1.50% vs 1.01%**
  - **P 219.93 vs 116.83 ppm** (Brazil max 390.9)
  - Ca 146.75 vs 81.45 ppm; Mg 66.89 vs 35.63 ppm
  - Lovibond red 9.84 vs 10.68
  - Iodine value 127 vs 130
  - All p<0.01. Fe and chlorophyll not significant.
- Pooled regressions (Table 6, p.6): bean **moisture → FFA +0.172** and **NOL +0.163** per pp; **heat damage → FFA +0.175**, **NOL +0.176** (p<0.01). Adjusted R² for FFA = 0.543.
- With origin interactions (Table 7, p.7), adjusted R² for FFA = **0.90**. The same bean defect has different oil effects by origin. For example, moisture has a larger FFA effect for US beans (interaction **+0.116**).
- Authors' warning: samples "are not nationally representative" (Table 3 note p.4; endnotes 1 and 3, p.9).

**3. What Nexus needs.**
- (a) An **origin quality prior** for the landed-cost layer and G3 origin choice: FFA, P and NOL by origin, compared with the NOPA and FOSFA limits Nexus already records. The Brazil sample mean FFA 1.32% is above both NOPA crude degummed (0.75%) and FOSFA 51 (1%). The Brazil mean P of 220 ppm is above NOPA's 0.02% (200 ppm) *(derived comparison)*.
- (b) A **quality-adjusted effective cost**: ΔNOL 0.49 pp × a Brazil customs CIF median of 1,267 $/MT (abcd doc §5) ≈ **USD 6/MT** extra oil loss *(derived, illustrative)*. That is before extra degumming/caustic cost (P, Ca, Mg), which the paper does not price. This is material against P1-04's **USD 20/MT** Brazil–US CFR spread alert.
- (c) A mechanism: harvest moisture and drying heat damage drive FFA. Weather-driven quality risk is separate from yield risk.
- Free sources: the paper's Supplementary Data S1 (Tables S1–S3; download needs approval); USSEC annual US soy quality reports (free, US only). **No free Brazil or Argentina crude-oil quality time series.** Nexus has only spec limits, not origin measurements.

**4. Rationale.**
- **Landed cost:** `landed_cost.py` treats CIF − CBOT as basis + freight + insurance, and the ontology already says the residual includes "quality". This paper is the first quantitative basis for the quality share of origin residual differences.
- **Origin choice and contract spec (G3):** when buying Brazilian crude, specify FFA and P limits and price refining-loss allowances.
- **Domestic crush:** Korean crushers (CJ and Sajo in Incheon) import US and Brazilian beans, so the paper's destination-crush setting is a close analogue for CE-024.

**5. Priority / classification.** **Must** / **Adopt as a documented prior (scenario parameter), Cite-with-caution.** Beans vs oil:
- The oil was extracted at destination from imported beans. It is **not Brazilian-crushed export crude**.
- Moisture and FFA formation during the ocean transit of beans may inflate the Brazil gap compared with oil crushed in Brazil.
- Korea's main crude channel, **Argentina, is not covered at all**.

**6. Caveats.**
- USSEC funding: a US-favourable conflict of interest.
- One plant, two marketing years, not representative.
- The OLS "causal inference" is really fixed-effects association.
- Tables 4–5 are rotated in the PDF and garbled in the text extraction (p.5). Tables 2, 3, 6 and 7 are clean.

**Lens views.**
- *P1-04:* adopt immediately. Add a quality-adjusted Brazil–US CFR spread (spread − ΔNOL×price − degumming allowance) so the >USD 20/MT alert does not fire on spreads that are just quality discounts. Add FFA/P clauses to the G3 "contract spec" alternative.
- *C-04:*
  - Extract only from clean Tables 2, 3, 6 and 7, with page + table + cell provenance. Do not ingest Tables 4–5 from the text layer; re-extract with layout-aware parsing if needed.
  - Units are FFA % (as oleic, AOCS Ca 5a-40) and minerals in ppm (Ca 17a-18), per Table 1 p.2. Tag them with QUDT and do not mix them with the NOPA "%P".
  - The marketing years differ (US Sep–Aug, Brazil Feb–Jan; endnote 2 p.9). No imputation for Argentina.
  - Label INFERENCE when transferring to Brazilian export crude.
- *Joint conclusion:* store the numbers as an EvidenceSpan-backed **parameter prior** in the landed-cost/G3 layer, not as a G2 feature. Validate against Nexus's own customs CIF residuals by origin (US vs BR, same months). Do not extend to Argentina.

**7. Ontology candidates.**
- `CAND-Q1` ORIGIN_CRUDE_QUALITY_GAP (BR higher FFA, P, NOL) → higher refining loss and degumming cost → quality-adjusted effective cost of BR-origin crude **UP** relative to US (Korea effective CIF). Evidence: Table 3 p.4, Table 6 p.6. Status: candidate. Outcome node: `KR_IMPORT_CIF` (effective, quality-adjusted), not `SBO_INTL_PRICE`.
- `CAND-Q2` BR_HARVEST_WEATHER_SHOCK (wet harvest, forced drying) → bean moisture and heat damage ↑ → crude FFA and NOL ↑ → quality discount on BR crude / refining cost ↑ → Korea effective CIF (BR) **UP**. Evidence: Table 6 p.6 (moisture +0.172, heat damage +0.175 on FFA), Table 2 p.3. Corroborated by Cravotto p.3–4. Proposed as a **quality branch of existing CE-009**, not a new price edge.

---

## Paper 5 — Cravotto et al., "Leading Edge Technologies and Perspectives in Industrial Oilseed Extraction"

**1. Citation.** Christian Cravotto, Ombéline Claux, Mickaël Bartier, Anne-Sylvie Fabiano-Tixier, Silvia Tabasso. *Molecules* 2023, 28, 5973, DOI 10.3390/molecules28165973. Published 9 Aug 2023 (p.1). Review with no primary data. **Two authors are affiliated with Pennakem Europa (EcoXtract®)**, the maker of the 2-MeOx solvent the review favours (p.1).

**2. Core findings.**
- World vegetable-oil production rose from **90.5 Mt (2000/01) to 207.5 Mt (2019/20)** (p.1). Soybean oil was **57.1 Mt, 28.8%** of the 2018/19 total (Table 1 p.2).
- Storage and drying:
  - Damaged seeds have higher FFA and need more refining (p.3).
  - Safe storage needs moisture **<13%** (p.3).
  - Drying above **63 °C** darkens the oil and raises **non-hydratable phosphatides** (p.4).
  - Hot dehulling (common for soy) reduces residual oil and **refining losses** (p.6).
- Residual oil in meal:
  - Mechanical presses: **8.7–16.3%** (p.13); high-capacity full presses **5–8%** (p.14).
  - Solvent extraction: **<1%** (p.19).
- Solvent plants: **1,000–5,000 t seed/day**, construction **USD 15–75 M** (p.19).
- Hexane: global demand **1.1 Mt/yr**, of which **650 kt** goes to oilseed extraction (p.25). n-hexane is REACH STOT RE 2, with a **reclassification to STOT RE 1 under way** (p.25).
- Costs:
  - Hexane process ≈ **EUR 30/t seed**; simulated hot-ethanol process **EUR 47.4/t seed** (p.29–30).
  - Hexane NPV is **~10.2% higher** than the best ethanol case for a **125 t/h** soybean plant, which would avoid 10,600 t CO2e/yr (p.30).
- 2-MeOx: EFSA called it safe on **20 Mar 2022**, and it was added to Directive 2009/32/EC on **26 Jan 2023** (p.31).

**3. What Nexus needs.**
- (a) A **processing-cost constant** to turn board crush into an approximate net crush margin (CE-018/019 context): roughly EUR 30/t seed ≈ EUR 160/t oil at 19% oil *(derived)*.
- (b) A mechanistic corroboration of Flores (drying → FFA and NHP).
- (c) A regulatory watch item: EU hexane reclassification as a possible step change in crush cost and compliance.
- Free source for (c): the ECHA RAC opinion register. Nexus has the extraction report, which largely overlaps (solvent is the universal standard).

**4. Rationale.** Small improvement to the crush-margin interpretation (G1 driver ranking) and to quality reasoning (G3 contract spec). The hexane rule is a long-horizon structural risk, outside the 60-day decision window.

**5. Priority / classification.** **Background** (with two **Should** sub-items: the cost constant and the drying→FFA mechanism). **Cite-with-caution** because of the commercial conflict of interest and simulation-based cost figures. Beans vs oil: directly about oil extraction, so the transfer is fine. But nothing here moves CBOT SBO in the forecast horizon.

**6. Caveats.**
- Cost numbers come from cited simulations (Carré; Potrich), not plant data.
- EU-centric.
- The text extraction duplicates many lines (two-column overlap), so verify quotes against the PDF.

**Lens views.**
- *P1-04:* low operational value. The only item is that plant scale (1–5 kt/d) and capex explain crush concentration (supports Haro Sly's 6-firm finding).
- *C-04:* the duplicated and interleaved text layer (p.2–7) makes exact-quote anchors unreliable, so re-extract with Docling before any EvidenceSpan. Tag the cost figures "simulation" in provenance. Normalise EUR/t seed vs per t oil, and do not mix them.
- *Joint conclusion:* KB/background only. Use the EUR 30/t figure as a labelled assumption in any net-crush-margin calculation. Put the hexane reclassification on the policy calendar as a watch item, not an edge.

**7. Ontology candidates.**
- Supports `CAND-Q2` (p.3–4, p.6).
- `CAND-W1` (watch, not an edge): EU n-hexane STOT RE 1 reclassification → EU crushers' compliance cost / solvent switch → EU crush cost ↑ → (negligible, long-run) SBO price UP. Evidence p.25. Do not register (fails relevance and horizon).

---

## Paper 6 — Alves et al., "Estrutura da cadeia produtiva e transmissão de preços da soja entre o produtor e o mercado varejista no Brasil" (Portuguese)

**1. Citation.** Lucilio R. A. Alves, André L. R. Sanches, Andréia C. de O. Adami, Geraldo S. de C. Barros, Mauro Osaki (ESALQ/USP – **CEPEA**). *Desenvolvimento em Questão* 20(58), 2022, e12723, DOI 10.21527/2237-6453.2022.58.12723 (p.1). Data: monthly nominal prices **Jan 2000–Dec 2018** from FGV-Ibre, CEPEA and IBGE IPCA. Fish series start 2008. Biodiesel and diesel series start 2011 (p.7, p.10). Method: DF-GLS, Johansen, structural VEC with 1 lag, IRFs and FEVD.

**2. Core findings (translated).**
- Brazil's soy output grew **6.25%/yr** from 2000/01 to 2019/20 (area 4.53%/yr, yield 1.64%/yr). **Crush grew only 3.47%/yr against bean exports +9.62%/yr** from 2000 to 2019. Bean exports were **≈60%** of production from 2010/11 to 2019/20 (p.2).
- Brazil is a **price taker**: domestic soy prices reflect CBOT (p.4). Seasonality: prices are usually low **Mar–May** and high **Nov–Jan** (p.6).
- **Domestic absorption of crude SBO rose from ~58% of production (2001–05) to 82% (2014–18).** For meal it rose from 38% to >52% (p.8). Crush yields average **~78% meal and 19.2% oil** (p.8).
- Biodiesel blend path (p.17):
  - 2% allowed in 2005, mandatory from 2008
  - 5% (2010), 6–7% (2014), 8% (Mar 2017), 10% (Mar 2018), 11% (2019), 12% (2020)
  - **About 70% of Brazilian biodiesel is SBO-based.**
  - Purchases were made through ANP, a government-intervened market.
- 12-month cumulative pass-through of a **10% soy price shock**:
  - **retail SBO +2.0%** (p.17)
  - pork +1.7%, chicken +1.2%, beef +0.8% (p.11, p.13)
  - diesel +0.5% (p.20)
  - fish +0.28%, eggs +0.25%, margarine +0.16% (p.16–17)
- FEVD of retail SBO from period 3 (Table 8, p.19): own **45.7%**, crude SBO **24.1%**, refined **21.3%**, soy **8.9%**.

**3. What Nexus needs.**
- (a) **Evidence for CE-023** (BR biodiesel → exportable surplus ↓): the 58→82% domestic-absorption shift and the blend timeline give a quantitative structural basis. Nexus currently relies on news-type evidence (Argus, Abiove).
- (b) A free **BR_BIODIESEL_BLEND_PCT step series** (CNPE/ANP resolutions), seeded from p.17 and extended to B14/B15 from ANP. Nexus has no such indicator.
- (c) **CEPEA/ESALQ crude SBO (São Paulo) daily**, the authors' own series. It is free with registration and is listed as unimplemented in `free_alternatives_inventory` §5. It gives Brazilian domestic crude value → export-parity / basis proxy, a free partial substitute for Platts basis (DQ-1).
- (d) Yield constants (19.2% oil) to cross-check farmdoc's ~20% US figure.
- The retail elasticities themselves are **not needed** (Brazilian consumer inflation is out of scope).

**4. Rationale.**
- G1 driver ranking: Brazil's domestic biodiesel absorption is a structural supply driver of world SBO export availability.
- Landed cost: CEPEA crude price vs CBOT gives a free, daily Brazil-side basis indicator for the BR channel.
- G1 analogues: blend step dates are event markers.

**5. Priority / classification.** **Should** (CE-023 evidence and blend series: **Must**, because they are cheap and directly support an existing candidate edge) / **Adopt** the structural facts and data source. The transmission elasticities are **Background** (Brazilian retail, not transferable to Korea CIF). Beans vs oil: the structural facts are oil-specific (p.8, p.17).

**6. Caveats.**
- Nominal, undeflated series (p.7).
- Data end in 2018. Brazil has since moved to B14/B15, and the ANP auction mechanism has changed (outside the paper's period, so verify before use).
- One-lag VEC with an imposed contemporaneous ordering.
- "Domestic consumption" share includes stocks change per USDA definitions.
- C-04: Figure 1 (p.9) is rotated and unreadable in the text layer. The impulse-response figures carry no numbers, so only the text-stated elasticities and Tables 1–10 are extractable.

**Lens views.**
- *P1-04:* the 82% domestic absorption explains why the BR→KR crude channel is small (Nexus customs: BR monthly median 1,326 MT vs AR 10,981 MT). Adopt the blend series as a leading indicator of BR exportable surplus. CEPEA crude is a useful CFR-construction input for BR origin.
- *C-04:* the values are clean and text-stated (p.8, p.17). Normalise CEPEA R$/t (tax-inclusive) to USD/MT with a T+2 FX rule. Check the CEPEA licence before ingestion (the inventory says the terms are unconfirmed). Record the blend steps with effective dates for as-of (`available_at` = resolution publication date, not the effective date).
- *Joint conclusion:* adopt the structural facts as CE-023 evidence now. Queue a CEPEA connector and a blend step series (free, but they need egress and licence approval). Do not use the elasticities.

**7. Ontology candidates.**
- `CAND-B1` (evidence for CE-023, not a new edge): BR blend mandate ↑ → domestic crude SBO absorption share ↑ (58→82%) → BR exportable surplus ↓ → SBO intl price **UP** / BR channel to Korea thinner. Evidence: p.8, p.17.
- `CAND-B2` (structural, for G1): Brazil crush lagging bean exports (3.47 vs 9.62%/yr) → oil supply grows slower than soy supply → SBO tightness relative to beans **UP** (oil share). Evidence: p.2. Candidate, needs PSD confirmation.

---

## Paper 7 — Haro Sly, "The Argentine portion of the soybean commodity chain"

**1. Citation.** Maria José Haro Sly (UFSC). *Palgrave Communications* 3:17095 (2017), DOI 10.1057/palcomms.2017.95. Published 26 Sep 2017 (p.1). Data: secondary sources, mainly 2002–2016 (censuses, INDEC, TELAM, Regunaga 2009, MECON 2011). The chain figure is for **2010** (p.4). World-systems framing.

**2. Core findings.**
- Soy covers **63%** of harvested land and gives **31.8%** of export income (p.3). The top-5 products are **85%** of exports to China (**58% soybeans, 10% soy oil**) (p.3). The trade deficit with China was **US$18.2 B** over 2008–2014 (p.3). China levied a **9%** tariff on SBO imports and prefers beans for its own crushers (p.3).
- Gross-income split for a 400 ha farm: **35%** to the state (export tax), **43%** to the renter, **22%** to the owner (Fig. 2, p.4).
- **50%** of production is controlled by **2.6%** of producers (2010) (p.5). Monsanto collected a **US$15/t** royalty through crushers and exporters from end-2015 (p.5).
- Logistics: **84% truck, 14.5% rail, 1.5% barge** to port. Transport costs **13–23%** of producer gross income depending on distance (p.6).
- Crush and trade:
  - **6 firms handle ~93% of crushing capacity** (Cargill, Dreyfus, Bunge, Glencore, Nidera; locals Molinos, AGD, Vicentin).
  - **Refining capacity is smaller than crushing** and concentrated (Bunge, Molinos, Vicentin, AGD).
  - 23 biodiesel producers (p.7).
  - Silo bags ≈ **30%** of storage capacity in 2007 (p.7).
  - Grain exports: **82%** in 6 firms in 2005, spread to **10** firms by 2012. The ACA cooperative was 5th-largest exporter in 2013 with **1.26 Mt** (p.8).
- Export tax:
  - The 2008 attempt at a **mobile export tax** tied to soy prices collapsed politically (p.7).
  - Macri cut the soybean tax **35% → 30%** and planned annual cuts (p.7).
  - COFCO bought **51%** of Nidera (2014) and the remaining **49%** (2016) (p.7).
- China cut soy imports from Argentina by **29%** in the first 7 months of 2016 as diplomatic pressure (p.9).
- 2010 chain flows (Fig. 2, p.4, **garbled extraction**): production 52,680 kt; crush 39,064 kt (74%); crude oil 7,032 kt; **67% of crude oil exported** (4,732 kt, US$3.9 B). These values need checking against the PDF image.

**3. What Nexus needs.**
- (a) An **Argentine export-tax rate step series** (beans, crude SBO, meal, refined) for G1 analogue dating: 2008 mobile-tax conflict, Dec-2015 cut, later re-raises, Decreto 423/2026. Nexus has only a sentiment indicator plus the 2026 schedule. Free sources: USDA GAIN Argentina Oilseeds Annuals and the Boletín Oficial.
- (b) **Crush-capacity concentration (6 firms ~93%)** and **refining < crushing**. These explain why the AR→KR channel is crude (matching Korea's crude 0% vs refined 5% ASEAN tariff logic in the abcd doc §4).
- (c) Interior logistics mix (truck-dominated) for the AR FOB vs farm-gate spread.
- (d) Event analogue: China using purchase cuts as leverage (2016) → AR bean/oil export diversion. Relevant to CE-011/012 framing.
- Free sources: CIARA-CEC monthly crush and exports, Bolsa de Comercio de Rosario crush-capacity reports, INDEC, MAGyP official FOB (already in the inventory). None are implemented.

**4. Rationale.** G1 (analogue years keyed to AR policy regime), landed cost (the AR residual is negative because of the export-tax-depressed FOB, per the `landed_cost.py` docstring), G3 origin choice (AR crude as the default channel), and supplier KB (who crushes and who refines in AR).

**5. Priority / classification.** **Should** / **Background with selective Adopt**: the export-tax events and crush/refining concentration get adopted, with Cite-with-caution on the numbers. Beans vs oil: the tax figures (35→30%) are for **soybeans**. Product rates were lower (differential export tax), and this paper does not give them. The crush/refining facts are oil-relevant.

**6. Caveats.**
- Advocacy framing.
- Secondary and dated data: crush concentration rests on Regunaga 2009, and the capacity basis differs from Nexus's shipment-based CR4, so the two are NOT COMPARABLE (capacity≠throughput).
- Fig. 2 units print as "mt" but mean thousand tonnes.
- Since 2017: Vicentin's 2020 default and the Bunge–Viterra merger change the firm list.

**Lens views.**
- *P1-04:* register AR crush concentration in the supplier monitor. Truck dependency means AR FOB is sensitive to diesel and road strikes, a lead-time and premium risk on the Rosario route. The export-tax series is the single most important AR-channel CIF driver.
- *C-04:*
  - Fig. 2 (p.4) is unreadable in the text layer, so do not ingest chain volumes without manual image verification.
  - The "35%→30%" span must carry `commodity = soybeans`, not SBO.
  - The concentration fact goes in the ontology `concentration` block as `basis: crush_capacity, as_of: ~2009, label: CONFIRMED-secondary`, with a NOT COMPARABLE note against `shipment_based`.
- *Joint conclusion:* adopt the export-tax event dates (with GAIN for product-specific rates) and the crush/refining structure as KB facts. Discard the chain volumes until verified.

**7. Ontology candidates.**
- Evidence for **CE-003** (and its reverse): Dec-2015 soybean export-tax cut 35→30% (p.7) and the 2008 mobile-tax collapse (p.7), as historical analogue events.
- `CAND-A1` (structural): AR crushing capacity ≫ refining capacity, plus differential export tax → AR exports skew to crude SBO → Korea's crude imports dominated by the AR channel. Evidence p.7. A KB fact, not a price edge.
- `CAND-A2` CN_PURCHASE_LEVERAGE (cutting origin purchases) → AR beans diverted / AR crush ↑ → more AR crude SBO offered → AR-channel CIF **DOWN**. Evidence p.9 (−29%). Candidate, weak; the direction for SBO is INFERENCE.

---

## (a) Ranked top-10 concrete items

| # | Item | Source (locator) | One-line rationale | Priority |
|---|---|---|---|---|
| 1 | **Origin crude-quality prior**: BR vs US FFA 1.32/0.44%, P 220/117 ppm, NOL 1.50/1.01%, checked against NOPA (0.75%, 200 ppm) and FOSFA (1%) | Flores Table 3 p.4 | First measured basis for the "quality" component of origin CIF residuals and for contract-spec clauses (G3, landed cost) | Must |
| 2 | **Quality-adjusted Brazil–US CFR spread** for the P1-04 >USD 20/MT alert (ΔNOL×price ≈ USD 6/MT, illustrative, before degumming cost) | Flores Table 3 p.4 + Nexus customs CIF | Stops false alerts on spreads that are really quality discounts and makes origin comparisons fair | Must |
| 3 | **CE-023 evidence**: BR crude SBO domestic absorption 58%→82%; blend B2→B12; ~70% of biodiesel is SBO | Alves p.8, p.17 | Turns a news-based candidate edge into a structurally evidenced one, at no cost | Must |
| 4 | **BR_BIODIESEL_BLEND_PCT step series** (CNPE/ANP, free), `available_at` = publication date | Alves p.17 (seed) | Leading indicator of BR exportable surplus. Event dates for G1 analogues | Should |
| 5 | **AR export-tax rate step series** (beans/crude/meal/refined, 2002–2026; GAIN + Boletín Oficial) | Haro Sly p.7 (2008, 2015 events) | Main AR-channel CIF driver. Nexus has only sentiment plus the 2026 schedule. Keys G1 analogue regimes | Should |
| 6 | **CEPEA/ESALQ crude SBO daily connector** (free, licence check) | Alves p.7 (CEPEA series); inventory §5 | Free daily Brazil-side basis/export-parity proxy, a partial substitute for paid Platts basis | Should |
| 7 | **AR crush/refining structure** (6 firms ~93% of capacity; refining < crushing) in the ontology concentration block, labelled capacity-based / NOT COMPARABLE | Haro Sly p.7 | Explains why AR→KR is a crude channel. Supplier-monitor context | Should |
| 8 | **Quality branch on CE-009**: wet harvest/drying → moisture & heat damage → FFA/NOL ↑ (moisture +0.172, heat damage +0.175) | Flores Table 6 p.6; Cravotto p.3–4 | Adds a weather→quality→effective-cost channel separate from the yield channel | Should |
| 9 | **Crush constants**: oil 19.2%/meal 78% (BR), AR ≈18% implied, processing ≈EUR 30/t seed, plant scale 1–5 kt/d | Alves p.8; Haro Sly p.4; Cravotto p.19, p.30 | Net-crush-margin approximation for CE-018/019. Cross-check with farmdoc ~20% | Background/Should |
| 10 | **Arco Norte→Panama route candidate** (DATA GAP for SBO) + rule "infrastructure announcement ≠ capacity" | Aguiar p.6, p.10, p.11, p.23 | Widens Panama risk to the BR channel. The rule protects P1-05 from over-reading project news | Background |

Not adopted: all of Khan et al. (low grade); Alves retail elasticities (out of scope); Miranda/Japanese trading houses (KB only, after verification; ranked 11th).

## (b) Disagreements between the lenses

1. **Flores quality gap — model input vs prior.** P1-04 wants it wired into the CFR spread alert and landed-cost bands now. C-04 objects: one Asian plant, USSEC-funded, destination-crushed beans, "not nationally representative", no Argentina. *Resolution:* use it as a labelled scenario prior (INFERENCE) in G3/landed cost only, never as a G2 feature. Validate against customs CIF residuals by origin before it changes any alert threshold.
2. **Arco Norte route registration.** P1-04 wants a route entity with Panama transit. C-04 says there is no SBO-specific evidence; it is "complexo soja"/grain terminals. *Resolution:* candidate with a DATA GAP flag. Activate only after ANTAQ/Comex Stat shows HS 1507 loadings at northern ports.
3. **AR crush concentration.** P1-04 wants it in the supplier monitor as current fact. C-04 says it is capacity-based, ~2009 vintage and pre-Vicentin default, so NOT COMPARABLE with shipment CR4. *Resolution:* register with basis, vintage and comparability labels, and refresh from BCR/CIARA.
4. **Chain-flow numbers (Haro Sly Fig. 2; Flores Tables 4–5; Alves Fig. 1; Cravotto duplicated text).** P1-04 would use the 2010 AR crude export share (67%). C-04 refuses ingestion from garbled text layers. *Resolution:* no ingestion until re-extracted with a layout-aware parser or manual image check.
5. **Japanese trading houses.** P1-04 wants entities now. C-04 requires primary filings because the paper's ownership facts are 2012–2020 press reports. *Resolution:* KB note now, entities after verification.
6. **Processing-cost constant.** P1-04 sees little use. C-04 flags the simulation origin and the author conflict of interest. *Resolution:* use only as a labelled assumption.

Both lenses agree on: rejecting Khan et al. numbers; not transferring the Brazilian retail elasticities; the value of free BR/AR official sources (CEPEA, ANP, ANTAQ, Comex Stat, CIARA, GAIN); and keeping beans-only findings out of SBO price edges.

## (c) Items needing paid data or approval

| Item | Why | Type |
|---|---|---|
| Origin-specific crude SBO quality time series (inspection certificates: SGS/Intertek/Cotecna) | No free BR/AR/US crude-oil quality series exists. Importer QA data is internal and **barred by D-021** | Paid (or not permissible) |
| Platts/Fastmarkets basis by origin (DQ-1) | Validate whether quality discounts show up in quoted basis (BR vs US vs AR) | Paid, decision pending |
| Baltic BCAA tanker freight (DQ-2) | Separate freight from quality in origin residuals | Paid, decision pending |
| Kpler/Vortexa cargo tracking | Confirm whether SBO tankers load at Arco Norte ports. Origin-level parcel quality and timing | Paid |
| Flores Supplementary Data S1 (Tables S1–S3) | Moisture–heat-damage correlations. Downloading a file needs user permission (CC-BY, so no licence issue) | Approval (download) |
| CEPEA crude SBO connector | Terms of use unconfirmed in the inventory. New egress domain | Approval (licence + egress) |
| ANP/CNPE blend series, ANTAQ, Comex Stat, CIARA-CEC, BCR, Boletín Oficial | Free, but new egress domains and connectors | Approval (egress, coordinator gate) |
| Any ontology change (CAND-Q1/Q2, B1/B2, A1/A2, R1, KB entities) and references README entries | Repo was read-only for this review. Edges need P1-04/P1-01 validation and the human gate | Approval (coordinator) |
