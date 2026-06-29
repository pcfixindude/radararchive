# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 75
- Latest phase: Phase 75 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status history
- Latest commit: `fbf606b`
- Latest tag: `phase-75-sandbox-status-trend-review-acknowledgment-status-history`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status history: local bounded history only
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status: local rollup only
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment: local only
- Render candidate sandbox comparison acknowledgment status trend hints: local advisory only
- Render candidate sandbox comparison acknowledgment status history: local bounded history only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **75**
- Purpose: Add bounded local history of trend review acknowledgment status rollups so operators can track coverage changes over time without production authorization.
- Main command added: `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-history`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/history`
- Tests: backend 863 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - History appends on status rollup refresh only
  - Coverage change is rollup-rank advisory — does not clear alerts
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with full acknowledgment status trend review chain (rollup, history) before any real MRMS rendering candidate attempt.

Next direction: status trend review acknowledgment status trend hints.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **76**
- Phase title: Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status trend hints
- Goal: Add local advisory trend hints derived from trend review acknowledgment status history so operators can see recurring coverage patterns without production authorization.
- Why this is next: Phase 75 adds bounded history; Phase 76 should derive advisory trend hints (mirrors Phase 71→72 flow).
- Safety boundaries:
  - local-only trend hints by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 76 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
