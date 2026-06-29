# Project State

Current phase: Phase 91 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Visual sample set bootstrap** — creates sample set, seeds acceptable annotations, refreshes readiness, resolves blockers
- **Trend-hint chain bootstrap** — seeds comparison history and refreshes upstream sandbox chain
- **Preflight blocker resolution** — orchestrates refresh flow; skips gated preflight when visual sample readiness is blocked
- **Gated preflight attempt** — runs preflight when review readiness allows
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 91)

```bash
make mrms-bootstrap-visual-sample-set ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by bootstrap):

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make mrms-visual-review-readiness ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
```

After bootstrap when preflight attempt ran:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-render-candidate-dry-run-plan ARGS="--refresh"
```

## Dev API

`mrms_visual_review_sample_bootstrap` compact on validation summary; `GET/POST /api/validation/mrms-visual-review/sample-set/bootstrap`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
