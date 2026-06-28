# Project State

Current phase: Phase 52 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Operator workflow presets** — local command presets with recommendations from operator review status
- **Dev Validation UX polish** — collapsible detail sections; Operator Review Status remains top-level summary
- **Scheduled operator review status** — consolidated status in scheduled validation reports with runbook guidance
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 52)

```bash
make operator-review-status
make operator-workflow-presets
make scheduled-proof-bundle-operator-status
curl http://127.0.0.1:8000/api/validation/operator-workflow-presets
```

## Dev API

Summary includes `operator_workflow_presets` compact (recommended presets, commands, safety flags). Presets are read-only workflow guidance — do not verify MRMS, clear alerts, or enable production rendering.

## Verified MRMS

`verified_mrms` is **false** everywhere. Operator workflow presets and operator review status are local guidance only.
