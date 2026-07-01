# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 114
- Latest phase: Phase 114 — Georef improvement
- Latest commit: `72c2562`
- Latest tag: `phase-114-georef-improvement`
- Push status: pushed to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **114**
- Purpose: Improve geographic placement for local decoded MRMS overlay playback.
- WGS84/rasterio bounds improved? **Yes** — `georef_bounds.py` computes WGS84 bounds via rasterio affine (`array_bounds`) or `transform_bounds` reprojection to EPSG:4326
- Overlay uses improved bounds? **Yes** — `decoded_overlay` API returns improved bounds; `WeatherMap` image/tile overlays and fitBounds use them; dashed bounds outline on map
- `geo_accurate` remains false? **Yes** — no production verification criteria met; notes state prototype-only placement
- Backend files changed:
  - `georef_bounds.py` (new) — WGS84 bounds extraction
  - `georef_overlay.py` — quality/source resolution
  - `render_metadata.py` — rasterio enrichment via georef_bounds
  - `grib2_decoder.py` — bounds/georef_quality in decode manifest
  - `selected_frame_decode.py` — georef fields in frame_manifest
  - `decoded_overlay.py`, `dev_overlay.py` schema — `bounds_source` field
- Frontend files changed:
  - `WeatherMap.tsx` — bounds outline layer
  - `DecodedOverlayPanel.tsx` — bounds source, values, prototype warning
  - `mapConfig.ts`, `client.ts`, `app.css`
- Debug UI / metadata fields:
  - `bounds_source` (e.g. `rasterio_affine_wgs84`, `rasterio_transform_wgs84`, `prototype_fallback`)
  - `georef_quality` (`rasterio_wgs84_affine`, `rasterio_wgs84_bounds`, `prototype_bounds`)
  - `georef_notes` with prototype disclaimer
  - Map dashed cyan bounds outline
- Artifacts: `geo_metadata.json`, `decode_manifest.json`, `frame_manifest.json` include bounds + georef_quality when rasterio enriches
- Tests: backend 1222 passed; frontend 16 passed; `npm run build` ok

## Current focus

Overlay placement uses rasterio-derived WGS84 bounds when available. Next: frame quality checks, georef UI controls, or tile/projection hardening.

## Next recommended phase

- Phase number: **115**
- Phase title: Frame quality checks
- Goal: Add local-dev checks for decoded frame sanity (empty grid, value range, dimension mismatch) surfaced in overlay panel.
- Why this is next: Georef improved; quality signals help catch bad decodes before playback.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 115 only.
Add local frame quality checks for decoded MRMS playback.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
