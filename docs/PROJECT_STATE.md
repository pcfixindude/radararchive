# Project State

Current phase: Phase 81 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Candidate trend-hint review acknowledgments** — local acknowledgment of reviewed candidate trend hints
- **Candidate trend hints** (Phase 80 chain) — local advisory trends from status history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 81)

```bash
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh
make mrms-render-candidate-trend-hint-review-acknowledgment --operator OP --note "Reviewed locally"
```

## Dev API

`mrms_render_candidate_trend_hint_review_acknowledgment` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-review-acknowledgments` for local trend-hint review acknowledgments (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
