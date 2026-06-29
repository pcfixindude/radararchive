# Next Steps

## Phase 93 - Gated render candidate scaffold review (Draft)

Goal: Evaluate the disabled-by-default render candidate scaffold when dry-run plan is `dry_run_plan_ready`.

```bash
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-render-candidate-scaffold ARGS="--refresh"
```

## Phase 92 verification commands

```bash
make test
make mrms-review-gated-dry-run-plan ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 92 gated review:

- `review_status`: `preflight_not_candidate_ready`
- `preflight_level`: `needs_review`
- `dry_run_plan_skipped`: `true`
- `dry_run_plan_status`: `null`
- Dry-run plan correctly not generated — resolve preflight first

Retry when preflight is ready:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
```
