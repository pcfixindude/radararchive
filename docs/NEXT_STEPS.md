# Next Steps

## Phase 122 - Frame catalog browser (Draft)

Goal: Browse local MRMS frames with cache/decode status and jump-to-frame in the UI.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 121 verification commands

```bash
make test
make local-replay-ready
make local-replay-ready RUN=1
cd frontend && npm test && npm run build
make backend
make frontend
```

Local result after Phase 121:

- `make local-replay-ready` prints dry-run checklist (frames, cache, decode, UI)
- `RUN=1` executes bounded local warm/decode only — never real ingest
- `GET /api/dev/local-replay-ready` powers the replay session setup checklist
- Replay session panel shows setup status and next command

## Phase 120 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 119 verification commands

```bash
make test
make mrms-ingest-window PRESET=last_3h LIMIT=8
cd frontend && npm test && npm run build
```
