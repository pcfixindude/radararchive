# Next Steps

## Phase 115 - Frame quality checks (Draft)

Goal: Local-dev sanity checks for decoded frames (value range, dimensions, empty grid).

```bash
make test
make decode-retry
```

## Phase 114 verification commands

```bash
make test
cd frontend && npm test && npm run build
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make decode-retry
make backend
make frontend
```

Local result after Phase 114:

- Overlay bounds from rasterio WGS84 affine or reprojected bounds
- Map shows dashed bounds outline when overlay active
- Panel shows `bounds_source`, bounds values, prototype georef warning
- `geo_accurate` remains false

## Phase 113 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --retry-failed'
```

## Phase 112 verification commands

```bash
make test
cd frontend && npm test && npm run build
```
