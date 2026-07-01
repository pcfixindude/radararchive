# Project State

Current phase: Phase 126 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Imported clip batch remediation plan** — bounded warm/decode command checklist from import problem frames
- **Clip manifest import replay** — import saved clip JSON; restore range/loop; readiness summary and remediation hints
- **Frame quality drill-down** — per-frame cache/decode/quality detail in replay UI; CLI/API status reports
- **Playback export clip** — export replay range as local clip manifest (API, CLI, UI copy/download)
- **Frame catalog browser** — list local frames with cache/decode status; jump-to-frame in replay UI
- **One-shot local replay setup** — `make local-replay-ready` checklist; optional `RUN=1` for bounded warm/decode
- **Saved replay bookmarks** — browser local storage for range, loop, ingest preset, and layer setup
- **Ingest date window UX** — guided presets, bounded command generation, Load frames panel
- **Playback range and loop** — set start/end frames, loop storm segments
- **Local replay session workflow** — replay session panel, readiness badge, keyboard shortcuts
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator workflow (Phase 126)

```bash
make mrms-ingest-window PRESET=last_3h LIMIT=8
make mrms-ingest-window PRESET=last_3h LIMIT=8 RUN=1 REAL=1
make local-replay-ready
make local-replay-ready RUN=1
make playback-export ARGS="--start 2026-06-28T13:00:00Z --end 2026-06-28T13:26:38Z"
make clip-import ARGS="--file data/dev/playback_export_latest.json"
make clip-remediation ARGS="--file data/dev/clip_import_latest.json"
make frame-quality ARGS="--timestamps 2026-06-28T13:00:00Z,2026-06-28T13:26:38Z"
make backend
make frontend
```

In the UI:
- **Range & loop → Import clip → Remediation plan** — grouped problem summary, copy-ready warm/decode checklist (not auto-run)
- **Range & loop → Import clip** — paste/upload exported JSON, validate, apply range and loop suggestion
- **Import clip → Problem frames** — inspect cold/missing frames; link to frame detail
- **Frame detail** — inspect selected/catalog/export/import frame; path hints, quality checks, suggested commands
- **Range & loop → Export clip** — manifest summary, copy JSON, download JSON
- **Frame catalog** — browse frames, see cache/decode readiness, click to jump
- **Replay session → Local replay setup** shows post-ingest checklist and next command
- **Load frames** / **Bookmarks** for ingest planning

## Verified MRMS

`verified_mrms` is **false** everywhere.
