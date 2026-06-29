# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 76
- Latest phase: Phase 76 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status trend hints
- Latest commit: `b087d8b`
- Latest tag: `phase-76-sandbox-status-trend-review-acknowledgment-status-trend-hints`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend hints: local advisory only
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status history: local bounded history only
- Render candidate sandbox comparison acknowledgment status trend review acknowledgment status: local rollup only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **76**
- Purpose: Add local advisory trend hints derived from trend review acknowledgment status history so operators can see recurring coverage patterns without production authorization.
- Main command added: `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-hint`
- Tests: backend 875 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Trend hints are advisory metadata only — derived from trend review acknowledgment status history
  - Conservative `needs_review` when worsened/stale streaks detected
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with full trend review acknowledgment status chain (rollup, history, trend hints) before any real MRMS rendering candidate attempt.

Next direction: status trend review acknowledgment status trend review acknowledgment.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **77**
- Phase title: Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment
- Goal: Add local acknowledgment of reviewed trend review acknowledgment status trend hints so operators can record review without clearing validation alerts or verifying MRMS.
- Why this is next: Phase 76 adds status trend hints; Phase 77 should let operators acknowledge reviewed hints locally (mirrors Phase 72→73 flow).
- Safety boundaries:
  - local-only acknowledgment by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 77 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
