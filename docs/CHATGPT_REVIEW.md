# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 74
- Latest phase: Phase 74 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status
- Latest commit: `b55b6ae`
- Latest tag: `phase-74-sandbox-status-trend-review-acknowledgment-status`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status: local rollup only
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment: local only
- Render candidate sandbox comparison acknowledgment status trend hints: local advisory only
- Render candidate sandbox comparison acknowledgment status history: local bounded history only
- Render candidate sandbox comparison acknowledgment status: local rollup only
- Render candidate sandbox comparison review acknowledgment: local only
- Render candidate sandbox comparison trend hints: local advisory only
- Render candidate sandbox comparison history: local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **74**
- Purpose: Add local rollup linking status trend hints to trend review acknowledgments so operators can see acknowledgment coverage without production authorization.
- Main command added: `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status`
- Tests: backend 850 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Rollup is advisory metadata only — does not clear alerts or mutate trend hints
  - `stale_acknowledgment` when status trend hint changes after acknowledgment
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with sandbox import/export, comparison history, trend hints, review acknowledgment, acknowledgment status, status history, status trend hints, status trend review acknowledgment, and status trend review acknowledgment status before any real MRMS rendering candidate attempt.

Next direction: status trend review acknowledgment status history.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **75**
- Phase title: Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status history
- Goal: Add bounded local history of trend review acknowledgment status rollups so operators can track coverage changes over time without production authorization.
- Why this is next: Phase 74 adds trend review acknowledgment status rollup; Phase 75 should capture bounded history (mirrors Phase 70→71 flow).
- Safety boundaries:
  - local-only history by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 75 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
