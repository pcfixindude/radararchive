# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 69
- Latest phase: Phase 69 — Gated candidate sandbox comparison review acknowledgment
- Latest commit: see tag `phase-69-sandbox-comparison-review-acknowledgment`
- Latest tag: `phase-69-sandbox-comparison-review-acknowledgment`
- Push status: pending
- Phase 68 push status: pushed (`f91a3dd`, tag `phase-68-sandbox-comparison-trend-hints`)
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Render candidate sandbox comparison review acknowledgment: local only; does not clear alerts
- Render candidate sandbox comparison trend hints: local advisory only
- Render candidate sandbox comparison history: local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **69**
- Purpose: Add local acknowledgment of reviewed sandbox comparison trend hints so operators can record review without clearing validation alerts or verifying MRMS.
- Main command added: `make mrms-render-candidate-sandbox-comparison-review-acknowledgment`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments`
- Tests: backend 790 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Acknowledgment is local review evidence only — does not clear alerts or change trend hints
  - `trend_review_still_recommended` may remain true after acknowledgment
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with sandbox import/export, comparison history, trend hints, and review acknowledgment before any real MRMS rendering candidate attempt.

Next direction: acknowledgment status rollup.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **70**
- Phase title: Gated candidate sandbox comparison acknowledgment status
- Goal: Add local rollup status linking latest trend hints to review acknowledgments so operators can see whether current hints have been acknowledged, without clearing alerts or authorizing production use.
- Why this is next: Phase 69 records acknowledgments; Phase 70 should summarize acknowledgment coverage against current trend hints locally.
- Safety boundaries:
  - local-only status rollup by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 70 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
