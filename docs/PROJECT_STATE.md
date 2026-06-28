# Project State

Current phase: Phase 49 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Operator review status consolidation** — one compact Dev Validation block from local review hints/history/exports/trends
- **Dev Validation export diff history** — recent entries (max 5) in summary API and UI
- **Review export diff trend regeneration hints** with scheduled validation tie-in
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 49)

```bash
make operator-review-status
make operator-review-status ARGS="--json"
curl http://127.0.0.1:8000/api/validation/operator-review-status
```

## Dev API

Summary includes `operator_review_status` compact (`status_level`, recommendations, `top_suggested_command`, `evidence_trend`, timestamps, counts).

## Verified MRMS

`verified_mrms` is **false** everywhere. Operator review status is local consolidation only — does not verify MRMS, clear alerts, or enable production rendering.
