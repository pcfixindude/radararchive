# Project State

Current phase: Phase 95 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated manifest import/export** — refreshes upstream gates and runs manifest IO only when sandbox layout is `sandbox_layout_ready`
- **Gated sandbox layout** — refreshes upstream gates and generates sandbox layout only when scaffold is `scaffold_ready`
- **Gated scaffold review** — refreshes preflight, resolves blockers, generates dry-run plan and scaffold only when gated
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 95)

```bash
make mrms-review-gated-manifest-io ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by gated manifest IO review):

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-render-candidate-sandbox-import-export ARGS="--refresh"   # only when sandbox layout is sandbox_layout_ready
```

When preflight is not `candidate_preflight_ready`:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-bootstrap-visual-sample-set ARGS="--refresh"      # if visual evidence is the blocker
```

When sandbox layout is not `sandbox_layout_ready`:

```bash
make mrms-review-gated-sandbox-layout ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_gated_manifest_io` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-manifest-io`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
