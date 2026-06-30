# Project State

Current phase: Phase 112 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Playback cache status UI** — per-frame dots on time slider; window counts in panels
- **Frame cache warming** — `make mrms-warm-frame-cache`
- **Optional auto-warm after ingest** — `--warm-cache` flag on bulk ingest
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Multi-frame playback** — hold previous overlay during decode; display overlay for map
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 112)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
# or one step:
make mrms-bulk-local-ingest ARGS='--real --limit 8 --warm-cache'
make backend
make frontend
```

API:

- `GET /api/dev/decoded-overlay/cache-status?timestamps=...`

Reports:

- `data/dev/mrms_bulk_ingest_latest.json`
- `data/dev/mrms_cache_warm_latest.json`

Cache:

- `data/dev/mrms_frame_cache/{timestamp_token}/`

## Verified MRMS

`verified_mrms` is **false** everywhere.
