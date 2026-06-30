# Next Steps

## Phase 112 - Playback polish and cache status UI (Draft)

Goal: Clear cache-ready indicators on time slider; smoother transitions when cache is warm.

```bash
make mrms-warm-frame-cache
make backend
make frontend
```

## Phase 111 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --limit 8'
make mrms-warm-frame-cache
make backend
make frontend
```

Local result after Phase 111:

- Warm report under `data/dev/mrms_cache_warm_latest.json`
- Per-frame cache under `data/dev/mrms_frame_cache/`
- Panel shows playback cache ready when frames matched
- Playback uses cached frames without per-step decode delay

## Phase 110 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --limit 8'
```

## Phase 109 verification commands

```bash
make test
cd frontend && npm test && npm run build
```
