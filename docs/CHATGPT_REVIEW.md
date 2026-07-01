# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

For Cursor, paste the ready-to-run prompt from **`docs/NEXT_PHASE_PROMPT.md`** (updated at the end of every completed phase).

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 122
- Latest phase: Phase 122 — Frame catalog browser
- Latest commit: `(pending commit)`
- Latest tag: `phase-122-frame-catalog-browser`
- Push status: pending push to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **122**
- Purpose: Browse local MRMS frames with cache/decode readiness and jump-to-frame in replay UI.
- CLI? **No** — status API only; no long-running work in request
- API? **Yes** — `GET /api/dev/frame-catalog` returns frames with cache/decode flags and counts
- UI? **Yes** — Frame catalog panel lists frames (newest first), filter by timestamp, click to jump playback
- Checks: cache_state, cache_ready, decode_ready per frame; summary counts
- Tests: backend frame catalog tests added; frontend frameCatalog.test.ts added

## Current focus

Frame catalog browser lets operators see cache/decode readiness and jump directly to frames. Next: playback export clip or frame quality drill-down.

## Next recommended phase

- Phase number: **123**
- Phase title: Playback export clip
- Goal: Export a bounded replay range as a local clip (frames list + optional preview bundle) for sharing or offline review.
- Why this is next: Navigation and setup are streamlined; exporting storm segments completes the local replay workflow loop.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 123 only.
Add playback export clip for bounded local replay ranges.
```

## Key docs (read order for new work)

1. `docs/NEXT_PHASE_PROMPT.md` — paste into Cursor to start the next phase
2. `docs/CHATGPT_REVIEW.md` (this file)
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_STEPS.md`
5. `docs/PHASE_LOG.md`
