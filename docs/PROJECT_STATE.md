# Project State

Current phase: Phase 94 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated sandbox layout** — refreshes preflight, resolves blockers, generates dry-run plan, scaffold, and sandbox layout only when upstream gates open
- **Gated scaffold review** — refreshes preflight, resolves blockers, generates dry-run plan and scaffold only when gated
- **Gated dry-run plan review** — refreshes preflight, resolves blockers, generates dry-run plan only when `candidate_preflight_ready`
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 94)

```bash
make mrms-review-gated-sandbox-layout ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by gated sandbox layout review):

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"   # only when preflight is candidate_preflight_ready
make mrms-review-gated-scaffold ARGS="--refresh"       # only when dry-run plan is dry_run_plan_ready
make mrms-render-candidate-sandbox ARGS="--refresh"      # only when scaffold is scaffold_ready
```

When preflight is not `candidate_preflight_ready`:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-bootstrap-visual-sample-set ARGS="--refresh"      # if visual evidence is the blocker
```

When scaffold is not `scaffold_ready`:

```bash
make mrms-review-gated-scaffold ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_gated_sandbox_layout` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-layout-review`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
