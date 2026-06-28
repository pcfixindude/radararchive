# Project State

Current phase: Phase 24 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with step-level drill-down and failure logging
- **Operator runbook**: [RUNBOOK_REAL_MRMS_VALIDATION.md](RUNBOOK_REAL_MRMS_VALIDATION.md)
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 24)

```bash
make scheduled-validation
make validation-failures
make real-mrms-smoke-test
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/failures
curl http://127.0.0.1:8000/api/validation/scheduled
```

## Local test

```bash
make test
make scheduled-validation
make validation-failures
cd frontend && npm run build
```
