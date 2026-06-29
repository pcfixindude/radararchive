# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 78
- Latest phase: Phase 78 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status
- Latest commit: `c12e1a1`
- Latest tag: `phase-78-sandbox-trend-review-acknowledgment-status-rollup`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status: local rollup only
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment: local acknowledgment only
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend hints: local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **78**
- Purpose: Add local rollup linking trend review acknowledgment status trend hints to trend review acknowledgments so operators can see combined coverage without production authorization.
- Main command added: `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status`
- Tests: backend 897 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Rollup is advisory metadata only — does not clear alerts or mutate trend hints
  - `needs_acknowledgment` / `stale` rollup states are not production authorization
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with full trend review acknowledgment status chain (rollup, history, trend hints, trend review acknowledgment, status rollup) before any real MRMS rendering candidate attempt.

Next direction: trend review acknowledgment status trend review acknowledgment status history.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **79**
- Phase title: Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status history
- Goal: Add local bounded history of trend review acknowledgment status rollups so operators can track coverage changes over time without production authorization.
- Why this is next: Phase 78 adds status rollup; Phase 79 should capture bounded history locally (mirrors Phase 74→75 flow).
- Safety boundaries:
  - local-only history by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 79 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
