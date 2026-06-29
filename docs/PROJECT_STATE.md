# Project State

Current phase: Phase 68 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison trend hints** — local advisory trend analysis from comparison history
- **Render candidate sandbox comparison history** — bounded local history JSON/Markdown
- **Render candidate sandbox import/export** — local metadata export/import
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 68)

```bash
make mrms-render-candidate-sandbox-import-export
make mrms-render-candidate-sandbox-comparison-history
make mrms-render-candidate-sandbox-comparison-trend-hint
```

## Dev API

`mrms_render_candidate_sandbox_comparison_trend_hint` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-trend-hint` for local trend hints (`needs_review` is not production authorization).

## Verified MRMS

`verified_mrms` is **false** everywhere.
