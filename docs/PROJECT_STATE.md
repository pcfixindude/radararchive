# Project State

Current phase: Phase 12 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery + download pipeline
- Placeholder processor and `/tiles` behavior unchanged
- GRIB2 inspection spike (`make inspect-grib2`)
- GRIB2 decode prototype (`make decode-grib2`) — optional rasterio/wgrib2
- Decode output under `data/staging/grib2_decode/` (not served by API)
- No production rendering; real MRMS not marked as rendered

## Local test

```bash
make test
make inspect-grib2
make decode-grib2
cd frontend && npm run build
```

## Prototype decode

```bash
make decode-grib2
PYTHONPATH=. python scripts/decode_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz
```

See `docs/GRIB2_DECODE.md` for optional decoder install and production rendering prerequisites.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
