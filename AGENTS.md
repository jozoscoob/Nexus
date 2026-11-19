# Project Nexus — Repository Agent Instructions

These instructions apply repository-wide to any coding assistant.

## Start Here

1. Read `README.md §QR` for commodity scope and G1/G2/G3 definitions.
2. Read `CLAUDE.md` for hard constraints and HITL rules.
3. Load only the path-scoped rule relevant to the files being changed.
4. Read the relevant `.claude/agents/*.md` role file when coordinating named project agents.

If a referenced file or fact is absent, report `정보 없음` rather than inferring it.

## Hard Boundaries

- Use external pipeline data only. Do not add internal operational data or proxies derived from it.
- Do not commit credentials, account identifiers, detailed network topology, personal schedules, or other
  confidential operational context.
- Do not extend the commodity scope beyond soybean oil without explicit approval.
- Do not produce or execute an autonomous Buy/Hold action. Procurement-affecting outputs require HITL.
- Never use `pickle`; use MLflow or joblib under the modeling rules.

## Data and Model Gates

- Model inputs must satisfy `available_at <= prediction_time`; absent as-of fields block model entry.
- Canonical target prices require `target_eligible=true`, `time_basis` of `CME_SESSION` or
  `EXCHANGE_SETTLEMENT`, unit `USc/lb`, no weekend dates, and one observation per session.
- `CBOT_BO_UTC_*` is a UTC-bucket diagnostic series and must never be relabeled as the canonical target.
- Do not replace a missing soybean-oil target with Brent, CPO, or the first available column.
- Time-series preprocessing and feature selection are fitted inside chronological folds only.

## Delivery Rules

- Use a branch and pull request; workflows must not push generated data directly to `main`.
- Required release gates fail closed. Do not hide failures with `--warn`, `|| true`, or
  `continue-on-error` on a model-entry path.
- Generated raw/model data belongs in workflow artifacts or an approved immutable snapshot store, not Git.
- Add synthetic tests that do not require credentials or proprietary datasets. Keep artifact-dependent tests
  as a separate integration layer.
- State what was verified and what remains blocked; a generated report is not proof that its target was valid.
