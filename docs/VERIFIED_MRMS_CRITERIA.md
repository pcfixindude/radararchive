# Verified MRMS Criteria (Future Phase — Not Met Today)

This document defines what must be true before RadarArchive could ever set `verified_mrms=true` in code, APIs, or reports.

**Current project status: these criteria are NOT met.** The pipeline remains an experimental prototype. `verified_mrms` is **false** everywhere by design.

## Purpose

`verified_mrms` would mean an operator-reviewed, repeatable process has confirmed that downloaded NOAA MRMS data was decoded, georeferenced, and rendered into tiles that pass documented sanity checks — not merely that files exist or jobs succeeded with zero tiles.

## Required criteria (all must pass)

### 1. Real NOAA MRMS source

- [ ] File downloaded from documented NOAA AWS MRMS source (not stub)
- [ ] Checksum (SHA-256) recorded and matches on re-read
- [ ] File size and timestamp recorded in catalog
- [ ] Source URL/object key retained for audit

### 2. Decoder and decode artifacts

- [ ] Named decoder used (wgrib2, rasterio, GDAL, or approved alternative)
- [ ] Decoder version recorded in decode manifest
- [ ] Decode artifacts written under `data/staging/grib2_decode/`
- [ ] `geo_metadata.json` present with bounds, CRS, grid dimensions

### 3. Product and time metadata

- [ ] Product ID matches expected MRMS reflectivity product
- [ ] Valid time / frame timestamp confirmed against catalog row
- [ ] No mismatch between filename stamp and catalog timestamp

### 4. Geospatial correctness

- [ ] Source and output CRS documented
- [ ] Bounds within expected CONUS (or stated region) tolerance
- [ ] Grid width/height consistent with metadata
- [ ] Warping math reviewed for prototype limitations documented

### 5. Visual / sanity checks

- [ ] Known weather feature or null-echo pattern spot-checked (documented)
- [ ] No obvious all-zero or all-NaN raster
- [ ] Tile PNG non-empty and visually plausible at zoom 0 (operator sign-off)

### 6. Tile output from decoded data

- [ ] Tiles built from decode artifacts, not placeholder generator
- [ ] `tiles_written > 0` for validated frame(s) at agreed zoom
- [ ] Tile cache paths recorded
- [ ] Headers report honest mode (not claiming production if prototype)

### 7. Production path used intentionally

- [ ] `ENABLE_PRODUCTION_RADAR_TILES=true` only during controlled validation
- [ ] Catalog gate satisfied (`production_rendering` / render status)
- [ ] Cached production tile exists before serving
- [ ] Serving headers match intentional production-prototype mode

### 8. Repeatable multi-frame validation

- [ ] Same pipeline succeeds across **multiple** frames (minimum count TBD, e.g. 3+)
- [ ] Per-frame metrics recorded (decode, tiles, elapsed)
- [ ] Failures/warnings absent or explicitly accepted and documented

### 9. Failure and alert hygiene

- [ ] No unacknowledged `failed` alert status for validation window
- [ ] Grouped failure causes reviewed
- [ ] `make validation-alerts` status `ok` or accepted warnings only

### 10. Operator review

- [ ] Human operator review recorded (date, reviewer, commit or report ID)
- [ ] Explicit statement that output is still prototype until product launch review
- [ ] Link to validation reports and failure log snapshot

## What does NOT qualify

- Stub/offline validation with zero decoded frames
- Queue jobs that succeed with **0 tiles written**
- Prototype warping without visual sanity check
- Single-frame smoke test only (insufficient for production claim)
- Automatic pass because real download occurred
- Setting `verified_mrms=true` in tests or demo data

## Current status (Phase 26)

| Criterion area | Status |
|----------------|--------|
| Real NOAA download (optional dev) | Partial — not proof |
| Decoder + decode | Optional — often skipped |
| Geo verification | Prototype only |
| Visual sanity | Not formalized |
| Multi-frame proof | Automated draft report (`make mrms-proof-report`) |
| Operator sign-off | Template only — [MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](MRMS_OPERATOR_SIGNOFF_TEMPLATE.md) |
| **verified_mrms** | **false** |

## Automated proof report fields (Phase 26)

`make mrms-proof-report` writes `data/dev/mrms_proof_latest.json` with:

