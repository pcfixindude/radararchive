# Project State

Current phase: Phase 88 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Gated preflight attempt** — runs existing preflight only when review readiness allows; records blockers otherwise
- **Candidate review readiness** — consolidated local summary of trend-hint review chain plus preflight status
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 88)

```bash
make mrms-render-candidate-review-readiness ARGS="--refresh"
make mrms-render-candidate-trend-hint-review-digest ARGS="--refresh"
make mrms-render-candidate-preflight-attempt ARGS="--refresh"
```

When review readiness shows `ready_for_preflight`, the gated attempt runs `make mrms-render-candidate-preflight --refresh` automatically.

## Dev API

`mrms_render_candidate_preflight_attempt` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/preflight-attempt` for gated preflight attempts (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
