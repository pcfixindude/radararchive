# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 70
- Latest phase: Phase 70 — Gated candidate sandbox comparison acknowledgment status
- Latest commit: (pending Phase 70 commit)
- Latest tag: `phase-70-sandbox-comparison-acknowledgment-status`
- Push status: pending
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison acknowledgment status: local rollup only; does not clear alerts
- Render candidate sandbox comparison review acknowledgment: local only
- Render candidate sandbox comparison trend hints: local advisory only
- Render candidate sandbox comparison history: local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **70**
- Purpose: Add local rollup status linking latest trend hints to review acknowledgments so operators can see whether current hints have been acknowledged.
- Main command added: `make mrms-render-candidate-sandbox-comparison-acknowledgment-status`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status`
- Tests: backend 803 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Status rollup is advisory metadata only — does not clear alerts or mutate acknowledgments
  - `stale_acknowledgment` when trend hint snapshot changes after last ack
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with sandbox import/export, comparison history, trend hints, review acknowledgment, and acknowledgment status before any real MRMS rendering candidate attempt.

Next direction: acknowledgment status history.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **71**
- Phase title: Gated candidate sandbox comparison acknowledgment status history
- Goal: Add bounded local history of acknowledgment status rollups so operators can track how coverage changed over time, without clearing alerts or authorizing production use.
- Why this is next: Phase 70 adds the status rollup; Phase 71 should persist bounded history of status changes for operator review.
- Safety boundaries:
  - local-only history by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 71 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
