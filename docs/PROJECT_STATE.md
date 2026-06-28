# Project State

Current phase: Phase 47 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Review export diff trend regeneration hints** with optional scheduled validation tie-in
- **Review session export diff trends** from bounded export diff history
- **Review session export diff** between consecutive Markdown exports
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 47)

```bash
make mrms-review-session-export-diff-trend-hint
make mrms-review-session-export-diff-trend
make scheduled-proof-bundle-review-export
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/review-sessions/export/diff/trend-hint
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Export diff trend hints are local operator evidence only — no external notifications.
