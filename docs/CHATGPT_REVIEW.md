# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 109
- Latest phase: Phase 109 — Multi frame playback animation
- Latest commit: `a7b5241`
- Latest tag: `phase-109-multi-frame-playback-animation`
- Push status: pushed to `origin/main` with tag
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **109**
- Purpose: Multi-frame local playback animation using cached per-frame decodes; adjacent-frame prefetch; responsive decode status during play.
- Playback controls exist? **Yes** — existing Play/Pause/step/speed controls; now show overlay playback status
- Playback advances selected timestamps? **Yes** — `usePlayback` steps catalog frames; `useFrameOverlay` loads overlay per frame
- Cached decoded frames animate on map? **Yes** — overlay tile/image source updates as `decodedOverlay` changes per timestamp
- Adjacent-frame prefetch works? **Yes** — `GET /api/dev/decoded-overlay/prefetch?timestamps=` + client-side cache warm for prev/next
- Missing-frame behavior:
  - `frame_missing` / `no_local_candidate` / `stub_input` — overlay hidden, status in panel/playback controls
  - `decode_failed` / `decoder_missing` — actionable commands shown
  - `decoding` — non-blocking; playback timer continues; map badge shows decoding
- Backend:
  - `frame_playback.py` — `prefetch_frames()` for up to 3 adjacent timestamps
  - `GET /api/dev/decoded-overlay/prefetch?timestamps=t1,t2,t3`
- Frontend:
  - `useFrameOverlay.ts` — per-frame load, in-memory cache, adjacent prefetch
  - `framePlayback.ts` — status helpers (`playing`, `paused`, `decoding`, `frame_ready`, `frame_missing`, `decode_failed`)
  - `PlaybackControls` — overlay playback status line
  - `DecodedOverlayPanel` — playback status + loading indicator
  - `WeatherMap` — decoding badge during frame load
- Tests: backend 1190 passed; frontend 15 passed; `npm run build` ok

## Current focus

Playback steps through catalog timestamps and updates decoded overlay per frame with prefetch for neighbors. Demo stubs show missing-frame states; real MRMS frames decode/cache and animate. Next: bulk local catalog ingestion or playback polish.

## Next recommended phase

- Phase number: **110**
- Phase title: Bulk local MRMS catalog ingestion
- Goal: Download/register multiple real MRMS frames locally so playback has more than one decodable timestamp.
- Why this is next: Playback works but demo catalog is mostly stubs; bulk ingestion unlocks meaningful multi-frame animation.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 110 only.
Bulk download and register multiple local MRMS catalog frames for playback.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
