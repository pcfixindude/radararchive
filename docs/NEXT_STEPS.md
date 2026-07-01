# Next Steps

## Phase 125 - Clip manifest import replay (Draft)

Goal: Load saved playback clip JSON to restore range, loop, and frame list in replay UI with clip-level readiness summary.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 124 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make frame-quality ARGS="--timestamps 2026-06-28T13:00:00Z,2026-06-28T13:26:38Z"
```

Local result after Phase 124:

- `GET /api/dev/frame-quality` returns per-frame cache/decode/quality detail (status only)
- `make frame-quality` writes `data/dev/frame_quality_latest.json` (gitignored)
- Frame detail panel shows path hints, quality checks, suggested remediation commands
- Frame catalog **detail** link and export clip frame list open inspect without jumping playback

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
