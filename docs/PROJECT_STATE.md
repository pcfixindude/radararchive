# Project State

Current phase: Phase 70 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison acknowledgment status** — local rollup linking trend hints to acknowledgments
- **Render candidate sandbox comparison review acknowledgment** — local operator acknowledgment of reviewed trend hints
- **Render candidate sandbox comparison trend hints** — local advisory trend analysis from comparison history
- **Render candidate sandbox comparison history** — bounded local history JSON/Markdown
- **Render candidate sandbox import/export** — local metadata export/import
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 70)

```bash
make mrms-render-candidate-sandbox-comparison-trend-hint --refresh
make mrms-render-candidate-sandbox-comparison-review-acknowledgment --operator OP --note "Reviewed locally"
make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh
```

## Dev API

`mrms_render_candidate_sandbox_comparison_acknowledgment_status` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status` for local status rollup (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
