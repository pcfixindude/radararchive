# Project State

Current phase: Phase 32 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with optional `--proof`, `--bundle`, `--diff-bundle`
- **Proof bundle diff alert hooks** when evidence worsens or is mixed
- **Exportable local MRMS proof bundles** and operator handoff checklist
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 32)

```bash
make scheduled-validation
make scheduled-proof-bundle
make mrms-proof-bundle
make mrms-proof-bundle-diff
make mrms-operator-handoff
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff?refresh=true
```

## Local test

```bash
make test
make scheduled-proof-bundle
cd frontend && npm run build
```
