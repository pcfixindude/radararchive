# Project State

Current phase: Phase 113 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Ingestion robustness** — bounded retries, partial success, `--retry-failed`, `--repair`
- **Playback cache status UI** — per-frame dots on time slider; window counts in panels
- **Frame cache warming** — `make mrms-warm-frame-cache`
- **Optional auto-warm after ingest** — `--warm-cache` flag on bulk ingest
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Multi-frame playback** — hold previous overlay during decode; display overlay for map
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 113)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
# partial failure recovery:
make mrms-bulk-local-ingest ARGS='--real --retry-failed'
# or skip already-valid frames:
make mrms-bulk-local-ingest ARGS='--real --missing-only --limit 8'
# repair bad zero-byte files:
make mrms-bulk-local-ingest ARGS='--real --repair --limit 8'
make mrms-warm-frame-cache
```

Reports:

- `data/dev/mrms_bulk_ingest_latest.json`
- `data/dev/mrms_cache_warm_latest.json`

Raw files:

- `data/raw/mrms/reflectivity/`

## Verified MRMS

`verified_mrms` is **false** everywhere.
