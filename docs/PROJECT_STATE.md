# Project State

Current phase: Phase 92 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated dry-run plan review** — refreshes preflight, resolves blockers, generates dry-run plan only when `candidate_preflight_ready`
- **Visual sample set bootstrap** — creates sample set, seeds annotations, refreshes readiness
- **Trend-hint chain bootstrap** — seeds comparison history and refreshes upstream sandbox chain
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 92)

```bash
make mrms-review-gated-dry-run-plan ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by gated review):

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-render-candidate-dry-run-plan ARGS="--refresh"   # only when preflight is candidate_preflight_ready
```

When preflight is not `candidate_preflight_ready`:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-bootstrap-visual-sample-set ARGS="--refresh"      # if visual evidence is the blocker
```

## Dev API

`mrms_render_candidate_gated_dry_run_review` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-dry-run-review`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
