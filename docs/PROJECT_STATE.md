# Project State

Current phase: Phase 63 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Render candidate dry-run plan** — local advisory plan JSON/Markdown, prerequisites/stop conditions, future commands not run now
- **Render candidate preflight** — local advisory checklist JSON/Markdown, conservative blocking/warnings, Dev Validation UI
- **Visual review sample-set annotations & readiness** — local annotation JSON, readiness Markdown, conservative advisory scoring
- **Visual review sample-set drilldown** — local JSON/Markdown sample set, recommended selection, Dev Validation UI
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 63)

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make mrms-visual-review-readiness
make mrms-render-candidate-preflight
make mrms-render-candidate-dry-run-plan
make operator-review-status
make operator-workflow-presets
```

## Dev API

`mrms_render_candidate_dry_run_plan` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/dry-run-plan` for local advisory dry-run plan (`dry_run_plan_ready` is not production authorization). Preflight and sample-set endpoints from Phases 60–62 unchanged. Default `make scheduled-validation` unchanged.

## Verified MRMS

`verified_mrms` is **false** everywhere.
