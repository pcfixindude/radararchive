# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 71
- Latest phase: Phase 71 — Gated candidate sandbox comparison acknowledgment status history
- Latest commit: (pending)
- Latest tag: `phase-71-sandbox-comparison-acknowledgment-status-history`
- Push status: pending
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison acknowledgment status history: local bounded history only; does not clear alerts
- Render candidate sandbox comparison acknowledgment status: local rollup only
- Render candidate sandbox comparison review acknowledgment: local only
- Render candidate sandbox comparison trend hints: local advisory only
- Render candidate sandbox comparison history: local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **71**
- Purpose: Persist bounded local history of acknowledgment status rollups when status is refreshed so operators can track coverage changes over time.
- Main command added: `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/history`
- Tests: backend 816 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - History appends on status refresh only — read-only compact does not append
  - Max 25 entries; coverage change is rollup-rank advisory only
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with sandbox import/export, comparison history, trend hints, review acknowledgment, acknowledgment status, and acknowledgment status history before any real MRMS rendering candidate attempt.

Next direction: acknowledgment status trend hints derived from history.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **72**
- Phase title: Gated candidate sandbox comparison acknowledgment status trend hints
- Goal: Add local advisory trend hints derived from acknowledgment status history so operators can see recurring coverage patterns without clearing alerts or authorizing production use.
- Why this is next: Phase 71 adds bounded status history; Phase 72 should surface trend hints from that history for operator review.
- Safety boundaries:
  - local-only hints by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 72 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
