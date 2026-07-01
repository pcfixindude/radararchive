# Project State

Current phase: Phase 119 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
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

## Operator workflow (Phase 119)

```bash
make mrms-ingest-window PRESET=last_3h LIMIT=8
# review output, then run real ingest explicitly:
make mrms-ingest-window PRESET=last_3h LIMIT=8 RUN=1 REAL=1
# or copy the bulk command from the UI / CLI plan
make mrms-warm-frame-cache
make decode-retry
make backend
make frontend
```

In the UI:
- **Load frames** — pick preset or custom UTC window, set limit, copy bounded ingest command
- **Range & loop** — Set start / Set end, loop storm segment
- **Replay session** — readiness checklist and next-command hints
- **Map & overlay** — toggles and fit-to-bounds on demand

## Verified MRMS

`verified_mrms` is **false** everywhere.
