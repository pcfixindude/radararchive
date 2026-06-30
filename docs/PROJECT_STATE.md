# Project State

Current phase: Phase 102 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Validation remediation** — classifies stub-mode validation/proof failures; documents for preflight without clearing alerts
- **Preflight attention resolution** — integrates validation remediation on refresh
- **Readiness milestone audit** — consolidates gated chain; local result readiness_ready after Phase 102
- **Preflight**: `candidate_preflight_ready` (stub-mode documented; not verified MRMS)
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 102)

```bash
make mrms-remediate-validation ARGS="--refresh"
make mrms-resolve-preflight-attention ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```

Artifacts:

- `data/dev/mrms_render_candidate_validation_remediation_latest.json`
- `data/dev/mrms_render_candidate_preflight_attention_latest.json`

Validation alert remains `failed` by design — stub-mode limitations documented for preflight path only.

## Continue gated chain (Phase 103)

```bash
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-review-gated-comparison ARGS="--refresh"
make mrms-review-gated-trend ARGS="--refresh"
make mrms-review-gated-ack ARGS="--refresh"
make mrms-review-gated-ack-history ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_validation_remediation` compact on validation summary.

## Verified MRMS

`verified_mrms` is **false** everywhere.
