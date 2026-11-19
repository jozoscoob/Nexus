# Release evidence by changed boundary

Use the controls relevant to the authorized work. These are review criteria, not claims that the controls already exist. Verify thresholds and supported commands from current code and official version-specific documentation.

| Boundary | Evidence needed before calling it ready |
|---|---|
| Image and dependencies | Reproducible build with compatible approved pins, actual installed versions, startup/import smoke check; base-image provenance and vulnerability review when in scope |
| Runner and n8n | Fixed/validated job selection, bounded timeouts and retries, required failure propagated to workflow, concurrency behavior, safe interruption/retry and idempotency; no duplicate publication |
| Trust and secrets | Minimum required privileges/mounts, secret redaction, job endpoint access matched to deployment, no credentials embedded in image/artifacts/logs, no execution of untrusted agent/source instructions |
| Data/model entry | Canonical target plus as-of and snapshot gates; negative tests show modeling cannot run with missing/invalid inputs; fold-local fit/selection/calibration and horizon-aware label separation |
| CI/CD | Actual changed paths trigger validation; required checks cannot succeed by skip, warning, or absent artifacts; immutable artifact lineage tied to tested commit/image; least workflow permissions; untrusted PRs cannot obtain privileged credentials |
| Publication/storage | Atomic or recoverable output publication, source vintages preserved, snapshot hash/schema verified on consumption; raw/model data kept outside Git; licensed material not exported without rights |
| Operations | Observable run/stage/result/duration and freshness, bounded failure alerts with no secrets, disk/retention behavior, documented restore/rollback and a safe drill when authorized |
| Customer delivery | Demonstrable intended use, evidence-linked limitations, human approval boundary, ownership/support path, data licensing and reproducibility; no unsupported SLA or business-value promise |

Do not change model promotion metrics or lower target coverage just to achieve a release. Consult `.claude/rules/modeling.md` and `docs/operations/g1_g2_preview_release_gates.md` for the requested model scope; documentation may lag implementation, so state conflicts and resolve them against hard gates.

## Minimal readiness record

For each acceptance criterion record:

```text
Criterion:
Revision and dirty-state scope:
Input snapshot/fixture and execution surface:
Command or inspected call path:
Observed result / exit status:
Status: PASS | FAIL | BLOCKED | NOT_RUN
Remaining risk and next required evidence:
```

Do not publish resolved environment variables or infrastructure detail in the record. Keep actual results distinct from proposed commands. Synthetic contract validation, real-source correctness, and deployment health are different claims. A required FAIL/BLOCKED/NOT_RUN prevents a production-ready verdict. A code-only change may be complete while release readiness remains unverified.
