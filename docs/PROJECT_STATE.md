# Project State

Current phase: Phase 78 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status** — local rollup linking trend hints to trend review acknowledgments
- **Render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment** — local acknowledgment of reviewed trend hints
- **Render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend hints** — local advisory trends from status history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 78)

```bash
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status --refresh
```

## Dev API

`mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status` for local status rollup (`needs_acknowledgment` is not production authorization).

## Verified MRMS

`verified_mrms` is **false** everywhere.
