# Next Steps

## Phase 88 - TBD (Draft)

Goal: Gated real MRMS render candidate preflight attempt — use existing `make mrms-render-candidate-preflight --refresh` when review readiness shows `ready_for_preflight` and visual evidence blockers are cleared.

## Phase 87 verification commands

```bash
make test
make mrms-render-candidate-review-readiness --refresh
make mrms-render-candidate-trend-hint-review-digest --refresh
cd frontend && npm test
cd frontend && npm run build
```
