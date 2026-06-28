# Project State

Current phase: Phase 30 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with optional `--proof` step
- **Exportable local MRMS proof bundles** (folder + ZIP + manifest)
- **Validation alert markers** with proof regression + sign-off linkage
- **Draft MRMS proof reports** with per-criterion evaluation
- **Local operator sign-off** via CLI and dev-only POST API
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 30)

```bash
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-bundle
make mrms-proof-bundle ARGS="--include-history"
make mrms-signoff ARGS="--initials OP --notes 'reviewed'"
make scheduled-validation ARGS="--proof"
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundles
curl http://127.0.0.1:8000/api/validation/signoffs
```

## Local test

```bash
make test
make mrms-proof-bundle
cd frontend && npm run build
```
