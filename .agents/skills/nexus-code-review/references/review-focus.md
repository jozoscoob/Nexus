# Nexus review focus

Read the rows relevant to the diff. Resolve current contracts from code and path-scoped rules rather than treating this reference as a schema or dependency lock.

| Changed boundary | Evidence to trace | Defects worth demonstrating |
|---|---|---|
| Connector → parquet/DuckDB | SDK request, timeout/retry, empty-result handling, schema, caller | Silent partial success, duplicate session rows, overwrite of vintages, swallowed required failure |
| Target → feature mart | `data/gold/feature_contract.yaml`, target producer, `src/features/build_feature_mart.py` | Missing target replaced with Brent/CPO/first column; UTC diagnostic relabeled; invalid units or session dates admitted |
| Publication → model input | `src/pipeline/asof.py`, join predicates, `scripts/validate_asof.py`, actual prediction cutoff | Missing/null as-of fields accepted, latest revisions backfilled into historical features, input available after prediction time |
| Folds → reported evaluation | Forecasting/evaluation code, feature selection, calibration, label windows | Fit or selection before chronological splits; future labels cross a training cutoff; preprocessing or calibration sees holdout data |
| Docker → n8n → runner | `docker/Dockerfile`, `docker/compose.yml`, `docker/jobs.py`, relevant `docker/n8n/*.json`, tests | Shell injection, credential exposure, uncontrolled job selection, concurrent writes, missing timeouts, nonzero exit treated as success |
| CI → model entry → publication | `.github/workflows/quality_gate.yml`, consuming workflow jobs/conditions, snapshot manifest consumer | Required check skipped or warning-only; `always()` reaches modeling after failed gates; stale/mismatched artifact consumed; generated raw/model data pushed to main |
| Agent output → downstream consumer | Prompt, raw evidence, schema validator, routing/error path | Retrieved instructions trusted; ungrounded claim becomes data; malformed output accepted; verification unavailable but marked successful |

Canonical soybean-oil target requirements from `AGENTS.md`: `target_eligible=true`, `time_basis` in `CME_SESSION`/`EXCHANGE_SETTLEMENT`, `USc/lb`, no weekend dates, one observation per session. `CBOT_BO_UTC_*` remains diagnostic. Trace positive-price, source-provenance, and coverage requirements from the current contract too. These are hard gates; a weighted DQ score cannot substitute for them.

`available_at <= prediction_time` must hold for every selected input. Merely checking `available_at >= event_time`, sorting dates, or using a chronological splitter is insufficient. Verify both the join and fitting boundary. Use the declared horizons (1/5/20/60 trading sessions) when checking label overlap; do not invent one universal gap length.

G1 historical analog distributions are observations, not forecasts. G2 bands require out-of-sample interval/calibration evidence under the current model policy. G3 uses market-cost/per-MT regret and runtime quantities, never actual company P&L claims from absent internal data. All procurement-affecting output remains behind the human gate.

Do not flag every `subprocess` occurrence: `CLAUDE.md` prohibits shell-based **data access**. Trace whether a use only orchestrates fixed commands or actually retrieves data/binds untrusted inputs. Never weaken validation to satisfy an older role checklist or imported simplification advice.
