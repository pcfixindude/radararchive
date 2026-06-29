# Project State

Current phase: Phase 87 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Candidate review readiness** — consolidated local summary of the trend-hint review chain plus gated preflight status
- **Candidate trend-hint review chain** — hints, acknowledgments, rollup, history, digest, digest history, digest diff (Phases 80–86)
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 87)

```bash
make mrms-render-candidate-review-readiness --refresh
make mrms-render-candidate-trend-hint-review-digest --refresh
make mrms-render-candidate-preflight --refresh
```

## Dev API

`mrms_render_candidate_review_readiness` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/review-readiness` for consolidated review readiness (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
