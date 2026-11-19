# Verification surfaces and safe execution

These paths were inspected on 2026-11-19. Re-read their current implementation before relying on them; the active checkout may contain another agent's uncommitted changes.

| Surface | Starting evidence | Verification boundary |
|---|---|---|
| Container/dependencies | `docker/Dockerfile`, `docker/requirements.txt`, `.claude/rules/libraries.md` | Compare actual image/runtime with declared Python/library versions; do not assume a lock or successful build from documentation |
| Orchestration | `docker/compose.yml`, `docker/jobs.py`, relevant `docker/n8n/*.json` | Follow fixed job arguments, exit codes, required/optional steps, locks, timeouts, and workflow failure branches |
| Canonical target | `scripts/validate_session_close.py`, `scripts/ingest_databento_bo.py`, `data/gold/feature_contract.yaml` | Target semantics and provenance; session validation may fetch network samples and write canonical output, so it is an integration action |
| Temporal input | `src/pipeline/asof.py`, `src/features/build_feature_mart.py`, `scripts/validate_asof.py` | Producer availability plus actual prediction cutoff selection; inspect CLI/report side effects before use |
| Model readiness | `scripts/data_readiness.py`, `docs/operations/g1_g2_preview_release_gates.md` | Check current contract thresholds; do not silently lower them or rely on a stale report |
| Snapshot lineage | `scripts/build_snapshot_manifest.py` and its consumers | SHA256, source run/revision, row counts/schema, immutable manifest and actual verification before consumption |
| Existing synthetic gates | `tests/test_milestone_gates.py`, relevant `tests/test_asof_observed_cap.py` | Failure behavior with synthetic data; passing is not real-source/session validation |
| PR enforcement | `.github/workflows/quality_gate.yml` plus downstream workflows | Inspect trigger paths, dependencies, skipped checks, required statuses, and artifact provenance, including Docker/skill-only changes |

## Non-mutating preflight

From the identified repository root:

```text
git status --short
git rev-parse HEAD
docker compose version
docker compose -f docker/compose.yml config --quiet
docker compose -f docker/compose.yml ps --services --status running
```

`config --quiet` avoids printing resolved environment secrets. Do not print full compose configuration, `.env`, auth files, process environments, or unrestricted container inspections. A local Docker check can be blocked by missing environment expansion or unavailable mounts; report that result and use an isolated fixture only with clearly stated limits.

If a runner already exists, inspect the selected test's code, fixtures and imports first. A targeted synthetic suite can then run with caches and temporary files outside the repository:

```text
docker compose -f docker/compose.yml exec -T runner python -B -m pytest -q -p no:cacheprovider --basetemp=/tmp/nexus-verification tests/test_milestone_gates.py
```

Use a unique temporary directory if checks might overlap. This is an example, not a blanket claim that all current tests are side-effect-free. Do not run `POST /run/mart`, `baseline`, `databento`, `codex_crawl`, `codex_verify`, or the blanket `tests` job without inspecting them and establishing authorization. The mart job can publish data; the full test suite can include artifact-dependent tests. `docker compose up`, image rebuilds, workflow imports/activation, and service restarts alter the running environment; use an isolated project when authorized and needed. Never mount or copy host login credentials into a fixture container.

For real-source verification, use the approved immutable snapshot/artifact store with known rights and human authorization where required. Do not pull licensed data or invent rows merely to make a gate pass. Reconcile code/docs disagreement against current hard rules and call paths; document the discrepancy instead of silently accepting the weaker behavior.
