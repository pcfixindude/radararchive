# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 107
- Latest phase: Phase 107 — Time synced playback and georef overlay
- Latest commit: `f558136`
- Latest tag: `phase-107-time-synced-playback-and-georef-overlay`
- Push status: pushed to `origin/main` with tag
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **107**
- Purpose: Sync decoded overlay visibility with frontend time slider / catalog timestamp; improve georef metadata; show stale/mismatch in panel; refresh path via `make decode-retry`.
- Decoded overlay syncs to selected time/catalog frame? **Yes** — when `selected_timestamp` matches `candidate_timestamp` (`sync_status: matched`), overlay tiles/image render; otherwise hidden (`overlay_visible: false`).
- Stale/mismatch status visible? **Yes** — `DecodedOverlayPanel` shows `sync_status`, `sync_message`, selected vs candidate timestamps; map badge reflects mismatch.
- Georef accuracy improved? **Partially** — `georef_overlay.py` resolves `georef_quality` (`prototype_bounds`, `rasterio_bounds`, `rasterio_wgs84_affine`) and `georef_notes`; `geo_accurate` remains **false**.
- Backend:
  - `overlay_sync.py` — candidate timestamp extraction, `evaluate_overlay_sync()` (`matched`, `mismatch`, `no_selection`, `no_candidate_timestamp`)
  - `georef_overlay.py` — bounds + quality notes from `geo_metadata.json`
  - `decoded_overlay.py` — `artifact_available`, `overlay_visible`, sync fields; tiles only when synced
  - `grib2_decoder.py` — sets `valid_timestamp` on geo metadata
  - `GET /api/dev/decoded-overlay?timestamp=` — optional selected frame query
- Frontend:
  - `App.tsx` — refetch overlay on `selectedTime` change; refresh passes selected time
  - `WeatherMap.tsx` — overlay only when `overlay_visible`; sync-aware badge
  - `DecodedOverlayPanel.tsx` — sync status, timestamps, georef quality/notes
  - `fetchDecodedOverlay(selectedTimestamp?)` in `api/client.ts`
- Local candidate timestamp: `2026-06-28T13:26:38Z` (demo slider times mismatch unless user selects matching catalog frame)
- Refresh path: `make decode-retry` → overlay metadata refresh → map updates on next fetch
- Tests: backend 1183 passed; frontend 11 passed; `npm run build` ok

## Current focus

Decoded overlay is time-sync aware for local dev. Demo catalog times may not match the single decoded MRMS frame — mismatch is explicit. Next: decode-on-selected-frame, catalog ingestion for matching timestamps, or playback animation foundation.

## Next recommended phase

- Phase number: **108**
- Phase title: Decode-on-selected catalog frame
- Goal: When user selects a catalog timestamp, attempt decode/preview for that frame (or show actionable “no local decode” state) so playback can advance through multiple decoded frames.
- Why this is next: Phase 107 ties overlay visibility to timestamp match, but only one local decode exists; multi-frame playback needs per-frame decode or catalog-backed frame selection.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 108 only.
Decode or resolve preview for the catalog-selected MRMS frame so time-slider playback can show more than one local decoded frame.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
