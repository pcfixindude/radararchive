# Project State

Current phase: Phase 101 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Preflight attention resolution** — inventories operator attention items, clears safe advisory items only, documents human-judgment blockers
- **Readiness milestone audit** — consolidates preflight through gated ack history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 101)

```bash
make mrms-resolve-preflight-attention ARGS="--refresh"
make operator-review-status ARGS="--refresh"
```

Preflight attention report:

- `data/dev/mrms_render_candidate_preflight_attention_latest.json`
- `data/dev/mrms_render_candidate_preflight_attention_latest.md`

Current local state (after Phase 101):

- Preflight: `needs_review`
- Attention resolution: `attention_blocked` (validation alert + proof report failures require human judgment)
- Validation alert: unchanged (`failed`)

```bash
make validation-failures
make mrms-proof-report ARGS="--refresh"
make operator-review-status ARGS="--refresh"
make mrms-resolve-preflight-attention ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
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

`mrms_render_candidate_preflight_attention` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/preflight-attention`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
