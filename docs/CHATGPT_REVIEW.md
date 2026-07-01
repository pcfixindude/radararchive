# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 117
- Latest phase: Phase 117 — Local replay session workflow
- Latest commit: (pending — see end-of-phase report)
- Latest tag: `phase-117-local-replay-session-workflow`
- Push status: (pending — see end-of-phase report)
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **117**
- Purpose: Make local radar replay feel like a usable operator workflow — keyboard shortcuts plus replay readiness/session summary.
- Replay session panel? **Yes** — `ReplaySessionPanel`: readiness badge, frame checklist, next-command hint, practical hints
- Keyboard shortcuts? **Yes** — Space play/pause, ←/→ step, O overlay, B bounds, F fit bounds; help in collapsible list
- Shortcuts ignore inputs? **Yes** — `isEditableTarget` skips inputs/textareas/selects
- Frontend files:
  - `keyboardShortcuts.ts`, `useReplayKeyboardShortcuts.ts`, `KeyboardShortcutsHelp.tsx`
  - `replaySessionSummary.ts`, `ReplaySessionPanel.tsx`
  - `App.tsx`, `app.css`
- Tests: backend 1229 passed; frontend 34 passed; `npm run build` ok

## Current focus

Local replay has keyboard controls and a session summary that shows what is ready, what is missing, and what command to run next. Next: playback range/loop or ingest window UX.

## Next recommended phase

- Phase number: **118**
- Phase title: Playback range and loop
- Goal: Let the operator set a start/end frame range and loop playback within that window for hands-on local replay.
- Why this is next: Session workflow and shortcuts exist; range/loop makes replaying a storm segment practical without manual stepping.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 118 only.
Add playback range selection and loop controls for local replay.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
