# Real MRMS Validation Runbook (Dev/Prototype)

This runbook explains how to run, inspect, and troubleshoot the **experimental** MRMS validation pipeline in RadarArchive.

**Important:** All validation output is prototype tooling. `verified_mrms` remains **false**. This is **not** verified production radar.

Future proof criteria (not met today): **[VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md)**.

## What the pipeline does

1. **Discover/register** MRMS catalog candidates (stub or real NOAA AWS)
2. **Download** pending frames (real mode only, when configured)
3. **Inspect/decode** `.grib2.gz` when optional decoders exist
4. **Build prototype tiles** (warping math; not production-verified)
5. **Enqueue/process** render jobs via local SQLite queue (no Redis/Celery)
6. **Persist dev reports** under `data/dev/`

Default map serving remains **placeholder tiles** unless feature flags and catalog gates are explicitly enabled.

## Prerequisites for full real validation

| Requirement | Purpose |
|-------------|---------|
| Network access | Download NOAA MRMS from AWS in `real` mode |
| `MRMS_SOURCE_MODE=real` or `--real` | Intentional real mode (never default) |
| Optional decoder (wgrib2 / rasterio / GDAL) | Inspect and decode real GRIB2 |
| Local disk | Raw downloads + decode artifacts + tile cache |
| `ENABLE_PRODUCTION_RADAR_TILES=false` (default) | Production serving stays off |

Without a decoder, real downloads may succeed but decode/tile steps will warn and write **0 tiles**.

## Stub validation (safe, offline default)

```bash
make validate-real-mrms-batch
make benchmark-render-queue
make scheduled-validation
make catalog-status
make render-queue-status
```

Stub mode uses offline catalog fixtures. Expect warnings about non-real GRIB2 and zero decoded frames — that is normal.

## Real one-frame smoke test (intentional, limited)

```bash
make real-mrms-smoke-test
# equivalent limits: --real, count=1, zoom 0 only, mark_catalog=false
```

Or via scheduled validation:

```bash
make scheduled-validation ARGS="--real --count 1 --min-zoom 0 --max-zoom 0"
```

**Warnings:** May download NOAA MRMS data. Still prototype — not verified MRMS.

## Scheduled validation (cron-friendly)

```bash
make scheduled-validation
make scheduled-validation ARGS="--json-report"
make scheduled-validation ARGS="--real --count 3 --min-zoom 0 --max-zoom 1"
```

Sample cron (not installed automatically):

```cron
0 */6 * * * cd /path/to/radararchive && make scheduled-validation >> data/dev/scheduled_validation.log 2>&1
```

Exit code: **0** success, **1** failure (suitable for cron monitoring).

## Check dashboard / API status

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/latest
curl http://127.0.0.1:8000/api/validation/scheduled
curl http://127.0.0.1:8000/api/validation/failures
curl http://127.0.0.1:8000/api/validation/alerts
curl http://127.0.0.1:8000/api/catalog/status
```

Frontend: Dev Validation panel shows alert status, grouped failure causes, suggested next action, scheduled steps, failure count, and **Show details** JSON drill-down.

## Check validation alerts

```bash
make validation-alerts
make validation-alerts ARGS="--refresh"
make validation-alerts ARGS="--json"
```

Alert file: `data/dev/validation_alert_latest.json` (local dev only; rebuilt after scheduled validation).

## Check recent failures

```bash
make validation-failures
make validation-failures ARGS="--limit 20"
make validation-failures ARGS="--json"
```

Log file: `data/dev/validation_failures.jsonl` (append-only, bounded to last 100 entries).

## Common failure causes

| Symptom | Likely cause | What to check |
|---------|--------------|---------------|
| Discovery/download errors | No network or AWS unreachable | Run stub mode first; verify network |
| `decoder unavailable` | No wgrib2/GDAL/rasterio | `make inspect-grib2`; install optional tools |
| No inspectable GRIB2 | Stub downloads or missing files | `MRMS_SOURCE_MODE=real make download-mrms` |
| Zero tiles written | No decode artifacts or zoom too high | `make decode-grib2`; lower zoom/count |
| Production tiles not served | Flag off (default) | `ENABLE_PRODUCTION_RADAR_TILES` + catalog gate + cached tile |
| Queue jobs failed | Missing artifacts or worker error | `make render-queue-status`; `make validation-failures` |
| `verified_mrms: false` | Always (by design) | Not a failure — prototype only |

## What success looks like (prototype)

- Scheduled validation **exit code 0**
- Steps show `succeeded` or `warning` (warnings are expected in stub mode)
- Catalog counts update in summary/API
- Optional: decoded frames and tiles written when decoder + real files exist

## What does NOT count as verified production MRMS

- Tiles built by prototype warping pipeline
- Queue benchmark or batch validation reports
- `production_rendering_enabled: false` (default)
- Any report with `verified_mrms: false` (all dev reports)
- Serving production-prototype tiles without explicit ops review and future validation phase

See **[VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md)** for the full checklist required before `verified_mrms` could ever become true.

## Verification commands

```bash
make test
make validation-alerts
make scheduled-validation
make validation-failures
make catalog-status
make render-queue-status
cd frontend && npm run build
```
