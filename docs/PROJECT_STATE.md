# Project State

Current phase: Phase 56 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
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

## Operator commands (Phase 56)

```bash
make mrms-visual-review
make mrms-visual-review-history
make mrms-visual-review ARGS="--json-report"
```

## Dev API

`mrms_visual_review` compact field on validation summary; `GET /api/validation/mrms-visual-review` and `/history`. Inspects existing catalog/tile artifacts only — does not download, decode, verify MRMS, or enable production rendering.

## Verified MRMS

`verified_mrms` is **false** everywhere.
