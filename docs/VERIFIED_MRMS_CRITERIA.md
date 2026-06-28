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

## Current status (Phase 25)

| Criterion area | Status |
|----------------|--------|
| Real NOAA download (optional dev) | Partial — not proof |
| Decoder + decode | Optional — often skipped |
| Geo verification | Prototype only |
| Visual sanity | Not formalized |
| Multi-frame proof | Not completed |
| Operator sign-off | Not completed |
| **verified_mrms** | **false** |

## Related docs

- [RUNBOOK_REAL_MRMS_VALIDATION.md](RUNBOOK_REAL_MRMS_VALIDATION.md) — how to run and troubleshoot
- [GRIB2_DECODE.md](GRIB2_DECODE.md) — decode prototype limitations
- [ARCHITECTURE.md](ARCHITECTURE.md) — pipeline architecture

A future phase must implement automated checks where possible, document results, and only then consider a guarded `verified_mrms` flag — never by default.
