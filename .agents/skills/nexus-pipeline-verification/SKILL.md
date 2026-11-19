---
name: nexus-pipeline-verification
description: Cross-verify Nexus data processing and Claude/Codex agent handoffs across Docker, n8n, data contracts, and model-entry gates. Use for pipeline reliability, provenance, leakage, and failure-propagation audits; does not perform procurement analysis or repair source data.
---

# Nexus pipeline verification

Establish whether an identified pipeline path can safely reach its next gate. Default to read-only inspection and credential-free synthetic verification. Do not alter source data, launch collection/training, invoke paid services, or change an active schedule as part of verification.

## Scope and contracts

Read repository `AGENTS.md`, `README.md §QR`, `CLAUDE.md`, `.claude/rules/tooling.md`, and relevant MEMORY pitfalls. Follow current hard rules when older examples disagree; absent facts or references are `정보 없음`. Load only relevant path-scoped rules. Load Ponytail when inspecting code. Read C-08's role file for data-validation work and C-05/C-03 only when their handoff is in scope; a named role file does not mean an agent or runtime exists.

Name the exact execution surface, revision plus dirty state, entry point, expected inputs/outputs, and downstream consumer. Use [verification.md](references/verification.md) for the existing Nexus path map and safe checks. Read the actual scripts and n8n error branches before running a command: a validator can fetch data or publish a canonical file. Do not equate a read-like job name with no side effects.

Trace producer → artifact → contract → as-of join → validation → model entry → report. Record missing/empty inputs, required versus optional dependencies, freshness/vintage, session calendar, units, and snapshot hash/schema checks. Use only external data. Do not infer internal inventory, quantities, margins, credentials, or infrastructure details.

## Cross-verify independently

- Recompute a small sample from source records with a second method when feasible, for example DuckDB ASOF selection versus an independent pandas selection. Use identical prediction cutoffs, units, timezone/session interpretation, and snapshot. A second agent agreeing with the first is not independent evidence.
- Prove selected values satisfy `available_at <= prediction_time`; missing or unparseable availability blocks model entry. Preserve source vintages. Check the canonical target's eligibility, time basis, `USc/lb`, session uniqueness, and no weekend dates. Never promote `CBOT_BO_UTC_*`, shift Sunday to Monday as a substitute for session construction, or fill a missing target from another commodity.
- For modeling, inspect fit/selection/calibration inside chronological folds and horizon-aware label boundaries. Require the current baseline and out-of-sample checks; report unexecuted checks explicitly.
- For Claude/Codex or other LLM handoffs, reconcile claims to cited source records and timestamps, validate output schemas, keep untrusted source text out of instruction authority, and test malformed or unavailable output. Record current provider/model configuration names only when necessary, never account identifiers or auth contents. Do not make live model calls unless separately authorized.
- On synthetic fixtures, inject failures relevant to the path: empty target, missing/future availability, duplicate/non-session target, stale or mismatched snapshot, failed required step, malformed agent response. Verify that downstream modeling/publication is not reached. Check n8n status/branch handling as well as process exit status. Optional connector failure must never bypass a required readiness gate.

## Evidence and handoff

For each check, report requirement, inspected path or command, synthetic/real input scope, observed result, expected failure behavior, and limitation. Use `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`; do not convert absent integration evidence into PASS. A critical FAIL or BLOCKED check blocks model/release readiness even if aggregate DQ or synthetic checks pass.

Give defects and reproduction evidence to the requested implementation task (or `$nexus-production-hardening` when appropriate). Keep code defects separate from observed data-quality failures and improvement proposals. Do not open issues, post messages, spawn agents, or modify files automatically from this verifier. Procurement-affecting validation or production-data writes require the existing CLAUDE human gate, including its planning and approval stages.
