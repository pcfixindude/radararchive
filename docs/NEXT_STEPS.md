# Next Steps

## Phase 124 - Frame quality drill-down (Draft)

Goal: Per-frame quality/readiness detail in replay UI for catalog or clip frames — decode status, cache hints, remediation commands.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 123 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make playback-export ARGS="--start 2026-06-28T13:00:00Z --end 2026-06-28T13:26:38Z --timestamps 2026-06-28T13:00:00Z,2026-06-28T13:26:38Z"
```

Local result after Phase 123:

- `GET /api/dev/playback-export` returns clip manifest for range start/end (status only)
- `make playback-export` writes `data/dev/playback_export_latest.json` (gitignored)
- Range & loop panel shows Export clip with frame/cache/decode summary
- Copy JSON or download manifest locally from UI

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
