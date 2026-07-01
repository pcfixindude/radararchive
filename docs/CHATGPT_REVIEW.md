# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

For Cursor, paste the ready-to-run prompt from **`docs/NEXT_PHASE_PROMPT.md`** (updated at the end of every completed phase).

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 125
- Latest phase: Phase 125 — Clip manifest import replay
- Latest commit: `(pending commit — run git commit after tests pass)`
- Latest tag: `phase-125-clip-manifest-import-replay`
- Push status: pending push to `origin/main` with tag
- Final git status: source ready; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **125**
- Purpose: Import saved playback clip JSON to restore replay range, loop suggestion, and frame list with clip-level readiness summary and batch remediation hints.
- CLI? **Yes** — `make clip-import` validates manifest file and writes report under `data/dev/` (gitignored)
- API? **Yes** — `POST /api/dev/clip-import` validates manifest and refreshes readiness (status only)
- UI? **Yes** — Import clip in Range & loop panel; paste/upload JSON, apply range, inspect problem frames
- Checks: manifest validation, refreshed cache/decode counts, problem_frames, suggested_commands
- Tests: backend `test_clip_import.py`; frontend `clipImport.test.ts`

## Current focus

Operators can export a clip, import it later or on another machine, apply range/loop to replay, and inspect problem frames with batch remediation hints. Next: one-click bounded remediation plan from imported clip problem frames.

## Next recommended phase

- Phase number: **126**
- Phase title: Imported clip batch remediation plan
- Goal: From imported clip problem frames, generate a bounded warm/decode command plan (copy-ready) without running ingest or decode automatically.
- Why this is next: Import surfaces problem frames and hints; a structured remediation plan closes the fix loop for cold/missing frames.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 126 only.
Add bounded batch remediation plan from imported clip problem frames.
```

## Key docs (read order for new work)

1. `docs/NEXT_PHASE_PROMPT.md` — paste into Cursor to start the next phase
2. `docs/CHATGPT_REVIEW.md` (this file)
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_STEPS.md`
5. `docs/PHASE_LOG.md`
