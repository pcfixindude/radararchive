# Project State

Current phase: Phase 53 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Workflow preset runbook guidance** — presets link to runbook sections with copy-ready commands
- **Operator workflow presets** — local command presets with recommendations from operator review status
- **Dev Validation UX polish** — collapsible detail sections; Operator Review Status remains top-level summary
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 53)

```bash
make operator-workflow-presets
make operator-workflow-presets ARGS="--json"
curl http://127.0.0.1:8000/api/validation/operator-workflow-presets
```

## Dev API

`operator_workflow_presets` preset objects include runbook guidance fields and copy-ready commands. Presets are advisory and local-only — do not run commands automatically, verify MRMS, clear alerts, or enable production rendering.

## Verified MRMS

`verified_mrms` is **false** everywhere.
