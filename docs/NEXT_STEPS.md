# Next Steps

## Phase 97 - Gated sandbox comparison trend hint (Draft)

Goal: Run gated local sandbox comparison trend hints when comparison history is `comparison_history_ready`.

```bash
make mrms-review-gated-comparison ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-trend-hint ARGS="--refresh"
```

## Phase 96 verification commands

```bash
make test
make mrms-review-gated-comparison ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 96 gated comparison history review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `manifest_io_skipped`: `true`
- `comparison_skipped`: `true`
- Comparison history correctly not run — resolve preflight first

Retry when upstream gates open:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-review-gated-comparison ARGS="--refresh"
```

Remaining blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Sandbox layout blocker: sandbox layout not generated — upstream gate closed
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
