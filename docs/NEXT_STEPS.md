# Next Steps

## Phase 91 - Bootstrap visual review sample set (Draft)

Goal: Create local visual review sample set and annotations so visual sample readiness reaches `candidate_ready` and gated preflight can run.

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make mrms-visual-review-readiness ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
```

## Phase 90 verification commands

```bash
make test
make mrms-bootstrap-trend-hint-chain ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 90 bootstrap:

- `bootstrap_status`: `chain_ready_visual_blocked`
- `rollup_status`: `not_needed`
- `digest_status`: `stable`
- `chain_readiness_level`: `chain_ready`
- `overall_readiness_level`: `ready_for_preflight`
- `preflight_not_run`: `true`
- Remaining blocker: `visual sample readiness: no_sample_set`
