# Project State

Current phase: Phase 39 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled proof bundle digest** (`make scheduled-proof-bundle-digest`) — optional local escalation digest + operator review checklist
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

## Operator commands (Phase 39)

```bash
make scheduled-proof-bundle-digest
make proof-bundle-diff-escalation-digest
make proof-bundle-diff-escalation-metrics
make scheduled-proof-bundle-handoff
make scheduled-proof-bundle-notify
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Scheduled digest and operator checklist are local review aids only — no external notifications.
