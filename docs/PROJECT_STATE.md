# Project State

Current phase: Phase 48 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Dev Validation export diff history** — recent entries (max 5) in summary API and UI
- **Review export diff trend regeneration hints** with scheduled validation tie-in
- **Review session export diff trends** from bounded export diff history
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 48)

```bash
make mrms-review-session-export-diff-history
curl http://127.0.0.1:8000/api/validation/summary
```

## Dev API

Summary includes `mrms_review_session_export_diff_history` compact (count, latest status/timestamp, recent entries max 5).

## Verified MRMS

`verified_mrms` is **false** everywhere. Export diff history is local operator evidence only.
