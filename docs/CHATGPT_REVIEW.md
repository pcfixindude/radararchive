# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 120
- Latest phase: Phase 120 — Saved replay bookmarks
- Latest commit: `49a1783`
- Latest tag: `phase-120-saved-replay-bookmarks`
- Push status: pushed to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **120**
- Purpose: Save and reload named storm-segment replay setups in browser local storage for fast local session resume.
- Bookmarks panel? **Yes** — save/load/rename/delete; compact list with active bookmark highlight
- Stored fields: range start/end, loop, selected layer/frame, ingest preset/window, limit, warm-cache
- Ingest command from bookmark? **Yes** — “Ingest cmd” shows copyable bounded bulk command per bookmark
- Storage: `radararchive.replayBookmarks.v1` with schema version, validation, max 20 bookmarks
- Restore hints when saved timestamps missing from timeline
- Frontend-only; no backend persistence or cloud sync
- Tests: backend 1241 passed; frontend 63 passed; `npm run build` ok

## Current focus

Local replay sessions can be bookmarked and restored quickly. Next: one-shot local replay setup or frame catalog browser.

## Next recommended phase

- Phase number: **121**
- Phase title: One-shot local replay setup
- Goal: Add a guided `make local-replay-ready` (or UI checklist) that chains bounded warm/decode status checks with clear next commands after ingest.
- Why this is next: Ingest, bookmarks, and range/loop exist; a single setup path reduces operator friction after loading frames.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 121 only.
Add one-shot local replay setup with bounded warm/decode readiness checks.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
