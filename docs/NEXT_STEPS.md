# Next Steps

## Phase 102 - Remediate validation alert failures for preflight (Draft)

Goal: Address or document stub-mode validation failures so operator review status can improve and preflight can advance toward `candidate_preflight_ready`.

```bash
make validation-failures
make mrms-proof-report ARGS="--refresh"
make operator-review-status ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```

## Phase 101 verification commands

```bash
make test
make operator-review-status ARGS="--refresh"
make mrms-resolve-preflight-attention ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```

Local result after Phase 101 attention resolution:

- `resolution_status`: `attention_blocked`
- `blocks_preflight`: `true`
- `preflight_level`: `needs_review` (unchanged)
- `validation_alert_unchanged`: `true` (alert still `failed`)
- `add_gated_wrapper_recommended`: `false`

Blocking attention items (human judgment — kept open):

1. Validation alert: operator attention needed — review `make validation-failures`
2. Latest proof report overall_status: failed — run `make mrms-proof-report`
3. Operator review status: validation alert failed

Remaining preflight warning:

- no local wgrib2/GDAL detected — tooling warning (non-blocking for attention resolution)

Retry after remediation:

```bash
make validation-failures
make mrms-proof-report ARGS="--refresh"
make operator-review-status ARGS="--refresh"
make mrms-resolve-preflight-attention ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```

When preflight reaches `candidate_preflight_ready`, continue gated chain:

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
