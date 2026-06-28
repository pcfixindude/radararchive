# Project State

Current phase: Phase 40 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Digest export history** (bounded, last 25) and **digest diff metadata**
- **Digest regeneration hints** in Dev Validation summary
- **Scheduled proof bundle digest** (`make scheduled-proof-bundle-digest`)
- **Proof bundle diff escalation metrics** and local Markdown digest export
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 40)

```bash
make proof-bundle-diff-escalation-digest-history
make proof-bundle-diff-escalation-digest-diff
make proof-bundle-diff-escalation-digest
make scheduled-proof-bundle-digest
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest-history
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest-diff
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Digest history, diff metadata, and regeneration hints are local review aids only — no external notifications.
