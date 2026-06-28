# Project State

Current phase: Phase 55 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
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

## Operator commands (Phase 55)

```bash
make operator-workflow-presets
make operator-workflow-presets ARGS="--json"
cd frontend && npm test
```

## Dev API

`operator_workflow_presets` includes grouped `operator_workflow_preset_groups` and per-preset `group_id`, `short_reason`, `recommended_priority`. Dev Validation filters presets client-side (recommended-only, optional group) and offers Copy buttons — advisory local-only; copy does not execute commands.

## Verified MRMS

`verified_mrms` is **false** everywhere.
