# Project State

Current phase: Phase 60 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Visual review sample-set drilldown** — local JSON/Markdown sample set, recommended selection, Dev Validation UI
- **Scheduled visual review workflow** — optional `--visual-review` scheduled step and `make scheduled-proof-bundle-visual-review`
- **Visual review operator integration** — stale visual review feeds operator review status and workflow presets
- **Visual review comparison & hints** — compare manifests, stale regeneration guidance
- **MRMS visual review artifacts** — local tile evidence manifest and Markdown report
- **Operator workflow presets** — standalone and scheduled visual review commands
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 60)

```bash
make mrms-visual-review
make mrms-visual-review-sample-set
make scheduled-proof-bundle-visual-review
make operator-review-status
make operator-workflow-presets
```

## Dev API

`mrms_visual_review_sample_set` compact on validation summary; `GET/POST /api/validation/mrms-visual-review/sample-set` for local drilldown sample set (does not verify MRMS). `scheduled_visual_review` compact; optional scheduled visual review step with `--visual-review` (explicit opt-in). Default `make scheduled-validation` unchanged.

## Verified MRMS

`verified_mrms` is **false** everywhere.
