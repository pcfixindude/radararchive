# Project State

Current phase: Phase 29 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with optional `--proof` step (compact proof-step status in summary)
- **Validation alert markers** with proof regression + sign-off linkage
- **Draft MRMS proof reports** with per-criterion evaluation
- **Proof history drill-down** API + dev panel proof review section
- **Local operator sign-off** via CLI and dev-only `POST /api/validation/signoffs` (does not set `verified_mrms`)
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 29)

```bash
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make mrms-signoff ARGS="--initials OP --notes 'reviewed' --accepted-limitations 'prototype only'"
make scheduled-validation ARGS="--proof"
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof/history
curl http://127.0.0.1:8000/api/validation/proof-regression/history
curl http://127.0.0.1:8000/api/validation/signoffs
curl -X POST http://127.0.0.1:8000/api/validation/signoffs \
  -H 'Content-Type: application/json' \
  -d '{"operator_initials":"OP","operator_notes":"local review only"}'
```

## Local test

```bash
make test
make mrms-proof-history
cd frontend && npm run build
```
