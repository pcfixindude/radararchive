# Next Steps

## Phase 89 - TBD (Draft)

Goal: Resolve visual evidence and review-chain preflight blockers so gated preflight can reach `candidate_preflight_ready`.

### Blocker-removal commands (current dev tree)

```bash
make mrms-render-candidate-trend-hint-ack-status ARGS="--refresh"
make mrms-render-candidate-trend-hint-review-digest ARGS="--refresh"
make mrms-render-candidate-review-readiness ARGS="--refresh"
make mrms-render-candidate-preflight-attempt ARGS="--refresh"
make mrms-visual-review-readiness ARGS="--refresh"
```

## Phase 88 verification commands

```bash
make test
make mrms-render-candidate-review-readiness ARGS="--refresh"
make mrms-render-candidate-preflight-attempt ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```
