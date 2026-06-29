# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 73
- Latest phase: Phase 73 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment
- Latest commit: (pending push)
- Latest tag: `phase-73-sandbox-acknowledgment-status-trend-review-acknowledgment`
- Push status: pending
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment: local only
- Render candidate sandbox comparison acknowledgment status trend hints: local advisory only
- Render candidate sandbox comparison acknowledgment status history: local bounded history only
- Render candidate sandbox comparison acknowledgment status: local rollup only
- Render candidate sandbox comparison review acknowledgment: local only
- Render candidate sandbox comparison trend hints: local advisory only
- Render candidate sandbox comparison history: local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **73**
- Purpose: Add local acknowledgment of reviewed acknowledgment status trend hints so operators can record review without clearing validation alerts or verifying MRMS.
- Main command added: `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgments`
- Tests: backend 838 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Acknowledgment does not clear alerts or mutate status trend hints
  - `trend_review_still_recommended` may remain true after acknowledgment
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with sandbox import/export, comparison history, trend hints, review acknowledgment, acknowledgment status, status history, status trend hints, and status trend review acknowledgment before any real MRMS rendering candidate attempt.

Next direction: status trend review acknowledgment status rollup.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **74**
- Phase title: Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status
- Goal: Add local rollup linking status trend hints to trend review acknowledgments so operators can see acknowledgment coverage without production authorization.
- Why this is next: Phase 73 adds status trend review acknowledgments; Phase 74 should rollup hint vs acknowledgment state locally (mirrors Phase 69→70 flow).
- Safety boundaries:
  - local-only rollup by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 74 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
