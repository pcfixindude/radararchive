# Project State

Current phase: Phase 115 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Frame quality checks** — diagnostic status on decoded overlay API and panel
- **Georef improvement** — rasterio WGS84 bounds for decoded overlay
- **Ingestion robustness** — bounded retries, partial success, `--retry-failed`
- **Playback cache status UI** — per-frame dots on time slider
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 115)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make decode-retry
make backend
make frontend
```

Decoded overlay response includes `frame_quality` with overall status and per-check messages. Playback is not blocked by warnings.

## Verified MRMS

`verified_mrms` is **false** everywhere.
