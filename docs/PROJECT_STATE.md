# Project State

Current phase: Phase 57 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
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

## Operator commands (Phase 57)

```bash
make mrms-visual-review
make mrms-visual-review-compare
make mrms-visual-review-hint
make mrms-visual-review-comparison-history
```

## Dev API

`mrms_visual_review_comparison` and `mrms_visual_review_hint` compact fields on validation summary; endpoints under `/api/validation/mrms-visual-review/comparison`, `/comparison/history`, and `/hint`.

## Verified MRMS

`verified_mrms` is **false** everywhere.
