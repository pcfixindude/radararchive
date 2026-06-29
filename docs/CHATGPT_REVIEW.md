# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 83
- Latest phase: Phase 83 — Candidate trend-hint acknowledgment status history
- Latest commit: `512d599`
- Latest tag: `phase-83-candidate-trend-hint-ack-status-history`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Candidate trend-hint acknowledgment status history: local advisory only
- Candidate trend-hint acknowledgment status rollup: local advisory only
- Candidate trend-hint review acknowledgments: local acknowledgment only
- Candidate trend hints (Phase 80 chain): local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **83**
- Purpose: Add local bounded history of trend-hint acknowledgment status rollups so operators can track coverage changes over time without production authorization.
- Main command added: `make mrms-render-candidate-trend-hint-ack-status-history`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status/history`
- Tests: backend 957 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - History does not clear alerts or mutate rollups or acknowledgments
  - History appends on status rollup refresh only
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with full candidate sandbox review chain (rollup, history, trend hints, acknowledgments) before any real MRMS rendering candidate attempt.

Next direction: candidate trend-hint review chain digest.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **84**
- Phase title: Candidate trend-hint review chain digest
- Goal: Add local digest combining trend-hint acknowledgment status rollup and history so operators can see a single coverage summary without production authorization.
- Why this is next: Phase 83 completes bounded history; Phase 84 should summarize rollup + history locally.
- Safety boundaries:
  - local-only digest by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 84 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
