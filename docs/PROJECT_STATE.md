# Project State

Current phase: Phase 110 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Bulk MRMS ingest** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- **Multi-frame playback** — play through catalog timestamps with per-frame decode overlay
- **Per-frame cache** — `data/dev/mrms_frame_cache/{token}/`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator commands (Phase 110)

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make decode-retry
make backend
make frontend
```

Reports:

- `data/dev/mrms_bulk_ingest_latest.json`
- `data/dev/mrms_bulk_ingest_latest.md`

Raw files:

- `data/raw/mrms/reflectivity/`

## Verified MRMS

`verified_mrms` is **false** everywhere.
