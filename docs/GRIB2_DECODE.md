# GRIB2 Decode Evaluation

Phase 11 evaluation notes for MRMS GRIB2.gz processing. **Not production rendering.**

## Intended future pipeline

```
MRMS GRIB2.gz (raw, immutable)
        ↓ decompress / stage
Decoded raster (float/int grid, native MRMS projection)
        ↓ normalize / QC
Normalized reflectivity values (dBZ or vendor units → standard dBZ)
        ↓ color table / legend
Styled raster (RGBA or indexed palette)
        ↓ COG or tile-ready raster
Cloud Optimized GeoTIFF and/or internal tile cache
        ↓ tile endpoint
GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png  (real radar, not placeholder)
        ↓ PWA map
MapLibre raster overlay + playback
```

Current state (Phases 1–11):
- Discovery, download, and placeholder processing are implemented.
- Real `.grib2.gz` files get `placeholder_for_real_raw` preview tiles only.
- `scripts/inspect_grib2.py` / `make inspect-grib2` reports metadata when decoders are available.

## Decoder options and tradeoffs

| Backend | Pros | Cons | Phase 11 status |
|---------|------|------|-----------------|
| **wgrib2 (CLI)** | Widely used for GRIB2 inventory; no Python geospatial stack required; good for metadata spike | Subprocess overhead; not ideal for raster tile generation; must be installed separately | **Used when available** for `-s` inventory |
| **GDAL + rasterio** | Strong raster I/O; COG output; reprojection; tile warping | Heavy native dependencies; larger deploy image; install complexity | Detected only — not required |
| **pygrib** | Direct GRIB2 message access in Python | Can be difficult to build/install; less common in cloud images | Detected only — future path |
| **cfgrib + xarray** | Ergonomic for NetCDF-like GRIB access | Depends on ecCodes; memory use for large grids | Detected only — future path |

### Recommendation (for Phase 12+)

1. **Metadata spike:** wgrib2 CLI (already wired in `grib2_inspector.py`).
2. **Production decode prototype:** rasterio/GDAL reading decoded grid → normalized numpy array → PNG/COG tile pyramid.
3. **Keep stub path:** demo/collector/MRMS stub files remain on placeholder tiles for offline dev.

## Inspection CLI

```bash
# Latest real downloaded MRMS file from catalog (safe when none exist)
make inspect-grib2

# Explicit file
PYTHONPATH=. python scripts/inspect_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz

# Fetch a real file first (network required)
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1
make inspect-grib2
```

When no real file exists, the script prints a hint and exits 0.

When no decoder is installed, the script still reports gzip size and GRIB magic checks.

## Module layout

- `backend/app/services/grib2_inspector.py` — dependency detection, staging, wgrib2 spike
- `backend/app/services/grib2_inspect_catalog.py` — find latest real MRMS candidates
- `scripts/inspect_grib2.py` — CLI entry point

## Non-goals (Phase 11)

- Replace placeholder map tiles with real radar
- Add hard dependencies on GDAL/rasterio/wgrib2 to `make setup`
- Change processor statuses or `/tiles` behavior
