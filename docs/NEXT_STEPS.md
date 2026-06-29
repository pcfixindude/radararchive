# Next Steps

## Phase 90 - TBD (Draft)

Goal: Bootstrap sandbox comparison trend-hint chain so ack rollup and review digest unblock.

```bash
make mrms-render-candidate-sandbox-comparison-history ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-trend-hint ARGS="--refresh"
make mrms-render-candidate-trend-hint-ack-status ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
```

Parallel visual evidence (if still blocked):

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make mrms-visual-review-readiness ARGS="--refresh"
```

## Phase 89 verification commands

```bash
make test
make mrms-resolve-preflight-blockers ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```
