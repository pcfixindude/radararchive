# Next Steps

## Phase 94 - Gated candidate artifact sandbox layout (Draft)

Goal: Generate gated local sandbox directory layout when scaffold review is `scaffold_ready`.

```bash
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-render-candidate-sandbox ARGS="--refresh"
```

## Phase 93 verification commands

```bash
make test
make mrms-review-gated-scaffold ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 93 gated scaffold review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `dry_run_plan_skipped`: `true`
- `scaffold_skipped`: `true`
- Scaffold correctly not generated — resolve preflight first

Retry when preflight is ready:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
```

Remaining preflight blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
