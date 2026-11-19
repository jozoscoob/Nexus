# Probabilistic Price-Range (Interval) Forecasting for Commodity Procurement Budgeting (Ag / Vegetable Oils)

Scope note: about 16 search/fetch calls. Several full texts were paywalled or blocked (MDPI returned 403, the Essex PDF failed on an SSL error), so many findings below rest on abstracts or search-engine excerpts. Each item says what was checked. Items tagged **[prior knowledge, not fetched this session]** are standard references I'm confident exist, but I did not reopen them here. Check them before quoting exact numbers.

---

## 1. Quantile regression / quantile GBM (LightGBM) / quantile random forests: calibration and gains over historical-simulation bands

### Takeaway
I found **no peer-reviewed study that tests QR, QRF or LightGBM-quantile bands against historical-simulation (HS) bands for agricultural or vegetable-oil prices**. That gap is the main finding for this question. The evidence that does exist comes from electricity prices, crypto, and general ML. It points the same way each time: pinball-trained quantile models are often *under-covered* out of sample. Their coverage has to be measured separately from pinball loss, and a conformal calibration layer is the usual fix.

### Cited Findings
- **Pinball loss does not guarantee coverage.** In skforecast's worked example, an 80% interval from quantile-regression forecasters reached only **71.9% empirical coverage**. A later version of the guide, on a different setup, reports about 77%. Low pinball loss does not imply nominal coverage, so coverage has to be checked on its own. (Library documentation, not peer-reviewed.) — [skforecast QR guide (latest)](https://skforecast.org/latest/user_guides/probabilistic-forecasting-quantile-regression); [skforecast 0.17](https://skforecast.org/0.17.0/user_guides/probabilistic-forecasting-quantile-regression)
- **Recommended evaluation:** "maximize sharpness subject to reliability" (the Gneiting–Raftery paradigm). Electricity-price papers score coverage (reliability) together with interval width or pinball-based scores (sharpness). — [Expectile regression averaging, arXiv 2402.07559](https://arxiv.org/pdf/2402.07559); [Isotonic QRA, arXiv 2507.15079](https://arxiv.org/pdf/2507.15079)
- **Ranking depends on the loss function.** Model rankings for probabilistic forecasts can change depending on the score used (pinball vs CRPS vs interval scores). — [Ranking probabilistic forecasting models with different loss functions, arXiv 2411.17743](https://arxiv.org/pdf/2411.17743) (title and topic only, per search excerpt)
- **QRF vs linear QR on volatile prices (electricity, Australia NEM):** QRF captures complex behaviour at each quantile, including the skewed spike risk in the price series, which linear QR misses. Search excerpt only; no coverage numbers retrieved. — [Probabilistic forecast methodology for volatile electricity prices in the NEM, arXiv 2311.07289](https://arxiv.org/pdf/2311.07289)
- **Crypto analogue (72-hour horizon):** A time-decay-weighted QRF was benchmarked against linear QR and a tuned LightGBM-quantile model, scored on pinball loss, empirical coverage and width. Linear QR **under-covered**. Conformally calibrated LightGBM **over-covered fairly uniformly across regimes**. (ResearchGate preprint, not verified as peer-reviewed.) — [Interval Forecasting of Cryptocurrency Returns using QRF (Solana)](https://www.researchgate.net/publication/395025657_Interval_Forecasting_of_Cryptocurrency_Returns_using_Quantile_Regression_Forests_An_Application_to_the_Solana_Ecosystem)
- **LightGBM-quantile vs QRF coverage (non-financial QSAR data):** Quantile LightGBM gave good coverage on most datasets, better than QRF but worse than BART, and its intervals were often narrower. Coverage should be compared alongside width. — [LightGBM for QSAR, arXiv 2105.08626](https://arxiv.org/pdf/2105.08626)
- **Quantile XGBoost for uncertainty quantification:** a general method paper. — [Quantile Extreme Gradient Boosting, arXiv 2304.11732](https://arxiv.org/pdf/2304.11732) (title only)
- **Foundational:** Meinshausen, N. (2006). "Quantile Regression Forests." *Journal of Machine Learning Research* 7, 983–999. **[foundational; prior knowledge, not fetched this session]** — [JMLR](https://www.jmlr.org/papers/v7/meinshausen06a.html)
- **Ag-commodity ML literature is mostly point forecasts.** Recent multi-commodity ag-futures ensembles report MAPE/MAE/RMSE, not coverage or CRPS. — [Explainable ensemble forecasting of multi-commodity ag futures, Algorithms 2026, doi:10.3390/a19080660](https://doi.org/10.3390/a19080660); [PSO-CS forecast combination for daily corn/wheat/soybean futures, Applied Soft Computing](https://www.sciencedirect.com/science/article/abs/pii/S1568494622008821)
- **USDA ERS season-average-price models** use futures prices to produce **point** forecasts for corn, soybeans and wheat. They do not produce distributions. — [USDA ERS SAP forecasts documentation](https://www.ers.usda.gov/data-products/season-average-price-forecasts/documentation)

### Inferences
- For a procurement band at 1-day to 3-month horizons, the practical recipe is: LightGBM or QRF quantiles (or linear QR on returns), then a conformal recalibration layer (CQR/ACI, Section 2), then backtesting coverage with Kupiec/Christoffersen tests against HS and filtered-HS (FHS/GARCH) baselines. The ML literature rarely includes HS baselines, so we would have to build that comparison ourselves.
- On log-returns, a near-random-walk price makes the median forecast close to the current price. Most of any gain from QR/GBM would then come from conditional *width* (volatility state, term structure, seasonality), not from shifting the location. That fits Section 5.

### Gaps
- No ag or vegetable-oil study found that reports QR/QRF/LightGBM coverage or pinball loss against HS bands. A targeted search of *Journal of Commodity Markets* and *AJAE* might still turn one up; I did not find it in this pass.
- No numerical coverage or pinball results were retrieved for the electricity QRF paper (only the excerpt).

---

## 2. Conformal prediction (split conformal, CQR, EnbPI, ACI) for time series and commodity/energy prices: coverage under regime shifts; ag/veg-oil applications

### Takeaway
Conformal methods are now standard as a calibration "last layer" in **electricity-price** forecasting. Adaptive variants (ACI, aggregated ACI, EnbPI, SPCI) hold close to nominal coverage under non-stationarity. Plain split conformal does not, because exchangeability fails. Agricultural applications only appear in **2026, on vegetable/potato/seed prices**. I found **none on soybean oil or palm oil**.

### Cited Findings
- **Foundational methods [prior knowledge, not fetched this session]:**
  - Romano, Y., Patterson, E., Candès, E. (2019). "Conformalized Quantile Regression." *NeurIPS 32*. — [arXiv 1905.03222](https://arxiv.org/abs/1905.03222)
  - Gibbs, I., Candès, E. (2021). "Adaptive Conformal Inference Under Distribution Shift." *NeurIPS 34*. The ACI update α_{t+1} = α_t + γ(α − err_t) gives long-run average coverage → 1−α even under arbitrary shift. — [arXiv 2106.00170](https://arxiv.org/abs/2106.00170)
  - Xu, C., Xie, Y. (2021). "Conformal Prediction Interval for Dynamic Time-Series" (EnbPI). *ICML, PMLR 139*. — [arXiv 2010.09107](https://arxiv.org/abs/2010.09107)
- **Zaffran, Féron, Goude, Josse, Dieuleveut (2022), "Adaptive Conformal Predictions for Time Series," ICML, PMLR 162.** Tested ACI and an aggregated variant (AgACI, which removes the need to pick γ) on **French day-ahead electricity prices**. Aggregation gave efficient intervals while staying close to valid coverage. Out-of-sample, 1-day-ahead (hourly). — [PMLR v162](https://proceedings.mlr.press/v162/zaffran22a/zaffran22a.pdf); [arXiv 2202.07282](https://arxiv.org/html/2202.07282v1)
- **Adaptive probabilistic forecasting of French spot prices (2024):** argues that adaptive conformal methods plus online aggregation should be "a fundamental last layer of any operational pipeline." — [arXiv 2405.15359](https://arxiv.org/html/2405.15359)
- **O'Connor et al. (2025), "Conformal Prediction for Electricity Price Forecasting in the Day-Ahead and Real-Time Balancing Market":** compares EnbPI and Sequential Predictive Conformal Inference (SPCI). The proposed ensemble (Q-Ens) gave narrower intervals while keeping coverage. Out-of-sample, Irish market. — [arXiv 2502.04935](https://arxiv.org/pdf/2502.04935); [ScienceDirect S266654682500103X](https://www.sciencedirect.com/science/article/pii/S266654682500103X)
- **Limitation:** basic split-conformal intervals are not adaptive. Only the *location* follows the point forecast and the *width* stays constant. Turning symmetric conformal intervals into quantiles also assumes a symmetric distribution. — [Isotonic QRA, arXiv 2507.15079](https://arxiv.org/pdf/2507.15079)
- **Ag applications (2026, excerpts only, not full-text verified):**
  - Weekly e-commerce **seed prices** (tomato, pepper, lettuce). A TFT+SARIMAX+LightGBM ensemble with **adaptive conformal intervals came close to nominal coverage at short horizons**. — [Agriculture 2026, doi:10.3390/agriculture16151620](https://doi.org/10.3390/agriculture16151620)
  - **Potato prices:** "Drift-Aware Conformal Prediction" wraps CNN/LSTM/N-BEATS/Autoformer/Informer and recalibrates on rolling windows for non-stationary markets. — [Potato Research 2026, doi:10.1007/s11540-026-10049-4](https://link.springer.com/article/10.1007/s11540-026-10049-4)
  - **Crop yields (not prices):** conformal coverage breaks down under distribution shift. The authors recommend judging coverage together with decision regret. (Zenodo preprint, not peer-reviewed.) — [Zenodo 23606678](https://zenodo.org/records/23606678)
- **Regime-shift evidence without conformal (TTF gas, Ukraine war / Nord Stream shock):** Schlüter, Pappert, Neumann (2024) compared ARMA-GARCH, copula time-series models, MLP and LSTM. **Most models underestimated variance during the shock and overestimated it afterwards.** The simpler models (ARMA-GARCH and MLP) gave the best interval coverage during the shock, and the LSTM was outperformed. arXiv preprint; numeric coverage and horizon not on the abstract page. — [arXiv 2407.16723](https://arxiv.org/abs/2407.16723)

### Inferences
- The TTF result (variance underestimated in the shock, overestimated after) is the failure ACI is built to correct, since it widens after misses and narrows after over-coverage. This argues for ACI/AgACI on top of any base band for veg-oil (e.g., the 2022 Ukraine/Indonesia export-ban spike in palm and soybean oil).
- ACI only guarantees *long-run average* coverage. After a jump it still misses for some days before widening. For budgeting, a stress overlay (scenarios, Section 4) is still needed.
- At multi-step horizons (1–3 months), each horizon needs its own calibration set, and the effective sample shrinks (non-overlapping 3-month errors give few observations per year). That weakens coverage estimates. I found no paper quantifying this for commodities.

### Gaps
- No conformal application found for soybean oil, palm oil, or grain futures.
- No numeric coverage figures retrieved for O'Connor et al. or Zaffran et al. (only the qualitative claims).

---

## 3. GARCH / EGARCH / GJR / realized-vol vs implied-vol bands: do options (e.g., CBOT soybean-oil options) forecast range better?

### Takeaway
For **grains and oilseeds (corn, wheat, soybeans)**, option-implied variance generally **beats historical/GARCH variance** as a forecast of realized variance. But implied vol is **biased upward** by a variance risk premium, so raw IV bands **over-cover**. For realized-volatility models, the **simple HAR is hard to beat out of sample** (1–66 days). I found **no IV-vs-GARCH study for soybean oil or palm oil specifically**.

### Cited Findings
- **Triantafyllou, A., Dotsis, G., Sarris, A. H. (2015). "Volatility Forecasting and Time-varying Variance Risk Premiums in Grains Commodity Markets." *Journal of Agricultural Economics* 66(2), 329–357.** Model-free implied variance and skewness for wheat, maize and soybean. **Option-implied risk-neutral variance outperforms historical variance as a predictor of future realised variance for all three.** Variance risk premia add significant predictive power for returns. (Abstract-level verification; full text paywalled; author order differs across indexes.) — [IDEAS/RePEc](https://ideas.repec.org/a/bla/jageco/v66y2015i2p329-357.html); [Essex repository](https://repository.essex.ac.uk/30100/); [FERDI WP version](https://ferdi.fr/publications/volatility-forecasting-and-time-varying-variance-risk-premiums-in-grains-commodity-markets)
- **Degiannakis, S., Filis, G., Klein, T., Walther, T. (2022). "Forecasting Realized Volatility of Agricultural Commodities." *International Journal of Forecasting* 38(1). DOI 10.1016/j.ijforecast.2019.08.011.** Tick data for corn, rough rice, soybeans, sugar and wheat (CME/ICE). HAR variants, **out-of-sample 1 to 66 days ahead**. Extended HAR variants fit better in-sample but **do not beat simple HAR out of sample**. "No benefit from adding more complexity." The result holds in a **VaR evaluation**. (Page numbers conflict between sources: 51–73 vs 74–96.) — [EconPapers](https://econpapers.repec.org/RePEc:eee:intfor:v:38:y:2022:i:1:p:74-96); [Bournemouth eprints](https://eprints.bournemouth.ac.uk/32687/); [MPRA preprint](https://mpra.ub.uni-muenchen.de/96267/)
- **Diersen, M., Wang, Z. "Weekly Options on Grain Futures"** (NCCC-134 2022; *Journal of Agricultural and Applied Economics*). For soybeans, **week-ahead implied vol averaged 16.7% vs 13.9% realized**. Market participants overpay future realized vol by about **420 bp for corn and 280 bp for soybeans** (a positive variance risk premium). — [farmdoc NCCC-134 PDF](https://farmdoc.illinois.edu/assets/meetings/nccc134/conf_2022/pdf/Diersen_Wang_NCCC-134_2022.pdf); [JAAE](https://www.cambridge.org/core/journals/journal-of-agricultural-and-applied-economics/article/weekly-options-on-grain-futures/2894EF96254BD133BF33E1F794BD1DE1)
- **Older evidence (pre-2015, foundational):** implied forward volatility for agricultural options **dominates historical-volatility forecasts**, but accuracy depends on the commodity. Earlier work finds a **significant upward bias** in IV for corn and soybeans. Another older study finds **no single method best across datasets and horizons**. One study finds model-free implied variance has about the same forecasting power as historical variance for soybeans. (Search excerpts, older work.) — [Intermediate Volatility Forecasts Using Implied Forward Volatility (ResearchGate)](https://www.researchgate.net/publication/23513876_Intermediate_Volatility_Forecasts_Using_Implied_Forward_Volatility_The_Performance_of_Selected_Agricultural_Commodity_Options); [Information Content of IV from Options on Ag Futures (ResearchGate)](https://www.researchgate.net/publication/23514024_THE_INFORMATION_CONTENT_OF_IMPLIED_VOLATILITY_FROM_OPTIONS_ON_AGRICULTURAL_FUTURES_CONTRACTS); [UCLouvain thesis on IV in ag markets](https://research.dial.uclouvain.be/bitstreams/35301086-027d-4e12-8e3d-7de76ec52c78/download)
- **USDA RMA / Sumaria (2014) price-volatility report:** IV is used to set crop-insurance price volatility factors. It is a practitioner precedent for IV-based price bands. (Not opened.) — [RMA PDF](https://legacy.rma.usda.gov/pubs/2014/pricevolatility.pdf)
- **Palm oil volatility:** GARCH(1,1) on Malaysian CPO (1995–2014) shows persistent volatility, with a **shock half-life of about 18.1 months**. Other studies add volume and open interest to the GARCH variance equation for CPO futures. I found **no CPO VaR/quantile backtest (Kupiec/Christoffersen) study**. — [Malaysian CPO market volatility: a GARCH approach (ResearchGate)](https://www.researchgate.net/publication/288228154_Malaysian_crude_palm_oil_market_volatility_A_GARCH_approach); [Trading activities and volatility of Malaysian CPO futures, JRFM 2022, doi:10.3390/jrfm15010034](https://doi.org/10.3390/jrfm15010034)
- **Energy analogue for VaR bands:** For crude-oil futures, realized-GARCH with high-frequency bipower variation passed all VaR backtests, while **GARCH, EGARCH and GJR were rejected in 4, 4 and 2 of 18 cases** (5% level). — [Forecasting VaR of crude oil futures: do high-frequency data help? (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/pii/S2096232025000095)

### Inferences
- **Practical band construction for soybean oil (CBOT ZL):** use IV from ZL options at the matching expiry as the width driver, scaled down by an estimated VRP ratio (RV/IV historically below 1 for grains per the numbers above). Then recalibrate with ACI. Raw IV bands will probably be too wide, which is conservative for a budget but costly if used to size hedges.
- **Palm oil** (Bursa Malaysia FCPO) has thinner listed options liquidity (not verified this session). GARCH/HAR or FHS bands are the realistic choice there, possibly borrowing information from ZL implied vol through the soy–palm spread correlation (inference).
- Given Degiannakis et al., a simple HAR-RV or GARCH(1,1)-t is a strong enough historical baseline. Fancier variants are unlikely to help out of sample.

### Gaps
- No study found comparing ZL (soybean oil) or palm oil IV against GARCH for interval coverage.
- I could not retrieve the full text of Triantafyllou et al. for horizon-specific loss statistics.
- I did not verify whether CME publishes a soybean-oil CVOL index or how deep ZL option liquidity is beyond the front months.

---

## 4. Scenario generation for procurement budgets (bootstrap, copulas, Monte Carlo with jumps) and how firms turn bands into budget/hedge decisions

### Takeaway
Industry practice is **Monte Carlo cash-flow-at-risk (CFaR) / budget-at-risk**. Firms simulate price paths, map them through exposure (volume × price × FX), and report percentiles of procurement cost against budget. They then compare hedge ratios by how much they shrink the CFaR tail. Most sources here are **vendor or consultancy material, not peer-reviewed**. I found no empirical academic study of how procurement teams actually use the bands.

### Cited Findings
- **McKinsey Working Papers on Risk No. 51 (Pergler & Rasmussen), "Strategic commodity and cash-flow-at-risk modeling for corporates":** corporates focus on **operating cash flow rather than market VaR**, and **Monte Carlo is the practical method**. — [McKinsey WP 51 PDF](https://www.mckinsey.com/~/media/mckinsey/dotcom/client_service/risk/working%20papers/51_strategic_commodity_and_cashflowatrisk_modeling.ashx)
- **Budget-at-risk per risk factor:** a patent measures budget-at-risk for each risk factor on a standalone basis, and how much hedging that single risk would reduce it. A second patent pairs CFaR with Monte Carlo for risked budget estimates. (Patents describe claimed methods, not validated practice.) — [USPTO 7962396](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7962396); [USPTO 7822670](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7822670)
- **Vendor descriptions (not peer-reviewed):** Monte Carlo converts commodity price moves into VaR/CFaR figures. A slightly pricier input can lower overall risk, so procurement should weigh risk, not just price. — [KYOS CFaR/EaR](https://www.kyos.com/solution/cashflow-earnings-at-risk/). CFaR maps the range of future cash flows using Monte Carlo. — [ION Group](https://iongroup.com/blog/treasury/why-corporates-must-consider-cash-flow-at-risk-cfar/). Stress testing, scenario analysis and Expected Shortfall sit alongside CFaR-driven hedge optimisation. — [UnRisk white paper](https://www.unrisk.com/white-papers/commodity-fx-interest-rate-cfar/). Scenario grids show how hedging costs and gains affect cash flow and margins. — [Phoenix Strategy Group](https://phoenixstrategy.group/blog/fpa-tips-hedging-market-risks). Commercial positioning of "budget certainty." — [Fastmarkets risk management](https://www.fastmarkets.com/products/risk-management/)
- **Copula-based time-series models** were among the TTF interval-forecast competitors. During the shock they did not beat simpler ARMA-GARCH on coverage. — [Schlüter et al. 2024, arXiv 2407.16723](https://arxiv.org/abs/2407.16723)

### Inferences
- A defensible pipeline for a veg-oil procurement budget:
  1. Generate marginal return paths with FHS (bootstrap standardized GARCH residuals) or an IV-scaled lognormal, plus a jump overlay calibrated to episodes like 2008, 2021–22 and the April 2022 Indonesian palm export ban.
  2. Link soybean oil, palm oil and FX (USD/KRW) with a t-copula or block bootstrap to keep tail dependence.
  3. Aggregate to monthly purchase cost.
  4. Report P50/P90/P95 against budget.
  5. Compute "budget-at-risk reduction per hedge ratio" for futures, collars and fixed-price contracts.
- Conformal or ACI calibration applies to the *marginal* bands (P5–P95 per horizon). The joint scenario engine then needs backtesting to confirm its implied marginal quantiles match the calibrated bands.

### Gaps
- No peer-reviewed empirical study found on how food or veg-oil buyers turn forecast bands into budget prices or hedge ratios. A follow-up search could target operations-management literature (e.g., Kouvelis et al. on procurement with financial hedging, *Manufacturing & Service Operations Management*); I did not verify any specific paper this session.
- No peer-reviewed evidence retrieved on bootstrap vs copula vs jump-diffusion scenario quality for ag commodities.

---

## 5. How hard is it to beat the random walk for agricultural commodity prices at 1-day to 3-month horizons?

### Takeaway
**Very hard for point forecasts at short horizons.** The no-change (random-walk) forecast is the standard benchmark. Sophisticated ML models often fail to beat it under strict out-of-sample protocols. Futures prices and some econometric models (local projections, dynamic model averaging) sometimes win, mostly at longer horizons or for real prices. For *interval* forecasting, the implication is that skill sits in the **width (volatility)**, not the centre.

### Cited Findings
- **"Forecasting Commodity Prices: Looking for a Benchmark"** (*Forecasting* (MDPI) 3(2), article 27, 2021). The random-walk no-change forecast is "the most popular benchmark." Using it for **nominal** prices is "somewhat justified," and **futures prices are recommended as a second benchmark**. Local projection models give competitive forecasts for **real** cereal prices (barley, maize, rice, wheat) relative to the random walk, **especially at longer horizons**. (Full text fetch blocked with 403; findings from search excerpts.) — [MDPI PDF](https://www.mdpi.com/2571-9394/3/2/27/pdf); [ResearchGate](https://www.researchgate.net/publication/352561979_Forecasting_Commodity_Prices_Looking_for_a_Benchmark)
- **Chinese soybean futures (2025, Systems 14(9) 1152):** under a strict out-of-sample protocol with Diebold–Mariano tests (Newey–West variance), **BiLSTM-Attention did not outperform the random walk**. — [MDPI Systems](https://www.mdpi.com/2079-8954/14/9/1152)
- **US soybean futures, Dynamic Model Averaging (2019/2021, *Emerging Markets Finance and Trade* 57(4)):** DMA **beat the random walk** on Diebold–Mariano tests. Predictors change over time. — [Taylor & Francis, doi:10.1080/1540496X.2019.1618265](https://www.tandfonline.com/doi/abs/10.1080/1540496X.2019.1618265)
- **2026 benchmark of classical vs deep-learning models:** naive persistence dominates on near-random-walk commodities. (arXiv preprint, excerpt only.) — [arXiv 2604.06227](https://arxiv.org/pdf/2604.06227)
- **Time-series foundation models for agricultural commodity prices (2026 arXiv):** evaluates TSFMs on commodity prices. I did not retrieve the results. — [arXiv 2601.06371](https://arxiv.org/pdf/2601.06371)
- **Palm oil and soybean oil:** a hybrid GA-VMD-LSTM paper applies Diebold–Mariano tests to monthly maize, palm oil and soybean oil at a one-year horizon. It compares only against **LSTM variants, not a random walk**, so it does not show skill over naive forecasts. — [Scientific Reports 2025, doi:10.1038/s41598-025-94173-0](https://www.nature.com/articles/s41598-025-94173-0)
- **Wholesale edible oil prices:** Gaussian process regression tuned with Bayesian optimization (*Asian Journal of Economics and Banking*). Benchmark against random walk not confirmed. — [Emerald, doi:10.1108/ajeb-06-2024-0070](https://emerald.com/insight/content/doi/10.1108/ajeb-06-2024-0070/full/html)
- **Asset-pricing approach to ag prices (Chen, Rossi et al., CREI WP):** predicting agri-commodity prices with exchange-rate and asset-pricing information. (Title and author excerpt; results not retrieved.) — [CREI working paper](https://www.crei.cat/wp-content/uploads/users/working-papers/rossi_predicting_agri.pdf); related: [NBER w13901 "Can Exchange Rates Forecast Commodity Prices?"](https://www.nber.org/system/files/working_papers/w13901/w13901.pdf) (foundational, pre-2015)
- **Futures vs random walk (Federal Reserve FEDS Note, 2026-09-03):** compares futures-based and no-change forecasts using relative RMSE. I could only confirm energy and natural gas from the excerpt, not ag. — [FEDS Note](https://www.federalreserve.gov/econres/notes/feds-notes/revisiting-the-forecasting-potential-of-futures-prices-20260903.html)
- **Benchmark-definition matters:** period-average futures forecasts vs end-of-month no-change benchmarks can flip conclusions. — [LCERPA WP 2024-3](https://www.lcerpa.org/files/LCERPA_2024_3.pdf)
- **Crude-oil analogue:** whether forecasts of the real price of oil beat the random walk is still debated. A no-change forecast based on end-of-month prices is reported as significantly more accurate up to one year ahead. — [J. Banking & Finance 2023, S0378426623001619](https://www.sciencedirect.com/science/article/pii/S0378426623001619)

### Inferences
- For a procurement band, centre the band on the futures price for the delivery month (or spot plus carry) and spend modelling effort on **width calibration**. Expect little gain from forecasting direction at 1-day to 3-month horizons.
- The right baselines for any band model are: (a) a random-walk centre with HS-percentile width; (b) a random-walk centre with GARCH/FHS width; (c) a futures centre with IV width. Score with coverage (Kupiec/Christoffersen), interval/Winkler score, pinball loss and CRPS. Use Diebold–Mariano on CRPS/pinball differences to test significance.

### Gaps
- **No study found reporting CRPS or pinball loss against a random-walk/HS benchmark for soybean oil or palm oil at 1-day to 3-month horizons.** This is the main empirical gap.
- Known older ag-forecast-evaluation literature was not re-verified this session and should be checked before citing: Colino, Irwin & Garcia on outlook vs futures forecasts for hogs and cattle; Ahumada & Cornejo (2016, *IJF*) on corn/soybean/wheat price forecasting.
