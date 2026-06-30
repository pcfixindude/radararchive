# Next Steps

## Phase 111 - Frame cache warming for playback (Draft)

Goal: After bulk ingest, decode/prefetch ingested timestamps into per-frame cache for smoother playback.

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make decode-retry
make backend
make frontend
```

## Phase 110 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make decode-retry
make backend
make frontend
```

Local result after Phase 110:

- Bulk ingest report under `data/dev/mrms_bulk_ingest_latest.json`
- Multiple `.grib2.gz` under `data/raw/mrms/reflectivity/`
- Catalog timestamps visible on time slider / playback
- Playback merges catalog + processed times

## Phase 109 verification commands

```bash
make test
cd frontend && npm test && npm run build
```

## Phase 108 verification commands

```bash
make test
make decode-retry
```
