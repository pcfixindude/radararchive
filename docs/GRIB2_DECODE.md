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

Current state (Phases 1–12):
- Discovery, download, and placeholder processing are implemented.
- Real `.grib2.gz` files get `placeholder_for_real_raw` preview tiles only.
- `make inspect-grib2` reports metadata when decoders are available.
- `make decode-grib2` writes prototype normalized raster artifacts under `data/staging/grib2_decode/` when optional decoders exist.
- **`/tiles` still serves placeholders** — decode output is not wired to the map.

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

## Prototype decode CLI (Phase 12)

```bash
# Latest real MRMS file (friendly when none/decoders missing)
make decode-grib2

# Explicit file
PYTHONPATH=. python scripts/decode_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz
```

### Optional decoder install (not part of `make setup`)

**Preferred:** rasterio + GDAL (system package or wheels)

```bash
# Example only — install method varies by platform
pip install rasterio numpy
```

**Lightweight fallback:** wgrib2 CLI (binary grid export)

```bash
# macOS example
brew install wgrib2
```

When no decoder is installed, `make decode-grib2` exits 0 with a friendly message.

### Prototype output

For each input file, output goes to a deterministic folder:

```
data/staging/grib2_decode/{token}/
  decode_manifest.json   # prototype metadata (production_rendering: false)
  normalized.tif         # rasterio path (optional)
  normalized.raw         # wgrib2 bin path (float32 0..1 normalized)
```

The manifest explicitly states that catalog `processed_status` and `/tiles` were not changed.

### Before production rendering (future phase)

1. Decode grid → consistent CRS/bounds aligned with map layer metadata
2. Build tile pyramid or COG cache under `data/tiles/`
3. Add feature flag or processed status such as `real_raster_processed`
4. Update `/tiles` to serve real imagery only when explicitly enabled
5. Keep stub/demo paths on placeholder tiles for offline dev

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
- `backend/app/services/grib2_decoder.py` — prototype raster decode (optional deps)
- `scripts/inspect_grib2.py` — inspection CLI
- `scripts/decode_grib2.py` — decode prototype CLI

## Non-goals (Phases 11–12)

- Replace placeholder map tiles with real radar
- Add hard dependencies on GDAL/rasterio/wgrib2 to `make setup`
- Change processor statuses or `/tiles` behavior
