# Next Steps

## Phase 126 - Imported clip batch remediation plan (Draft)

Goal: From imported clip problem frames, generate a bounded warm/decode command plan (copy-ready) without auto-running ingest or decode.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make clip-import ARGS="--file data/dev/playback_export_latest.json"
```

## Phase 125 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make playback-export ARGS="--start 2026-06-28T13:00:00Z --end 2026-06-28T13:26:38Z --timestamps 2026-06-28T13:00:00Z,2026-06-28T13:26:38Z"
make clip-import ARGS="--file data/dev/playback_export_latest.json"
```

Local result after Phase 125:

- `POST /api/dev/clip-import` validates manifest and returns refreshed readiness summary (status only)
- `make clip-import` writes `data/dev/clip_import_latest.json` (gitignored)
- Range & loop panel shows Import clip with paste/upload, validate, apply to replay
- Problem frames link to frame detail inspect; batch remediation hints shown

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
