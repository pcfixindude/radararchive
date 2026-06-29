# Project State

Current phase: Phase 73 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison acknowledgment status trend review acknowledgment** — local operator acknowledgment of reviewed status trend hints
- **Render candidate sandbox comparison acknowledgment status trend hints** — local advisory trends from status history
- **Render candidate sandbox comparison acknowledgment status history** — bounded local history of status rollups
- **Render candidate sandbox comparison acknowledgment status** — local rollup linking trend hints to acknowledgments
- **Render candidate sandbox comparison review acknowledgment** — local operator acknowledgment of reviewed trend hints
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 73)

```bash
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint --refresh
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment --operator OP --note "Reviewed locally"
```

## Dev API

`mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgments` for local acknowledgments (does not clear alerts or authorize production).

## Verified MRMS

`verified_mrms` is **false** everywhere.
