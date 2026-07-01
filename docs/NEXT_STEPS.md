# Next Steps

## Phase 123 - Playback export clip (Draft)

Goal: Export a bounded replay range as a local clip manifest for sharing or offline review.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 122 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

Local result after Phase 122:

- `GET /api/dev/frame-catalog` returns local frames with cache/decode flags (status only)
- Frame catalog panel lists frames newest-first with text filter
- Click a frame row to jump playback (updates slider and selected frame)
- Range highlights on time slider unchanged

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
