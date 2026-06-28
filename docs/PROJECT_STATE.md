# Project State

Current phase: Phase 41 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Local MRMS proof review sessions** linking escalation, digest, handoff, diff, and bundle evidence
- **Digest export history** and **digest diff metadata** with regeneration hints
- **Scheduled proof bundle digest** (`make scheduled-proof-bundle-digest`)
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 41)

```bash
make mrms-review-session ARGS="--operator OP --notes 'local review' --accepted-limitations"
make mrms-review-sessions
make scheduled-proof-bundle-digest
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/review-sessions
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Review sessions are local operator evidence only — no external notifications.
