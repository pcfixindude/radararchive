# Project State

Current phase: Phase 44 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
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

## Operator commands (Phase 44)

```bash
make scheduled-proof-bundle-review-export
make mrms-review-session-export
make mrms-review-session ARGS="--operator OP --notes 'local review' --accepted-limitations"
make scheduled-proof-bundle-digest
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/review-sessions/export
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Scheduled review export is local operator evidence only — no external notifications.
