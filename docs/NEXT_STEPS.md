# Next Steps

## Phase 108 - Decode-on-selected catalog frame (Draft)

Goal: Resolve or decode preview for the catalog-selected MRMS timestamp so playback can advance beyond a single local decode.

```bash
make decode-retry
make backend
make frontend
```

## Phase 107 verification commands

```bash
make test
cd frontend && npm test
cd frontend && npm run build
make decode-retry
make backend
make frontend
```

Local result after Phase 107:

- Overlay sync: `sync_status` `matched` when slider/catalog time equals candidate (`2026-06-28T13:26:38Z`)
- Mismatch: demo slider times show `mismatch` — overlay hidden, panel explains stale state
- `georef_quality`: rasterio bounds/affine notes; `geo_accurate` false
- Refresh: panel **Refresh** or `make decode-retry` then refetch overlay metadata

## Phase 106 verification commands

```bash
make test
cd frontend && npm test
cd frontend && npm run build
make decode-retry
```

Local result after Phase 106:

- `color_scale_mode`: `reflectivity_dbz`
- `tile_mode`: `local_raster_tiles`
- `tile_count`: 8 (z0–z1, 2×2 per level)

## Phase 105 verification commands

```bash
make decode-retry
make backend
make frontend
```
