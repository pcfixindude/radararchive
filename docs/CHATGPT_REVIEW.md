# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 105
- Latest phase: Phase 105 — Wire decoded preview map overlay
- Latest commit: (pending)
- Latest tag: `phase-105-wire-decoded-preview-map-overlay`
- Push status: (pending)
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Decoded map overlay: local dev prototype only — not verified MRMS, not production tile serving

## Latest phase summary

- Phase: **105**
- Purpose: Wire local `decoded_prototype` preview into the frontend map shell for local development.
- Backend:
  - `GET /api/dev/decoded-overlay` — overlay metadata (status, bounds, labels, refresh commands)
  - `GET /api/dev/decoded-overlay/preview.png` — serves latest preview PNG from `data/dev/`
  - Service: `backend/app/services/decoded_overlay.py`
- Frontend:
  - `DecodedOverlayPanel` — status, labels, Refresh button
  - `WeatherMap` — MapLibre `image` source overlay when preview available
- Decoded preview visible in local map shell? **Yes** (when `make decode-retry` has produced preview)
- Georef: **rasterio_bounds** when `geo_metadata.json` was enriched from rasterio; otherwise **prototype_bounds** (DEFAULT_MRMS_BOUNDS). `geo_accurate` remains false.
- Preview paths:
  - PNG: `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
  - API image: `/api/dev/decoded-overlay/preview.png`
  - Metadata: `/api/dev/decoded-overlay`
- Refresh workflow: run `make decode-retry` or `make mrms-local-render-pipeline`, then click **Refresh** in the Local decoded preview panel
- Tests: backend 1165 passed; frontend 9 passed; `npm run build` ok

## Current focus

Decoded prototype is visible on the local map overlay. Next: improve color scale, tile slicing, or time-synced playback — **not** another gated wrapper.

## Next recommended phase

- Phase number: **106**
- Phase title: Improve decoded preview color scale and tile slicing
- Goal: Replace prototype grayscale sampling with reflectivity color table, slice decoded grid into multiple preview tiles or enable `ENABLE_DECODED_TILES` for catalog frame locally (still prototype, still not verified MRMS).
- Why this is next: Overlay is wired and georef-placed; visual fidelity and multi-zoom preview are the practical next improvements.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off by default
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 106 only.
Improve decoded preview color scale and tile slicing for local dev.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
