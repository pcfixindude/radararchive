# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 84
- Latest phase: Phase 84 — Candidate trend-hint review chain digest
- Latest commit: TBD
- Latest tag: `phase-84-candidate-trend-hint-review-digest`
- Push status: pending
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Candidate trend-hint review chain digest: local advisory only
- Candidate trend-hint acknowledgment status history: local advisory only
- Candidate trend-hint acknowledgment status rollup: local advisory only
- Candidate trend-hint review acknowledgments: local acknowledgment only
- Candidate trend hints (Phase 80 chain): local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **84**
- Purpose: Add local digest combining trend-hint acknowledgment status rollup and history so operators can see one coverage summary without production authorization.
- Main command added: `make mrms-render-candidate-trend-hint-review-digest`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest`
- Tests: TBD
- Known limitations:
  - Digest does not clear alerts or mutate rollups, history, or acknowledgments
  - Digest is advisory metadata only — not production authorization
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with full candidate sandbox review chain (rollup, history, digest, trend hints, acknowledgments) before any real MRMS rendering candidate attempt.

Next direction: candidate trend-hint review digest history.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **85**
- Phase title: Candidate trend-hint review digest history
- Goal: Add local bounded history of trend-hint review digests so operators can track digest changes over time without production authorization.
- Why this is next: Phase 84 adds the review chain digest; Phase 85 should persist bounded history on digest refresh.
- Safety boundaries:
  - local-only history by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 85 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
