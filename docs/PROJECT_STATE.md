# Project State

Current phase: Phase 120 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Saved replay bookmarks** — browser local storage for range, loop, ingest preset, and layer setup
- **Ingest date window UX** — guided presets, bounded command generation, Load frames panel
- **Playback range and loop** — set start/end frames, loop storm segments, range highlights on time slider
- **Local replay session workflow** — replay session panel, readiness badge, next-command hints, keyboard shortcuts
- **Usable local radar replay** — map/overlay toggles, fit-to-bounds, selected-frame summary
- **Frame quality checks** — diagnostic status on decoded overlay API and panel
- **Georef improvement** — rasterio WGS84 bounds; optional bounds outline toggle
- **Ingestion robustness** — bounded retries, `--retry-failed`, `--repair`
- **Playback cache status UI** — per-frame dots on time slider
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Guided ingest window** — `make mrms-ingest-window PRESET=last_3h LIMIT=8`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 120)

```bash
make mrms-ingest-window PRESET=last_3h LIMIT=8
make mrms-ingest-window PRESET=last_3h LIMIT=8 RUN=1 REAL=1
make mrms-warm-frame-cache
make decode-retry
make backend
make frontend
```

In the UI:
1. **Load frames** — pick ingest window, copy/run bounded command
2. **Range & loop** — set storm segment, enable loop
3. **Bookmarks** — save current setup by name; later Load to restore range/loop/ingest settings
4. **Replay session** — readiness checklist and next-command hints

## Verified MRMS

`verified_mrms` is **false** everywhere.
