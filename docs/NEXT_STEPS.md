# Next Steps

## Phase 120 - Saved replay bookmarks (Draft)

Goal: Save and reload named storm-segment replay ranges and ingest window presets in browser local storage.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 119 verification commands

```bash
make test
cd frontend && npm test && npm run build
make mrms-ingest-window PRESET=last_3h LIMIT=8
make backend
make frontend
```

Local result after Phase 119:

- **Load frames** panel builds bounded ingest commands from presets
- `make mrms-ingest-window` dry-runs by default; `RUN=1 REAL=1` required to download
- `GET /api/dev/ingest-window/plan` returns command plan without downloading
- Replay session hints point to guided ingest workflow

## Phase 118 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 117 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```
