# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 82
- Latest phase: Phase 82 — Candidate trend-hint acknowledgment status rollup
- Latest commit: `436cb38`
- Latest tag: `phase-82-candidate-trend-hint-ack-status-rollup`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Candidate trend-hint acknowledgment status rollup: local advisory only
- Candidate trend-hint review acknowledgments: local acknowledgment only
- Candidate trend hints (Phase 80 chain): local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **82**
- Purpose: Add local rollup linking candidate trend hints to trend-hint review acknowledgments so operators can see combined coverage without production authorization.
- Main command added: `make mrms-render-candidate-trend-hint-ack-status`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status`
- Tests: backend 944 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Rollup does not clear alerts or mutate trend hints or acknowledgments
  - `trend_review_recommended` may remain true after acknowledgment
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with full candidate sandbox review chain (rollup, history, trend hints, acknowledgments) before any real MRMS rendering candidate attempt.

Next direction: candidate trend-hint acknowledgment status history.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **83**
- Phase title: Candidate trend-hint acknowledgment status history
- Goal: Add local bounded history of trend-hint acknowledgment status rollups so operators can track coverage changes over time without production authorization.
- Why this is next: Phase 82 adds the trend-hint acknowledgment status rollup; Phase 83 should persist bounded history on refresh.
- Safety boundaries:
  - local-only history by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 83 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
