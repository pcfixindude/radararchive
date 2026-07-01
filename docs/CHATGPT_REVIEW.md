# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 119
- Latest phase: Phase 119 — Ingest date window UX
- Latest commit: (see end-of-phase report)
- Latest tag: `phase-119-ingest-date-window-ux`
- Push status: pushed to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **119**
- Purpose: Guided bounded MRMS ingest date/time window with presets and visible commands — no silent download.
- Guided CLI? **Yes** — `make mrms-ingest-window` (dry-run default; `--run --real` required to download)
- Ingest plan API? **Yes** — `GET /api/dev/ingest-window/plan`
- UI panel? **Yes** — **Load frames**: presets, custom UTC range, limit, warm-cache, copy command, use replay range
- Presets: last 1h / 3h / 6h, custom, current replay range
- Replay hints updated to point at guided ingest workflow
- Tests: backend 1241 passed; frontend 55 passed; `npm run build` ok

## Current focus

Operators can pick an ingest window, see a bounded `--real` command, run it manually, then warm/decode/replay. Next: saved replay bookmarks or one-shot local replay setup.

## Next recommended phase

- Phase number: **120**
- Phase title: Saved replay bookmarks
- Goal: Save and reload named storm-segment replay ranges and last ingest window presets in the browser for faster repeat local sessions.
- Why this is next: Ingest window + range/loop exist; persisting operator choices removes repetitive setup between sessions.
- Safety boundaries:
  - local dev / prototype only
  - browser-local storage only — no cloud sync
  - real MRMS download remains explicit and bounded
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 120 only.
Add saved replay bookmarks for local range and ingest presets.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
