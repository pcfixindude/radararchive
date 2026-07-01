# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

For Cursor, paste the ready-to-run prompt from **`docs/NEXT_PHASE_PROMPT.md`** (updated at the end of every completed phase).

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 126
- Latest phase: Phase 126 — Imported clip batch remediation plan
- Latest commit: `12ad3bb` — phase 126: imported clip batch remediation plan
- Latest tag: `phase-126-imported-clip-batch-remediation`
- Push status: pushed to `origin/main` with tag
- Final git status: clean except untracked `data/dev/agent_logs/` (not committed)

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **126**
- Purpose: From imported clip problem frames, generate a bounded warm/decode command plan (copy-ready checklist) in replay UI and CLI without auto-running ingest or decode.
- CLI? **Yes** — `make clip-remediation` reads import report or manifest; writes plan under `data/dev/` (gitignored)
- API? **Yes** — `POST /api/dev/clip-remediation`; `POST /api/dev/clip-import` includes `remediation_plan`
- UI? **Yes** — Import clip panel **Remediation plan** section with grouped summary and copy-ready command block
- Checks: problem frame grouping (cold/missing/failed), bounded commands (max 8 default), explicit not-auto-run note
- Tests: backend `test_clip_remediation.py`; frontend `clipRemediation.test.ts`

## Current focus

Operators can import a clip, inspect problem frames, and copy a structured warm/decode remediation checklist. Next: sync playback timestamp list when applying imported clip (not just range endpoints).

## Next recommended phase

- Phase number: **127**
- Phase title: Import clip frame list sync
- Goal: When applying an imported clip, restore manifest frame timestamps to playback (not just range/loop).
- Why this is next: Remediation closes the fix loop; frame list sync makes apply match the exported clip sequence for replay.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 127 only.
Sync playback timestamp list when applying imported clip manifest frames.
```

## Key docs (read order for new work)

1. `docs/NEXT_PHASE_PROMPT.md` — paste into Cursor to start the next phase
2. `docs/CHATGPT_REVIEW.md` (this file)
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_STEPS.md`
5. `docs/PHASE_LOG.md`
