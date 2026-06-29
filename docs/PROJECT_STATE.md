# Project State

Current phase: Phase 72 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison acknowledgment status trend hints** — local advisory trends from status history
- **Render candidate sandbox comparison acknowledgment status history** — bounded local history of status rollups
- **Render candidate sandbox comparison acknowledgment status** — local rollup linking trend hints to acknowledgments
- **Render candidate sandbox comparison review acknowledgment** — local operator acknowledgment of reviewed trend hints
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 72)

```bash
make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint --refresh
```

## Dev API

`mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-hint` for local trend hints (`needs_review` is not production authorization).

## Verified MRMS

`verified_mrms` is **false** everywhere.
