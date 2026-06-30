# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 111
- Latest phase: Phase 111 — Frame cache warming for playback
- Latest commit: (pending)
- Latest tag: `phase-111-frame-cache-warming-for-playback`
- Push status: (pending)
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **111**
- Purpose: Warm per-frame decode cache after bulk ingest so playback avoids per-step decode delay.
- Cache warming command exists? **Yes** — `make mrms-warm-frame-cache`
- Warms bulk-ingested window? **Yes** — reads `data/dev/mrms_bulk_ingest_latest.json` timestamps first, falls back to catalog local real MRMS
- Local run counts (typical stub test / when raw present): considered/skipped/decoded/failed reported in warm report; skips cached frames unless `--force`
- Commands:
  - `make mrms-warm-frame-cache`
  - `make mrms-warm-frame-cache ARGS='--limit 8'`
  - Optional: `--start`, `--end`, `--force`, `--product`, `--include-stubs`
- Report paths:
  - `data/dev/mrms_cache_warm_latest.json`
  - `data/dev/mrms_cache_warm_latest.md`
- Cache paths: `data/dev/mrms_frame_cache/{timestamp_token}/` (preview PNG, tiles/, frame_manifest.json)
- Playback starts smoothly from warmed cache? **Yes** — Phase 109 `useFrameOverlay` hits in-memory + disk cache via `resolve_selected_frame` fast path; panel shows `playback_ready` when warm report has matched frames
- Backend: `frame_cache_warmer.py` — `select_cache_window()`, `run_cache_warm()`
- Frontend: `DecodedOverlayPanel` — playback cache ready status from overlay API
- Tests: backend 1199 passed; frontend 15 passed; `npm run build` ok

## Current focus

Bulk ingest + cache warming prepare multi-frame playback offline. Next: playback polish, ingestion robustness, or georef improvement.

## Next recommended phase

- Phase number: **112**
- Phase title: Playback polish and cache status UI
- Goal: Improve playback UX when cache is warm vs cold; show per-frame ready indicators on slider; optional auto-warm after bulk ingest.
- Why this is next: Cache warming works; polish makes the warmed state obvious during play.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 112 only.
Polish playback UX with cache-ready indicators and smoother frame transitions.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
