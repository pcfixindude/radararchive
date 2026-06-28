# Project State

Current phase: Phase 35 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Proof bundle diff alert trend** summary over bounded history
- **Optional local diff alert acknowledgments** (does not clear alerts)
- **Proof bundle diff alert history** timeline
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 35)

```bash
make proof-bundle-diff-alert-history
make proof-bundle-diff-alert-trend
make proof-bundle-diff-acknowledge ARGS="--operator OP --note 'local review'"
make scheduled-proof-bundle
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-alert-trend
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-acknowledgments
```

## Verified MRMS

`verified_mrms` is **false** everywhere. Trend and acknowledgment are local review aids only.
