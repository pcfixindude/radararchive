# Project State

Current phase: Phase 116 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Usable local radar replay** — map/overlay toggles, fit-to-bounds, selected-frame summary, next-command hints
- **Frame quality checks** — diagnostic status on decoded overlay API and panel
- **Georef improvement** — rasterio WGS84 bounds; optional bounds outline toggle
- **Ingestion robustness** — bounded retries, `--retry-failed`, `--repair`
- **Playback cache status UI** — per-frame dots on time slider
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 116)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make decode-retry
make backend
make frontend
```

In the UI: use **Map & overlay** to toggle decoded overlay, bounds outline, debug sections, and fit map to overlay bounds on demand.

## Verified MRMS

`verified_mrms` is **false** everywhere.