- `overall_status`: `not_started` | `insufficient_evidence` | `failed` | `ready_for_operator_review`
- `criteria_counts`: passed / failed / warning / skipped / unknown
- `aggregate_criteria`: per-criterion status from this checklist
- `frames[]`: per-frame evidence (checksum, paths, geo sanity, tiles, warnings)
- Always: `verified_mrms: false`, `proof_only: true`, `operator_review_required: true`

Criterion IDs evaluated: `real_noaa_source`, `decoder_and_artifacts`, `product_time_metadata`, `geospatial_correctness`, `visual_sanity_checks` (manual/skipped), `tile_output_from_decoded`, `production_path_intentional`, `repeatable_multi_frame`, `failure_alert_hygiene`, `operator_review` (manual/skipped).

**Signing the operator template does NOT set `verified_mrms=true`.**

## Regression and sign-off workflow (Phase 27)

After each `make mrms-proof-report`, the previous latest report is snapshotted for comparison.

```bash
make mrms-proof-regression
make mrms-signoff ARGS="--initials OP --notes 'reviewed' --accepted-limitations 'prototype only'"
```

- Regression report: `data/dev/mrms_proof_regression_latest.json`
- Sign-offs: `data/dev/mrms_signoffs.json` (local only)
- Validation alerts include `proof_regression` cause when regression detected
- `make scheduled-validation ARGS="--proof"` runs proof + regression after validation

Sign-off records `verified_mrms: false`, `does_not_set_verified_mrms: true`, and `does_not_enable_production: true` always.

## Dev sign-off API (Phase 29)

Optional dev/local `POST /api/validation/signoffs` shares the same validation as `make mrms-signoff`. Response always includes `verified_mrms: false` and `local_signoff_only: true`. Sign-off refreshes the validation alert but does **not** clear proof regression automatically.

## Proof bundle export (Phase 30)

`make mrms-proof-bundle` packages local proof/regression/sign-off/alert JSON into a timestamped folder + ZIP. Bundles are **supporting evidence only** — they do **not** verify MRMS or enable production rendering. Manifest always includes `verified_mrms: false`.

## Proof bundle diff + operator handoff (Phase 31)

`make mrms-proof-bundle-diff` compares the latest bundle to the previous bundle baseline. `make mrms-operator-handoff` writes a local Markdown checklist. Both are **supporting review evidence only** — `verified_mrms` stays false.

## Operator guidance + scheduled handoff (Phase 33)

Validation alert `operator_guidance` and scheduled `--handoff` auto-regeneration are **review aids only**. They map alert causes to runbook sections and may refresh the handoff checklist when proof bundle diff is worsened or mixed. They do **not** set `verified_mrms=true`, enable production rendering, mutate catalog gates, or clear validation alerts.

## Proof bundle diff alert history (Phase 34)

`make proof-bundle-diff-alert-history` and `GET /api/validation/proof-bundle-diff-alert-history` expose a bounded local timeline of diff alert states. This is **supporting review evidence only** — `verified_mrms` stays false and history does not verify MRMS or enable production rendering.

## Scheduled proof bundle monitoring (Phase 32)

`make scheduled-proof-bundle` runs scheduled validation with `--proof --bundle --diff-bundle`. This is **local evidence monitoring only** — it does not verify MRMS or enable production rendering. Alerts may flag `worsened` or `mixed` diff status for operator review.

## Proof review history (Phase 28)

Bounded read-only history for dev panel drill-down:

```bash
make mrms-proof-history
make mrms-proof-history ARGS="--json"
curl http://127.0.0.1:8000/api/validation/proof/history
curl http://127.0.0.1:8000/api/validation/proof-regression/history
curl http://127.0.0.1:8000/api/validation/signoffs
```

Dev Validation panel: **Show proof review** toggles proof history, regression history, and sign-off lists.

## Related docs

- [RUNBOOK_REAL_MRMS_VALIDATION.md](RUNBOOK_REAL_MRMS_VALIDATION.md) — how to run and troubleshoot
- [MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](MRMS_OPERATOR_SIGNOFF_TEMPLATE.md) — operator review template
- [GRIB2_DECODE.md](GRIB2_DECODE.md) — decode prototype limitations
- [ARCHITECTURE.md](ARCHITECTURE.md) — pipeline architecture

A future phase may gate `verified_mrms` behind documented operator approval — never by default.
