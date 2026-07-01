# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 115
- Latest phase: Phase 115 — Frame quality checks
- Latest commit: (pending)
- Latest tag: `phase-115-frame-quality-checks`
- Push status: pending
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **115**
- Purpose: Local-dev diagnostic quality checks for decoded MRMS playback frames.
- Frame quality checks exist? **Yes** — `frame_quality.py` with artifacts, manifest, grid values, dimensions, georef bounds, tile preview checks
- Overall statuses: `ok`, `warning`, `error`, `unavailable` (advisory only — does not block playback)
- API integration: optional `frame_quality` on `GET /api/dev/decoded-overlay`
- Frontend: `DecodedOverlayPanel` shows overall status, per-check messages, measured grid/min-max
- Backend files:
  - `frame_quality.py` (new)
  - `decoded_overlay.py`, `dev_overlay.py` schema
- Frontend files:
  - `DecodedOverlayPanel.tsx`, `client.ts`, `frameQualityDisplay.ts`, `app.css`
- Tests: backend 1229 passed; frontend 17 passed; `npm run build` ok

## Current focus

Decoded overlay panel surfaces frame quality diagnostics. Next: georef UI controls, tile/projection hardening, or playback polish.

## Next recommended phase

- Phase number: **116**
- Phase title: Georef UI controls
- Goal: Add compact UI controls for toggling bounds outline, fit-to-bounds, and georef debug visibility during local playback.
- Why this is next: Quality + georef metadata exist; operators need lightweight map controls without new verification gates.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 116 only.
Add georef UI controls for local playback debug.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
