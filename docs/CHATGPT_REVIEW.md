# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

For Cursor, paste the ready-to-run prompt from **`docs/NEXT_PHASE_PROMPT.md`** (updated at the end of every completed phase).

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 127
- Latest phase: Phase 127 — Import clip frame list sync
- Latest commit: (pending — phase 127 commit)
- Latest tag: `phase-127-import-clip-frame-list-sync`
- Push status: pending
- Final git status: clean except untracked `data/dev/agent_logs/` (not committed)

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **127**
- Purpose: When applying an imported clip, sync playback timestamp list from manifest frames (not just range endpoints) so replay matches the exported clip sequence.
- CLI? **No new CLI** — uses existing `make clip-import`
- API? **Backend helper only** — `extract_apply_frame_timestamps` in clip import service (no new endpoint)
- UI? **Yes** — apply preview (“Will restore N frames” vs range-only fallback); apply merges clip frame list into playback timeline
- Checks: bounded to `MAX_CLIP_FRAMES` (200); range/loop still applied; no auto warm/decode
- Tests: backend `test_clip_import.py` (apply timestamp helper); frontend `clipImport.test.ts`, `ClipImportPanel.test.tsx`

## Current focus

Applying an imported clip now restores the exported frame sequence into replay (when manifest includes frames), with a clear apply preview. Next: show playback position within the applied clip sequence.

## Next recommended phase

- Phase number: **128**
- Phase title: Applied clip sequence position
- Goal: After applying an imported clip frame list, show current position within the clip sequence in replay UI (e.g. “Clip frame 4/26”) and warn when the selected frame is outside the applied sequence.
- Why this is next: Frame list sync makes apply match export; operators need visible feedback on where they are in the restored clip.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 128 only.
Show applied clip sequence position in replay UI.
```

## Key docs (read order for new work)

1. `docs/NEXT_PHASE_PROMPT.md` — paste into Cursor to start the next phase
2. `docs/CHATGPT_REVIEW.md` (this file)
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_STEPS.md`
5. `docs/PHASE_LOG.md`
