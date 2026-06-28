# Project State

Current phase: Phase 26 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with step-level drill-down and failure logging
- **Validation alert markers** with grouped failure causes (local dev only)
- **Draft MRMS proof reports** with per-criterion evaluation and geo sanity helpers
- **Operator sign-off template** — signing does not set `verified_mrms`
- **Verified MRMS proof criteria** documented — criteria **not met**; `verified_mrms` false
- **Operator runbook**: [RUNBOOK_REAL_MRMS_VALIDATION.md](RUNBOOK_REAL_MRMS_VALIDATION.md)
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 26)

```bash
make scheduled-validation
make validation-failures
make validation-alerts
make mrms-proof-report
make real-mrms-smoke-test
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/failures
curl http://127.0.0.1:8000/api/validation/alerts
curl http://127.0.0.1:8000/api/validation/proof
curl http://127.0.0.1:8000/api/validation/scheduled
```

## Local test

```bash
make test
make mrms-proof-report
make validation-alerts
make scheduled-validation
cd frontend && npm run build
```
