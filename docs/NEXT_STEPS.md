# Next Steps

## Phase 100 - Gated sandbox acknowledgment trend hint (Draft)

Goal: Run gated local sandbox acknowledgment trend hints when acknowledgment history is `ack_history_ready`.

```bash
make mrms-review-gated-ack-history ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint ARGS="--refresh"
```

## Phase 99 verification commands

```bash
make test
make mrms-review-gated-ack-history ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 99 gated acknowledgment history review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `ack_skipped`: `true`
- `history_skipped`: `true`
- Acknowledgment history correctly not run — resolve preflight first

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
make mrms-review-gated-ack-history ARGS="--refresh"
```

Remaining blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Sandbox layout blocker: sandbox layout not generated — upstream gate closed
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
