# Next Steps

## Phase 95 - Gated candidate sandbox manifest import/export (Draft)

Goal: Run gated local sandbox manifest import/export when sandbox layout is `sandbox_layout_ready`.

```bash
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-render-candidate-sandbox-import-export ARGS="--refresh"
```

## Phase 94 verification commands

```bash
make test
make mrms-review-gated-sandbox-layout ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 94 gated sandbox layout review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `dry_run_plan_skipped`: `true`
- `scaffold_skipped`: `true`
- `sandbox_skipped`: `true`
- Sandbox layout correctly not generated — resolve preflight first

Retry when upstream gates open:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
```

Remaining preflight blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Dry-run blocker: dry-run plan not generated — preflight gate closed
- Scaffold blocker: scaffold not generated — upstream gate closed
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
