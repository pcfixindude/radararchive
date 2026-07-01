# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

For Cursor, paste the ready-to-run prompt from **`docs/NEXT_PHASE_PROMPT.md`** (updated at the end of every completed phase).

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 123
- Latest phase: Phase 123 — Playback export clip
- Latest commit: `(pending commit)`
- Latest tag: `phase-123-playback-export-clip`
- Push status: pending push to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **123**
- Purpose: Export bounded replay ranges as local clip manifests for sharing or offline review.
- CLI? **Yes** — `make playback-export` writes manifest JSON under `data/dev/` (gitignored)
- API? **Yes** — `GET /api/dev/playback-export` returns clip manifest (status only)
- UI? **Yes** — Export clip action in Range & loop panel with summary, copy JSON, download JSON
- Checks: frame list, cache/decode counts, optional preview paths from frame cache
- Tests: backend `test_playback_export.py`; frontend `playbackExport.test.ts`

## Current focus

Operators can export storm-segment clip manifests from the replay UI or CLI. Next: frame quality drill-down or clip import/replay from saved manifest.

## Next recommended phase

- Phase number: **124**
- Phase title: Frame quality drill-down
- Goal: Per-frame quality/readiness detail panel in replay UI — decode status, cache path hints, and remediation commands for frames in the active clip or catalog selection.
- Why this is next: Export completes the share/save loop; drill-down helps operators fix cold/missing frames before replay or re-export.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 124 only.
Add frame quality drill-down for catalog/clip frames in replay UI.
```

## Key docs (read order for new work)

1. `docs/NEXT_PHASE_PROMPT.md` — paste into Cursor to start the next phase
2. `docs/CHATGPT_REVIEW.md` (this file)
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_STEPS.md`
5. `docs/PHASE_LOG.md`
