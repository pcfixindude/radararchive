# Project State

Current phase: Phase 114 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Georef improvement** — rasterio WGS84 bounds for decoded overlay; map bounds outline
- **Ingestion robustness** — bounded retries, partial success, `--retry-failed`, `--repair`
- **Playback cache status UI** — per-frame dots on time slider
- **Frame cache warming** — `make mrms-warm-frame-cache`
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 114)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make decode-retry
make backend
make frontend
```

Decoded overlay uses WGS84 bounds from `geo_metadata.json` when rasterio enriches decode output. `geo_accurate` remains **false**.

## Verified MRMS

`verified_mrms` is **false** everywhere.
