# Project State

Current phase: Phase 54 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
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

## Operator commands (Phase 54)

```bash
make operator-workflow-presets
make operator-workflow-presets ARGS="--json"
```

## Dev API

`operator_workflow_presets` includes grouped `operator_workflow_preset_groups` and per-preset `group_id`, `short_reason`, `recommended_priority`. Advisory local-only — does not run commands automatically.

## Verified MRMS

`verified_mrms` is **false** everywhere.
