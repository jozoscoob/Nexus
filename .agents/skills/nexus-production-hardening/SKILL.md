---
name: nexus-production-hardening
description: Implement requested Nexus reliability fixes and prepare evidence for production release across Docker, n8n, CI/CD, and data/model gates. Use for authorized remediation or release-readiness work; excludes autonomous deployment, procurement actions, and customer outreach.
---

# Nexus production hardening

Turn a concrete reliability requirement or verified defect into a tested, reviewable change. Creating these skills does not authorize a whole-project rewrite or establish production readiness.

## Establish the work

Read `AGENTS.md`, `README.md §QR`, `CLAUDE.md`, `.claude/rules/tooling.md`, and relevant MEMORY pitfalls. Load Ponytail for code work and only the rules for affected paths (including testing rules for tests). Read named C-01/C-04/C-05/C-08 roles only when coordinating those responsibilities. Missing facts or references: `정보 없음`. Bring experienced engineering judgment without claiming an employment history or certifications.

Define the requested behavior, affected G1/G2/G3 boundary, acceptance evidence, and authorized execution surface. Preserve soybean-oil scope, external-only inputs, canonical-target semantics, as-of/fold gates, and human oversight. Current repository hard rules outrank older role templates and imported tool advice. Do not access internal inventory because an older HITL example mentions it. All errors/warnings/project logs follow the Korean diagnostics convention. Pipelines use the approved parquet/DuckDB and SDK access patterns; never pickle.

Inspect dirty state and related callers before editing. Preserve others' changes. Use a `codex/` branch and PR; prefer an isolated worktree if the active checkout is being edited. If Windows prevents checkout of unrelated paths, a verified sparse worktree can isolate the change. Do not reset, stash, clean, or bulk-stage someone else's work.

## Choose and implement the repair

Trace the failing behavior end to end. Reuse current helpers before adding infrastructure or dependencies. Explain alternatives when they materially affect correctness, cost, reliability, or maintenance: current behavior, viable option, evidence, tradeoff, chosen correction, and acceptance check. Do not equate fewer lines or a fashionable tool with improvement.

Implement the authorized correction at its owning boundary and update affected callers/contracts together. For relevant operating risks, use [release-evidence.md](references/release-evidence.md). Do not add every control in that reference to every change. A collection warning is acceptable only if a separate required readiness gate still blocks downstream modeling on insufficient inputs.

Add credential-free synthetic regression tests that fail for the demonstrated defect, including negative/failure propagation when gates are touched. Keep real-data and credential-dependent tests in a separate integration layer. Pin approved runtime dependencies inside Docker; do not install a new framework on the host or replace project orchestration solely because a reference repository recommends it.

Run appropriate checks on the actual changed revision in the intended container when available. Verify critical runtime versions rather than assuming the image matches the Dockerfile. Recheck when new changes invalidate evidence. If a check is unavailable, preserve the failure and name the missing prerequisite. Do not mask it with warning-only flags, `|| true`, `continue-on-error`, retries with no stopping condition, or synthetic data presented as real.

## Review and release

Keep the implementation and review passes distinct. A read-only review must inspect the full final diff and changed-file coverage; its reviewer does not edit or delegate. Use `$nexus-code-review` or the available review-agent when applicable. Spawn an independent reviewer only when the user or applicable instructions authorize delegation; otherwise perform and label a separate self-review. Reproduce and resolve substantiated findings, then rerun affected checks. If the same failure persists after two attempted repairs without new evidence, stop speculative changes, preserve the failing evidence, and report the next diagnostic or approval needed. This does not cap the initial full-diff review or hide remaining findings.

Prepare a skills/code-only PR with the concrete before/after behavior, alternatives/rationale where useful, validation evidence, remaining blockers, and rollback or compatibility implications. Stage explicit paths; never add generated raw/model data, credentials, account identifiers, or confidential operational context. Do not post reviews, request reviewers, merge, push, publish, or deploy unless the user's task or repository delivery instructions authorize the specific action; repository PR delivery does not authorize deployment or outreach.

Treat a deploy as a separate decision on concrete evidence. For production-data writes or procurement-affecting outputs, follow CLAUDE's Explore → Plan → Validate → explicitly approved Execute gate, using the host's planning surface when available. If the required planning surface is unavailable, prepare the plan read-only and report the limitation; never bypass the approval. No autonomous Buy/Hold action.

Return the change and verified results first, followed by material limitations. Distinguish code verified, synthetic behavior verified, real-data integration verified, and deployment verified. Missing critical evidence blocks readiness. Customer-facing statements must match the proven scope: historical G1 references, measured G2 intervals, and G3 market-cost/per-MT regret where validated. Never promise company P&L savings, customer acquisition, or production certification from passing tests alone.
