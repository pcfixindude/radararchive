# Next Steps

## Phase 92 - Gated render candidate dry-run plan review (Draft)

Goal: Evaluate the dry-run plan when preflight is `candidate_preflight_ready` or after reviewing the latest gated preflight attempt.

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-render-candidate-dry-run-plan ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
```

## Phase 91 verification commands

```bash
make test
make mrms-bootstrap-visual-sample-set ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

Local result after Phase 91 bootstrap:

- `bootstrap_status`: `preflight_attempted`
- `visual_readiness_level`: `candidate_ready`
- `visual_readiness_reason`: `all_samples_acceptable`
- `review_readiness_level`: `ready_for_preflight`
- `preflight_not_run`: `false`
- Gated preflight advisory captured — review preflight report before dry-run plan
