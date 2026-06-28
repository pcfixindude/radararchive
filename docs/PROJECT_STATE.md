# Project State

Current phase: Phase 38 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Proof bundle diff escalation metrics** and **local Markdown digest export**
- **Proof bundle diff escalation history** (bounded snapshots)
- **Optional stdout urgent notices** (local terminal only)
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 38)

```bash
make proof-bundle-diff-escalation-metrics
make proof-bundle-diff-escalation-digest
make proof-bundle-diff-escalation-history
make scheduled-proof-bundle-notify
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-metrics
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Metrics and digest are local review aids only — no external notifications.
