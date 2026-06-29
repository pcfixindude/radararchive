# Project State

Current phase: Phase 89 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Preflight blocker resolution** — orchestrates refresh flow and records specific remaining blockers
- **Gated preflight attempt** — runs preflight only when review readiness allows
- **Candidate review readiness** — consolidated trend-hint review chain summary
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 89)

```bash
make mrms-resolve-preflight-blockers ARGS="--refresh"
```

Full flow (run automatically by the command above):

```bash
make mrms-render-candidate-trend-hint-ack-status ARGS="--refresh"
make mrms-render-candidate-trend-hint-review-digest ARGS="--refresh"
make mrms-render-candidate-review-readiness ARGS="--refresh"
make mrms-visual-review-readiness ARGS="--refresh"
make mrms-render-candidate-preflight-attempt ARGS="--refresh"
```

## Dev API

`mrms_render_candidate_preflight_blockers` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/preflight-blockers`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
