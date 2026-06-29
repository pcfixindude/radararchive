# Project State

Current phase: Phase 93 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated scaffold review** — refreshes preflight, resolves blockers, generates dry-run plan and scaffold only when upstream gates open
- **Gated dry-run plan review** — refreshes preflight, resolves blockers, generates dry-run plan only when `candidate_preflight_ready`
- **Visual sample set bootstrap** — creates sample set, seeds annotations, refreshes readiness
- **Trend-hint chain bootstrap** — seeds comparison history and refreshes upstream sandbox chain
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 93)

```bash
make mrms-review-gated-scaffold ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by gated scaffold review):

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"   # only when preflight is candidate_preflight_ready
make mrms-render-candidate-scaffold ARGS="--refresh"     # only when dry-run plan is dry_run_plan_ready
```

When preflight is not `candidate_preflight_ready`:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-bootstrap-visual-sample-set ARGS="--refresh"      # if visual evidence is the blocker
```

When dry-run plan is not `dry_run_plan_ready`:

```bash
make mrms-review-gated-dry-run-plan ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_gated_scaffold_review` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-scaffold-review`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
