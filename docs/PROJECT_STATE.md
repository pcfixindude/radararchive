# Project State

Current phase: Phase 31 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Exportable local MRMS proof bundles** (folder + ZIP + manifest)
- **Proof bundle diff** comparing latest vs baseline bundle evidence
- **Operator handoff checklist** (local Markdown + JSON metadata)
- **Validation alert markers** with proof regression + sign-off linkage
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 31)

```bash
make mrms-proof-bundle
make mrms-proof-bundle-diff
make mrms-operator-handoff
make mrms-proof-report
make mrms-proof-regression
make mrms-signoff
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundles
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff
curl http://127.0.0.1:8000/api/validation/operator-handoff
```

## Local test

```bash
make test
make mrms-proof-bundle-diff
cd frontend && npm run build
```
