# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 118
- Latest phase: Phase 118 — Playback range and loop
- Latest commit: (see end-of-phase report)
- Latest tag: `phase-118-playback-range-and-loop`
- Push status: pushed to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **118**
- Purpose: Select a start/end frame range and loop playback within that window for local storm-segment replay.
- Range controls? **Yes** — Set start, Set end, Clear range; order auto-normalized with notice
- Loop range? **Yes** — toggles wrap inside range; pauses at range end when loop off
- Keyboard shortcuts? **Yes** — `[` start, `]` end, `L` loop, `Esc` clear range
- Range visibility? **Yes** — time slider highlights range; playback panel shows position and loop status
- Frontend files:
  - `replayRange.ts`, `loopPlayback.ts`, `useReplayRange.ts`, `ReplayRangeControls.tsx`
  - `usePlayback.ts`, `PlaybackControls.tsx`, `TimeSlider.tsx`, `keyboardShortcuts.ts`, `App.tsx`
- Tests: backend 1229 passed; frontend 51 passed; `npm run build` ok

## Current focus

Local replay supports storm-segment looping with visible range status. Next: ingest window UX or playback speed presets per range.

## Next recommended phase

- Phase number: **119**
- Phase title: Ingest date window UX
- Goal: Let the operator pick a date/time window for bounded local MRMS ingest from the UI or a guided CLI preset, reducing manual ARGS tinkering.
- Why this is next: Replay workflow is solid; expanding available frames without memorizing ingest flags moves toward a fuller personal archive.
- Safety boundaries:
  - local dev / prototype only
  - real MRMS download remains explicit and bounded
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 119 only.
Add ingest date window UX for bounded local MRMS ingest.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
