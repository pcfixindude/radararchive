# Project State

Current phase: Phase 74 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison acknowledgment status trend review acknowledgment status** — local rollup linking status trend hints to trend review acknowledgments
- **Render candidate sandbox comparison acknowledgment status trend review acknowledgment** — local operator acknowledgment of reviewed status trend hints
- **Render candidate sandbox comparison acknowledgment status trend hints** — local advisory trends from status history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 74)

```bash
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment --operator OP --note "Reviewed locally"
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status --refresh
```

## Dev API

`mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status` for local rollup (does not clear alerts or authorize production).

## Verified MRMS

`verified_mrms` is **false** everywhere.
