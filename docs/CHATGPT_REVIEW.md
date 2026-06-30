# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 112
- Latest phase: Phase 112 — Playback polish and cache status UI
- Latest commit: (pending push)
- Latest tag: `phase-112-playback-polish-and-cache-status-ui`
- Push status: pending
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **112**
- Purpose: Make warm-vs-cold cache state obvious during playback; per-frame readiness on slider; smoother overlay transitions; optional post-ingest warm.
- Per-frame cache status indicators exist? **Yes** — colored dots on `TimeSlider` (ready / cold / missing / failed / stub)
- Playback transition flicker improved? **Yes** — `useFrameOverlay` holds previous `displayOverlay` while decoding; `WeatherMap` shows “Loading next frame…” and skips overlay removal during transition
- Auto-warm or post-ingest warm hint exists? **Yes** — `make mrms-bulk-local-ingest ARGS='--real --limit 8 --warm-cache'` (optional); ingest report also hints `make mrms-warm-frame-cache`
- Backend route changes:
  - `GET /api/dev/decoded-overlay/cache-status?timestamps=...` — window counts + per-frame `cache_state`
  - `backend/app/services/playback_cache_status.py` — `build_playback_cache_status()`, `resolve_frame_cache_state()`
- Frontend component changes:
  - `TimeSlider` — per-frame cache dots + summary line
  - `PlaybackControls` — window cache counts + warm hint
  - `DecodedOverlayPanel` — window/frame cache status + cold-cache command
  - `usePlaybackCacheStatus` — fetches cache-status API
  - `useFrameOverlay` — `displayOverlay` hold during decode
  - `WeatherMap` — uses `displayOverlay`; transition badge
  - `framePlayback.ts` — `cacheStateLabel()`, `cacheStateClass()`
- Commands:
  - `make mrms-warm-frame-cache`
  - `make mrms-bulk-local-ingest ARGS='--real --limit 8 --warm-cache'` (optional bounded auto-warm)
- Report/cache paths:
  - `data/dev/mrms_cache_warm_latest.json`
  - `data/dev/mrms_cache_warm_latest.md`
  - `data/dev/mrms_frame_cache/{timestamp_token}/`
  - `data/dev/mrms_bulk_ingest_latest.json`
- Tests: backend 1202 passed; frontend 16 passed; `npm run build` ok

## Current focus

Playback cache state is visible in UI; transitions hold previous frame during decode. Next: ingestion robustness, georef improvement, or frame quality checks.

## Next recommended phase

- Phase number: **113**
- Phase title: Ingestion robustness
- Goal: Harden bulk ingest retries, failure reporting, and partial-window recovery without changing verification gates.
- Why this is next: Cache warming and playback polish assume reliable ingest; failures should be clearer and recoverable.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 113 only.
Harden bulk MRMS ingest retries and partial-window recovery.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
