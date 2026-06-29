# Next Steps

## Phase 96 - Gated sandbox comparison history (Draft)

Goal: Run gated local sandbox comparison history when manifest import/export is `manifest_io_ready`.

```bash
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-history ARGS="--refresh"
```

## Phase 95 verification commands

```bash
make test
make mrms-review-gated-manifest-io ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 95 gated manifest IO review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `dry_run_plan_skipped`: `true`
- `scaffold_skipped`: `true`
- `sandbox_skipped`: `true`
- `manifest_io_skipped`: `true`
- Manifest import/export correctly not run — resolve preflight first

Retry when upstream gates open:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
```

Remaining blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Dry-run blocker: dry-run plan not generated — preflight gate closed
- Scaffold blocker: scaffold not generated — upstream gate closed
- Sandbox layout blocker: sandbox layout not generated — upstream gate closed
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
