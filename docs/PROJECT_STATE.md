# Project State

Current phase: Phase 46 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Review session export diff trends** from bounded export diff history (local/dev only)
- **Review session export diff** between consecutive Markdown exports
- **Optional auto-export after review session create**
- **Scheduled review session export** after digest/handoff
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 46)

```bash
make mrms-review-session-export-diff-trend
make mrms-review-session-export-diff
make mrms-review-session-export-diff-history
make mrms-review-session-export
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/review-sessions/export/diff/trend
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Export diff trends are local operator evidence only — no external notifications.
