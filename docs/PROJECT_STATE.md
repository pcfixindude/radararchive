# Project State

Current phase: Phase 62 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate preflight** — local advisory checklist JSON/Markdown, conservative blocking/warnings, Dev Validation UI
- **Visual review sample-set annotations & readiness** — local annotation JSON, readiness Markdown, conservative advisory scoring
- **Visual review sample-set drilldown** — local JSON/Markdown sample set, recommended selection, Dev Validation UI
- **Scheduled visual review workflow** — optional `--visual-review` scheduled step and `make scheduled-proof-bundle-visual-review`
- **Visual review operator integration** — stale visual review feeds operator review status and workflow presets
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 62)

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make mrms-visual-review-readiness
make mrms-render-candidate-preflight
make scheduled-proof-bundle-visual-review
make operator-review-status
make operator-workflow-presets
```

## Dev API

`mrms_render_candidate_preflight` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/preflight` for local advisory preflight (`candidate_preflight_ready` is not production authorization). Sample-set and readiness endpoints from Phases 60–61 unchanged. Default `make scheduled-validation` unchanged.

## Verified MRMS

`verified_mrms` is **false** everywhere.
