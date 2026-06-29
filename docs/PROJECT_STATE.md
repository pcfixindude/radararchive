# Project State

Current phase: Phase 86 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Candidate trend-hint review digest diff** — local diff between consecutive review digests
- **Candidate trend-hint review digest history** — bounded local history of review digests
- **Candidate trend-hint review chain digest** — local digest combining rollup and history
- **Candidate trend-hint acknowledgment status history** — bounded local history of acknowledgment status rollups
- **Candidate trend-hint acknowledgment status rollup** — local rollup linking trend hints to acknowledgments
- **Candidate trend-hint review acknowledgments** — local acknowledgment of reviewed candidate trend hints
- **Candidate trend hints** (Phase 80 chain) — local advisory trends from status history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 86)

```bash
make mrms-render-candidate-trend-hint-review-digest --refresh
make mrms-render-candidate-trend-hint-review-digest-history --refresh
make mrms-render-candidate-trend-hint-review-digest-diff --refresh
```

## Dev API

`mrms_render_candidate_trend_hint_review_digest_diff` compact on validation summary; `GET /api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest/diff` for local trend-hint review digest diff (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
