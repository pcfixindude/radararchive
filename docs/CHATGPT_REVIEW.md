# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

For Cursor, paste the ready-to-run prompt from **`docs/NEXT_PHASE_PROMPT.md`** (updated at the end of every completed phase).

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 124
- Latest phase: Phase 124 — Frame quality drill-down
- Latest commit: `(pending commit)`
- Latest tag: `phase-124-frame-quality-drilldown`
- Push status: pending push to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **124**
- Purpose: Per-frame quality/readiness drill-down in replay UI — decode status, cache path hints, preview availability, remediation commands.
- CLI? **Yes** — `make frame-quality` writes report JSON under `data/dev/` (gitignored)
- API? **Yes** — `GET /api/dev/frame-quality` returns quality report (status only)
- UI? **Yes** — Frame detail panel; inspect from frame catalog or export clip frame list
- Checks: cache/decode readiness, path hints, frame_quality checks, suggested_commands
- Tests: backend `test_frame_quality_report.py`; frontend `frameDetail.test.ts`

## Current focus

Operators can inspect any catalog or clip frame for cache/decode/quality detail and copy suggested remediation commands. Next: import saved clip manifest to restore replay range or batch-fix cold frames.

## Next recommended phase

- Phase number: **125**
- Phase title: Clip manifest import replay
- Goal: Load a saved playback clip JSON (from export) to restore range, loop, and frame list in the replay UI; show clip-level readiness summary and batch remediation hints.
- Why this is next: Export + drill-down complete the save/inspect loop; import closes the loop for offline/shared clip review.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 125 only.
Add clip manifest import to restore replay range from saved export JSON.
```

## Key docs (read order for new work)

1. `docs/NEXT_PHASE_PROMPT.md` — paste into Cursor to start the next phase
2. `docs/CHATGPT_REVIEW.md` (this file)
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_STEPS.md`
5. `docs/PHASE_LOG.md`
