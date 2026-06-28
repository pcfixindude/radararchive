# Project State

Current phase: Phase 37 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Proof bundle diff escalation history** (bounded snapshots)
- **Optional stdout urgent notices** (local terminal only)
- **Proof bundle diff alert escalation** hints with runbook deep links
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 37)

```bash
make proof-bundle-diff-escalation
make proof-bundle-diff-escalation-history
make scheduled-proof-bundle-notify
make scheduled-proof-bundle ARGS="--notify-stdout"
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-history
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Escalation history and stdout notices are local review aids only — no external notifications.
