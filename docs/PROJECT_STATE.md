# Project State

Current phase: Phase 66 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate sandbox import/export** — local metadata export/import JSON/Markdown, advisory comparison, schema version 1.0
- **Render candidate artifact sandbox** — local `data/dev/` sandbox layout, manifest/report JSON/Markdown, report-only cleanup
- **Render candidate command scaffold** — disabled-by-default local scaffold JSON/Markdown, hard safety gates, dry-run/no-op default
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 66)

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make mrms-visual-review-readiness
make mrms-render-candidate-preflight
make mrms-render-candidate-dry-run-plan
make mrms-render-candidate-scaffold
make mrms-render-candidate-sandbox
make mrms-render-candidate-sandbox-export
make mrms-render-candidate-sandbox-import-export
make operator-review-status
make operator-workflow-presets
```

## Dev API

`mrms_render_candidate_sandbox_import_export` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export` (+ `/export`, `/import`) for local metadata import/export (`imported` is not production authorization). Sandbox, scaffold, and earlier render-candidate endpoints unchanged.

## Verified MRMS

`verified_mrms` is **false** everywhere.
