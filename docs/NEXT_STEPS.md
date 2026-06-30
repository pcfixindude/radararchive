# Next Steps

## Phase 101 - Resolve operator review attention items for preflight (Draft)

Goal: Clear open operator review attention items so preflight can advance from `needs_review` to `candidate_preflight_ready`.

```bash
make operator-review-status ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```

## Phase 100 verification commands

```bash
make test
make mrms-readiness-milestone-audit ARGS="--refresh"
```

Local result after Phase 100 milestone audit:

- `audit_status`: `readiness_blocked`
- `preflight_level`: `needs_review`
- `root_gate`: `preflight`
- `blocker_category`: `operator_action`
- `add_gated_wrapper_recommended`: `false`
- All downstream gated steps (`dry_run_plan` through `ack_history`) blocked only because preflight is blocked

Shortest safe retry after fixes:

```bash
make operator-review-status ARGS="--refresh"
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

Remaining blockers/warnings (local dev):

- Blocker: preflight level is `needs_review` (need `candidate_preflight_ready`)
- Warning: no local wgrib2/GDAL detected — future real render path may need tooling
- Warning: operator review status indicates open attention items
