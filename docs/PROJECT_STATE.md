# Project State

Current phase: Phase 51 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Dev Validation UX polish** — collapsible detail sections; Operator Review Status remains top-level summary
- **Scheduled operator review status** — consolidated status in scheduled validation reports with runbook guidance
- **Operator review status consolidation** — runbook deep-links and guidance items in Dev Validation
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 51)

```bash
make operator-review-status
make scheduled-validation
curl http://127.0.0.1:8000/api/validation/summary
```

## Dev API

Summary unchanged from Phase 50. Dev Validation panel is frontend-only polish — collapsible sections with summary lines visible when collapsed.

## Verified MRMS

`verified_mrms` is **false** everywhere. Operator review status and scheduled operator status are local guidance only — do not verify MRMS, clear alerts, or enable production rendering.
