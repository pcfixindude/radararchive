# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 108
- Latest phase: Phase 108 — Decode on selected catalog frame
- Latest commit: (pending)
- Latest tag: `phase-108-decode-on-selected-catalog-frame`
- Push status: (pending)
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **108**
- Purpose: When user selects a catalog timestamp, resolve/decode/preview that specific local MRMS frame or return actionable no-local-decode state; cache per-frame artifacts.
- Selected timestamp resolves matching local MRMS frame? **Yes** — catalog lookup + filesystem scan for `data/raw/mrms/reflectivity/*{token}*.grib2.gz`
- Selected-frame decode works? **Yes** — decodes if needed via existing `decode_grib2_file`, caches under `data/dev/mrms_frame_cache/{token}/`
- Selected-frame preview/tiles render? **Yes** — when `frame_status: matched`, overlay visible with per-frame preview/tiles; preview/tile APIs accept `?timestamp=`
- No-local-frame behavior:
  - `sync_status: no_local_candidate` — no local `.grib2.gz`; shows nearest raw/decoded timestamps + `MRMS_SOURCE_MODE=real make download-mrms` command
  - `sync_status: stub_input` — demo/catalog stub only
  - `sync_status: decode_failed` / `decoder_missing` — actionable retry commands
  - `sync_status: stale_latest_fallback` — latest pipeline preview exists for different frame
  - `sync_status: no_selection` — no timestamp (latest metadata only, overlay hidden)
- Backend:
  - `selected_frame_decode.py` — `resolve_selected_frame()`, per-frame cache manifest
  - `decoded_overlay.py` — prefers selected-frame resolve when `timestamp` + DB session provided
  - `tile_preview.py` — `build_local_tile_preview_at_root()` for per-frame tile roots
  - `GET /api/dev/decoded-overlay?timestamp=&refresh=` — decode/resolve selected frame
  - `GET /api/dev/decoded-overlay/preview.png?timestamp=`
  - `GET /api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png?timestamp=`
- Frontend:
  - `DecodedOverlayPanel` — frame status, nearest timestamps, no-local hints
  - `decodedOverlayPreviewUrl` / tile template — pass `timestamp` query
- Frame cache: `data/dev/mrms_frame_cache/{timestamp_token}/frame_manifest.json`, preview PNG, `tiles/`
- Tests: backend 1188 passed; frontend 11 passed; `npm run build` ok

## Current focus

Selecting a catalog timestamp now triggers on-demand local decode/preview when a matching raw MRMS file exists. Demo stub timestamps show stub/no-local states. Next: multi-frame playback animation or bulk local catalog ingestion.

## Next recommended phase

- Phase number: **109**
- Phase title: Multi-frame playback animation
- Goal: Wire time-slider playback to prefetch/decode adjacent catalog frames and animate decoded overlay across cached frames.
- Why this is next: Phase 108 decodes one selected frame; playback needs frame queueing and smooth transitions.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 109 only.
Add multi-frame playback animation using cached per-frame decodes from the time slider.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
