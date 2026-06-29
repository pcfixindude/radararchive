# Project State

Current phase: Phase 69 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison review acknowledgment** — local operator acknowledgment of reviewed trend hints
- **Render candidate sandbox comparison trend hints** — local advisory trend analysis from comparison history
- **Render candidate sandbox comparison history** — bounded local history JSON/Markdown
- **Render candidate sandbox import/export** — local metadata export/import
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 69)

```bash
make mrms-render-candidate-sandbox-comparison-trend-hint
make mrms-render-candidate-sandbox-comparison-review-acknowledgment --operator OP --note "Reviewed locally"
```

## Dev API

`mrms_render_candidate_sandbox_comparison_review_acknowledgment` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments` for local acknowledgments (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
