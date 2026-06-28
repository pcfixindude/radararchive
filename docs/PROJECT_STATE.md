# Project State

Current phase: Phase 27 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with step-level drill-down and failure logging
- **Validation alert markers** with grouped failure causes and proof regression hooks
- **Draft MRMS proof reports** with per-criterion evaluation
- **Proof regression detection** comparing latest vs previous proof evidence
- **Local operator sign-off persistence** — does not set `verified_mrms`
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 27)

```bash
make scheduled-validation
make scheduled-validation ARGS="--proof"
make validation-alerts
make mrms-proof-report
make mrms-proof-regression
make mrms-signoff ARGS="--initials OP --notes 'reviewed' --accepted-limitations 'prototype only'"
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-regression
curl http://127.0.0.1:8000/api/validation/signoffs
```

## Local test

```bash
make test
make mrms-proof-report
make mrms-proof-regression
cd frontend && npm run build
```
