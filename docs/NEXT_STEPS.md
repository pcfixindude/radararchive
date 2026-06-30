# Next Steps

## Phase 113 - Ingestion robustness (Draft)

Goal: Harden bulk ingest retries, clearer failure reporting, and partial-window recovery.

```bash
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make test
```

## Phase 112 verification commands

```bash
make test
cd frontend && npm test && npm run build
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
# optional one-step warm:
make mrms-bulk-local-ingest ARGS='--real --limit 8 --warm-cache'
make backend
make frontend
```

Local result after Phase 112:

- Time slider shows per-frame cache dots (ready/cold/missing/failed/stub)
- Playback controls and decoded overlay panel show window cache counts
- `GET /api/dev/decoded-overlay/cache-status` returns per-frame states
- Playback holds previous overlay while next frame decodes
- Cold cache hints `make mrms-warm-frame-cache`

## Phase 111 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make backend
make frontend
```

## Phase 110 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --limit 8'
```
