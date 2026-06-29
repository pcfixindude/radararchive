# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 67
- Latest phase: Phase 67 — Gated candidate sandbox manifest comparison history
- Latest commit: `1a20eff`
- Latest tag: `phase-67-sandbox-comparison-history`
- Push status: pushed to origin main with tag
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison history: local advisory only; records metadata comparisons from import/export; not production authorization
- Render candidate sandbox import/export: local metadata/report-only
- Scheduled visual review: explicit opt-in only

## Latest phase summary

- Phase: **67**
- Purpose: Add local comparison history for candidate sandbox exports/imports so operators can review changes across candidate artifact reports.
- Main command added: `make mrms-render-candidate-sandbox-comparison-history`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-history`
- Tests: backend 767 passed; frontend vitest 8 passed; frontend build succeeded
- Known limitations:
  - History records metadata comparisons only — no binary artifacts
  - Entries recorded automatically on import and on export-vs-previous-export pairs
  - Bounded history (25 entries)
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with sandbox import/export and comparison history before any real MRMS rendering candidate attempt.

Next direction: comparison trend hints across history.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **68**
- Phase title: Gated candidate sandbox comparison trend hints
- Goal: Add local trend hints across sandbox comparison history so operators can spot recurring changes without touching production tile serving or verifying MRMS.
- Why this is next: Phase 67 persists comparison history; Phase 68 should summarize trends/hints for operator review.
- Safety boundaries:
  - local-only trend hints by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no download/decode/render by default
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 68 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
