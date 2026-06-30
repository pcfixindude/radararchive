# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 106
- Latest phase: Phase 106 — Improve decoded preview color scale and tile slicing
- Latest commit: (pending)
- Latest tag: `phase-106-improve-decoded-preview-color-scale-and-tile-slicing`
- Push status: (pending)
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **106**
- Purpose: Reflectivity dBZ color table for decoded previews; local color tile pyramid; map overlay prefers raster tiles when available.
- Colorized reflectivity preview works? **Yes** — `color_scale_mode: reflectivity_dbz`, no-data (≤-900 dBZ) transparent
- Local decoded tile slicing works? **Yes** — `tile_mode: local_raster_tiles`, 8 tiles (z0–z1, 2×2 per level) under `data/dev/mrms_local_render_tiles/`
- Backend:
  - `color_scale.py` — dBZ color breaks, PNG encoder
  - `tile_preview.py` — local color tile pyramid builder
  - `GET /api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png` — local dev color tiles
  - Updated `mrms_local_render_pipeline.py` — color preview default, grayscale fallback
- Frontend:
  - `WeatherMap` — MapLibre raster tile source when `tile_mode=local_raster_tiles`, else color image overlay
  - `DecodedOverlayPanel` — shows render mode, color scale mode, tile mode/status, georef accuracy
- Output paths:
  - Color preview: `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
  - Local tiles: `data/dev/mrms_local_render_tiles/{z}/{x}/{y}.png`
  - Overlay API: `/api/dev/decoded-overlay`, `/api/dev/decoded-overlay/preview.png`, `/api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png`
- Georef: `rasterio_bounds` from enriched `geo_metadata.json`; `geo_accurate` false
- Local run: `make decode-retry` → `preview_ok`, `reflectivity_dbz`, `local_raster_tiles`
- Tests: backend 1173 passed; frontend 11 passed; `npm run build` ok

## Current focus

Colorized decoded preview and local tile pyramid work. Next: time-synced playback, geo-accurate overlay, or catalog-frame tile sync — **not** another gated wrapper.

## Next recommended phase

- Phase number: **107**
- Phase title: Time-synced playback and geo-accurate overlay
- Goal: Sync decoded overlay with time slider selection; improve georef accuracy or tie overlay to selected catalog timestamp.
- Why this is next: Color preview and local tiles render; playback/georef alignment is the practical next visual improvement.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 107 only.
Sync decoded overlay with time slider and improve geo-accurate placement for local dev.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
