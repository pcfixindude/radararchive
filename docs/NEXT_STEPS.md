# Next Steps

## Phase 121 - One-shot local replay setup (Draft)

Goal: Guided `make local-replay-ready` or UI checklist chaining bounded warm/decode readiness after ingest.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 120 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

Local result after Phase 120:

- **Bookmarks** panel saves/loads named replay setups in browser local storage
- Restores range, loop, ingest preset, layer, and selected frame when available
- “Ingest cmd” per bookmark copies bounded bulk ingest command
- Hints when saved timestamps are not in the current timeline

## Phase 119 verification commands

```bash
make test
make mrms-ingest-window PRESET=last_3h LIMIT=8
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 118 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```
