# Project State

Current phase: Phase 84 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Candidate trend-hint review chain digest** — local digest combining rollup and history
- **Candidate trend-hint acknowledgment status history** — bounded local history of acknowledgment status rollups
- **Candidate trend-hint acknowledgment status rollup** — local rollup linking trend hints to acknowledgments
- **Candidate trend-hint review acknowledgments** — local acknowledgment of reviewed candidate trend hints
- **Candidate trend hints** (Phase 80 chain) — local advisory trends from status history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 84)

```bash
make mrms-render-candidate-trend-hint-ack-status --refresh
make mrms-render-candidate-trend-hint-review-digest --refresh
```

## Dev API

`mrms_render_candidate_trend_hint_review_digest` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest` for local trend-hint review chain digest (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
