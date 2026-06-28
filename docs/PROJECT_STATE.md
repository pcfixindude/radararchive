# Project State

Current phase: Phase 45 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Review session export diff** between consecutive Markdown exports (local/dev only)
- **Optional auto-export after review session create** (CLI `--export-after-create`, API `export_after_create`, Dev Validation checkbox)
- **Scheduled review session export** after digest/handoff in one local sequence
- **Review session Markdown export** with comparison, guidance, and regeneration hints
- **Local MRMS proof review sessions** linking escalation, digest, handoff, diff, and bundle evidence
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 45)

```bash
make mrms-review-session-export-diff
make mrms-review-session-export-diff-history
make mrms-review-session ARGS="--operator OP --notes 'local review' --accepted-limitations --export-after-create"
make mrms-review-session-export
make scheduled-proof-bundle-review-export
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/review-sessions/export/diff
curl http://127.0.0.1:8000/api/validation/review-sessions/export/diff/history
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Export diff and auto-export are local operator evidence only — no external notifications.
