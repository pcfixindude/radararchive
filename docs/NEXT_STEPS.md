# Next Steps

## Phase 127 - Import clip frame list sync (Draft)

Goal: When applying an imported clip, sync the playback timestamp list from manifest frames (not just range endpoints) so replay matches the exported clip frame sequence.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
make clip-import ARGS="--file data/dev/playback_export_latest.json"
```

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
