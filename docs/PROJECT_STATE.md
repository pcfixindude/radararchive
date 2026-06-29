# Project State

Current phase: Phase 90 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Trend-hint chain bootstrap** — seeds comparison history and refreshes upstream sandbox chain through ack rollup and review digest
- **Preflight blocker resolution** — orchestrates refresh flow; skips gated preflight when visual sample readiness is blocked
- **Gated preflight attempt** — runs preflight only when review readiness allows
- **Candidate review readiness** — consolidated trend-hint review chain summary
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 90)

```bash
make mrms-bootstrap-trend-hint-chain ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by bootstrap):

```bash
make mrms-render-candidate-sandbox-comparison-trend-hint ARGS="--refresh"
make mrms-render-candidate-trend-hint-ack-status ARGS="--refresh"
make mrms-render-candidate-trend-hint-review-digest ARGS="--refresh"
make mrms-render-candidate-review-readiness ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
```

When trend-hint chain is ready but visual sample set is missing:

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make mrms-visual-review-readiness ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_trend_hint_chain_bootstrap` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
