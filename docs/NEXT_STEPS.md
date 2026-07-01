# Next Steps

## Phase 116 - Georef UI controls (Draft)

Goal: Toggle bounds outline, fit-to-bounds, and georef debug details during local playback.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 115 verification commands

```bash
make test
cd frontend && npm test && npm run build
make decode-retry
make backend
make frontend
```

Local result after Phase 115:

- `GET /api/dev/decoded-overlay` includes `frame_quality` object
- Panel shows overall quality status and individual check messages
- Grid dimensions and min/max shown when available in measured fields
- Quality checks are advisory only

## Phase 114 verification commands

```bash
make test
make decode-retry
```

## Phase 113 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --retry-failed'
```
