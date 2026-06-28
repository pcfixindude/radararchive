# Project State

Current phase: Phase 58 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Visual review operator integration** — stale visual review feeds operator review status and workflow presets
- **Visual review comparison & hints** — compare manifests, stale regeneration guidance
- **MRMS visual review artifacts** — local tile evidence manifest and Markdown report
- **Workflow preset command UX** — recommended-only/group filters and Copy-to-clipboard (does not execute commands)
- **Grouped workflow presets** — presets organized by category with recommended priority sorting
- **Workflow preset runbook guidance** — runbook deep-links and copy-ready commands
- **Operator workflow presets** — local command presets with recommendations from operator review status
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 58)

```bash
make operator-review-status
make operator-workflow-presets
make mrms-visual-review
make mrms-visual-review-hint
make mrms-visual-review-compare
```

## Dev API

`operator_review_status` includes `visual_review_regeneration_recommended`, comparison status, artifact counts, and runbook guidance for stale visual review. Workflow preset `regenerate-visual-review` is recommended when the visual review hint recommends regeneration.

## Verified MRMS

`verified_mrms` is **false** everywhere.
