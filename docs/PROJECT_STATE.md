# Project State

Current phase: Phase 111 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Frame cache warming** — `make mrms-warm-frame-cache`
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Multi-frame playback** — per-frame cache + adjacent prefetch
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 111)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make backend
make frontend
```

Reports:

- `data/dev/mrms_bulk_ingest_latest.json`
- `data/dev/mrms_cache_warm_latest.json`

Cache:

- `data/dev/mrms_frame_cache/{timestamp_token}/`

## Verified MRMS

`verified_mrms` is **false** everywhere.
