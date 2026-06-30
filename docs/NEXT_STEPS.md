# Next Steps

## Phase 110 - Bulk local MRMS catalog ingestion (Draft)

Goal: Download and register multiple real MRMS frames locally so playback can animate across several decodable timestamps.

```bash
MRMS_SOURCE_MODE=real make download-mrms ARGS='--register-discovered --limit 10'
make decode-retry
make backend
make frontend
```

## Phase 109 verification commands

```bash
make test
cd frontend && npm test
cd frontend && npm run build
make backend
make frontend
```

Local result after Phase 109:

- Press Play — timestamps advance; overlay fetches per frame
- Adjacent frames prefetched (prev/next)
- Panel/controls show: playing, paused, decoding, frame ready, frame missing, decode failed
- Real MRMS timestamps animate decoded tiles when cached

## Phase 108 verification commands

```bash
make test
make decode-retry
```

## Phase 107 verification commands

```bash
make test
cd frontend && npm test && npm run build
```
