# Next Steps

## Phase 99 - Gated sandbox acknowledgment history (Draft)

Goal: Run gated local sandbox acknowledgment history when comparison acknowledgment is `comparison_ack_ready` or `comparison_ack_needs_acknowledgment`.

```bash
make mrms-review-gated-ack ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history ARGS="--refresh"
```

## Phase 98 verification commands

```bash
make test
make mrms-review-gated-ack ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 98 gated comparison acknowledgment review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `trend_skipped`: `true`
- `ack_skipped`: `true`
- Comparison acknowledgment correctly not run — resolve preflight first

Retry when upstream gates open:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-review-gated-comparison ARGS="--refresh"
make mrms-review-gated-trend ARGS="--refresh"
make mrms-review-gated-ack ARGS="--refresh"
```

Remaining blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Sandbox layout blocker: sandbox layout not generated — upstream gate closed
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
