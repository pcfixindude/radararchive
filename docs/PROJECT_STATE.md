# Project State

Current phase: Phase 98 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated comparison acknowledgment** — refreshes upstream gates and runs acknowledgment status only when trend hint is `trend_hint_ready` or `trend_hint_needs_review`
- **Gated trend hint review** — refreshes upstream gates and runs comparison trend hints only when comparison history is `comparison_history_ready`
- **Gated comparison history** — refreshes upstream gates and runs comparison history only when manifest IO is `manifest_io_ready`
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 98)

```bash
make mrms-review-gated-ack ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by gated comparison acknowledgment review):

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-review-gated-comparison ARGS="--refresh"
make mrms-review-gated-trend ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-acknowledgment-status ARGS="--refresh"   # only when trend_hint_ready
```

When preflight is not `candidate_preflight_ready`:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-bootstrap-visual-sample-set ARGS="--refresh"      # if visual evidence is the blocker
```

When trend hint is not ready:

```bash
make mrms-review-gated-trend ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_gated_comparison_ack` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-ack-review`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
