# Project State

Current phase: Phase 100 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Readiness milestone audit** — consolidates preflight through gated ack history; identifies root blocker and stops gated-wrapper recursion
- **Gated acknowledgment history** — refreshes upstream gates and runs acknowledgment history only when comparison acknowledgment is ready
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 100)

```bash
make mrms-readiness-milestone-audit ARGS="--refresh"
```

One command refreshes the full gated chain and writes consolidated audit:

- `data/dev/mrms_render_candidate_readiness_milestone_audit_latest.json`
- `data/dev/mrms_render_candidate_readiness_milestone_audit_latest.md`

When preflight is not `candidate_preflight_ready` (current local state):

```bash
make operator-review-status ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-resolve-preflight-blockers ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```

When preflight is `candidate_preflight_ready`, continue gated chain:

```bash
make mrms-review-gated-dry-run-plan ARGS="--refresh"
make mrms-review-gated-scaffold ARGS="--refresh"
make mrms-review-gated-sandbox-layout ARGS="--refresh"
make mrms-review-gated-manifest-io ARGS="--refresh"
make mrms-review-gated-comparison ARGS="--refresh"
make mrms-review-gated-trend ARGS="--refresh"
make mrms-review-gated-ack ARGS="--refresh"
make mrms-review-gated-ack-history ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_readiness_milestone_audit` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/readiness-milestone-audit`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
