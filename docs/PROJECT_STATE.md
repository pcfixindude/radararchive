# Project State

Current phase: Phase 118 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Playback range and loop** — set start/end frames, loop storm segments, range highlights on time slider
- **Local replay session workflow** — replay session panel, readiness badge, next-command hints, keyboard shortcuts
- **Usable local radar replay** — map/overlay toggles, fit-to-bounds, selected-frame summary
- **Frame quality checks** — diagnostic status on decoded overlay API and panel
- **Georef improvement** — rasterio WGS84 bounds; optional bounds outline toggle
- **Ingestion robustness** — bounded retries, `--retry-failed`, `--repair`
- **Playback cache status UI** — per-frame dots on time slider
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 118)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make decode-retry
make backend
make frontend
```

In the UI:
- **Range & loop** — Set start / Set end on current frame, toggle loop, clear range
- **Keyboard shortcuts**: `[` / `]` set range, `L` loop range, `Esc` clear range; plus Space/←/→/O/B/F from Phase 117
- **Replay session** panel shows readiness and next command
- **Map & overlay** toggles decoded overlay, bounds outline, debug sections, fit map on demand

## Verified MRMS

`verified_mrms` is **false** everywhere.
