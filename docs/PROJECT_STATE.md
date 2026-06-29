# Project State

Current phase: Phase 97 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated trend hint review** — refreshes upstream gates and runs comparison trend hints only when comparison history is `comparison_history_ready`
- **Gated comparison history** — refreshes upstream gates and runs comparison history only when manifest IO is `manifest_io_ready`
- **Gated manifest import/export** — refreshes upstream gates and runs manifest IO only when sandbox layout is `sandbox_layout_ready`
- **Gated sandbox layout** — refreshes upstream gates and generates sandbox layout only when scaffold is `scaffold_ready`
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 97)

```bash
make mrms-review-gated-trend ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by gated trend hint review):

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-review-gated-comparison ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-trend-hint ARGS="--refresh"   # only when comparison_history_ready
```

When preflight is not `candidate_preflight_ready`:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-bootstrap-visual-sample-set ARGS="--refresh"      # if visual evidence is the blocker
```

When comparison history is not `comparison_history_ready`:

```bash
make mrms-review-gated-comparison ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_gated_trend_review` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-trend-review`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
