# Project State

Current phase: Phase 67 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox comparison history** — bounded local history JSON/Markdown, advisory import/export comparisons
- **Render candidate sandbox import/export** — local metadata export/import JSON/Markdown
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 67)

```bash
make mrms-render-candidate-sandbox-export
make mrms-render-candidate-sandbox-import-export
make mrms-render-candidate-sandbox-comparison-history
```

## Dev API

`mrms_render_candidate_sandbox_comparison_history` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-history` for local comparison history (`ready` is not production authorization).

## Verified MRMS

`verified_mrms` is **false** everywhere.
