# Next Steps

## Phase 98 - Gated sandbox comparison acknowledgment (Draft)

Goal: Run gated local sandbox comparison acknowledgment when trend hint is `trend_hint_ready` or `trend_hint_needs_review`.

```bash
make mrms-review-gated-trend ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-review-acknowledgment ARGS="--refresh"
```

## Phase 97 verification commands

```bash
make test
make mrms-review-gated-trend ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 97 gated trend hint review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `comparison_skipped`: `true`
- `trend_skipped`: `true`
- Trend hints correctly not run — resolve preflight first

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
```

Remaining blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Sandbox layout blocker: sandbox layout not generated — upstream gate closed
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
