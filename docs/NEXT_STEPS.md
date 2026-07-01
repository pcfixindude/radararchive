# Next Steps

## Phase 128 - Applied clip sequence position (Draft)

Goal: After applying an imported clip frame list, show current position within the clip sequence in replay UI (e.g. “Clip frame 4/26”) and warn when the selected frame is outside the applied sequence.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make playback-export ARGS="--start 2026-06-28T13:00:00Z --end 2026-06-28T13:26:38Z --timestamps 2026-06-28T13:00:00Z,2026-06-28T13:26:38Z"
make clip-import ARGS="--file data/dev/playback_export_latest.json"
```

## Phase 127 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make playback-export ARGS="--start 2026-06-28T13:00:00Z --end 2026-06-28T13:26:38Z --timestamps 2026-06-28T13:00:00Z,2026-06-28T13:26:38Z"
make clip-import ARGS="--file data/dev/playback_export_latest.json"
```

Local result after Phase 127:

- `buildApplyPayload` includes bounded manifest frame timestamps (`MAX_CLIP_FRAMES` = 200)
- Apply handler merges clip frame list into playback timeline and selects first clip frame
- Import clip panel shows apply preview: “Will restore N frames from clip sequence” vs range-only fallback
- Backend `extract_apply_frame_timestamps` helper with tests
- No auto warm/decode; no new ingest endpoints

## Phase 126 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make clip-import ARGS="--file data/dev/playback_export_latest.json"
make clip-remediation ARGS="--file data/dev/clip_import_latest.json"
```

Local result after Phase 126:

- `POST /api/dev/clip-remediation` builds bounded warm/decode plan from manifest or import report (status only)
- `POST /api/dev/clip-import` includes `remediation_plan` with grouped problem summary and copy-ready command block
- `make clip-remediation` writes `data/dev/clip_remediation_latest.json` (gitignored)
- Import clip panel shows **Remediation plan** with cold/missing/failed counts and copy-ready checklist
- Explicit note: commands are not auto-run
