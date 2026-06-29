# Project State

Current phase: Phase 99 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated acknowledgment history** — refreshes upstream gates and runs acknowledgment history only when comparison acknowledgment is `comparison_ack_ready` or `comparison_ack_needs_acknowledgment`
- **Gated comparison acknowledgment** — refreshes upstream gates and runs acknowledgment status only when trend hint is ready
- **Gated trend hint review** — refreshes upstream gates through comparison history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 99)

```bash
make mrms-review-gated-ack-history ARGS="--refresh"
```

Equivalent step-by-step flow (run automatically by gated acknowledgment history review):

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-review-gated-comparison ARGS="--refresh"
make mrms-review-gated-trend ARGS="--refresh"
make mrms-review-gated-ack ARGS="--refresh"
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history ARGS="--refresh"   # only when comparison_ack_ready
```

When preflight is not `candidate_preflight_ready`:

```bash
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-bootstrap-visual-sample-set ARGS="--refresh"      # if visual evidence is the blocker
```

When comparison acknowledgment is not ready:

```bash
make mrms-review-gated-ack ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_gated_ack_history` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-ack-history`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
