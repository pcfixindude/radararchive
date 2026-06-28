# Project State

Current phase: Phase 50 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
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

## Operator commands (Phase 50)

```bash
make operator-review-status
make scheduled-proof-bundle-operator-status
curl http://127.0.0.1:8000/api/validation/summary
```

## Dev API

Summary includes `operator_review_status` (with `guidance_items`, `top_guidance_item`, runbook fields) and `scheduled_operator_status` compact from the latest scheduled run.

## Verified MRMS

`verified_mrms` is **false** everywhere. Operator review status and scheduled operator status are local guidance only — do not verify MRMS, clear alerts, or enable production rendering.
