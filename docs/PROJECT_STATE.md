# Project State

Current phase: Phase 117 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Local replay session workflow** — replay session panel, readiness badge, next-command hints, keyboard shortcuts
- **Usable local radar replay** — map/overlay toggles, fit-to-bounds, selected-frame summary
- **Frame quality checks** — diagnostic status on decoded overlay API and panel
- **Georef improvement** — rasterio WGS84 bounds; optional bounds outline toggle
- **Ingestion robustness** — bounded retries, `--retry-failed`, `--repair`
- **Playback cache status UI** — per-frame dots on time slider
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 117)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make decode-retry
make backend
make frontend
```

In the UI:
- **Replay session** panel shows frame readiness, cache/quality/bounds status, and the next command to run
- **Keyboard shortcuts**: Space play/pause, ←/→ step, O toggle overlay, B toggle bounds, F fit map to bounds
- **Map & overlay** toggles decoded overlay, bounds outline, debug sections, and fit map to overlay bounds on demand

## Verified MRMS

`verified_mrms` is **false** everywhere.
