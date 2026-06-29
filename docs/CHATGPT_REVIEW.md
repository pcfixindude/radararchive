# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 68
- Latest phase: Phase 68 — Gated candidate sandbox comparison trend hints
- Latest commit: see tag `phase-68-sandbox-comparison-trend-hints`
- Latest tag: `phase-68-sandbox-comparison-trend-hints`
- Push status: pending
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison trend hints: local advisory only; does not verify MRMS or clear alerts
- Render candidate sandbox comparison history: local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **68**
- Purpose: Add local trend hints across sandbox comparison history so operators can spot recurring changes.
- Main command added: `make mrms-render-candidate-sandbox-comparison-trend-hint`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-trend-hint`
- Tests: backend 779 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Trend hints are advisory metadata only — derived from comparison history
  - Conservative `needs_review` when changed streak or recurring signals detected
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with sandbox import/export, comparison history, and trend hints before any real MRMS rendering candidate attempt.

Next direction: comparison review acknowledgment.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **69**
- Phase title: Gated candidate sandbox comparison review acknowledgment
- Goal: Add local acknowledgment of reviewed sandbox comparison trend hints so operators can record review without clearing validation alerts or verifying MRMS.
- Why this is next: Phase 68 adds trend hints; Phase 69 should let operators acknowledge reviewed hints locally without production side effects.
- Safety boundaries:
  - local-only acknowledgment by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 69 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
