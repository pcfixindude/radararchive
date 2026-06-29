# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 85
- Latest phase: Phase 85 — Candidate trend-hint review digest history
- Latest commit: TBD
- Latest tag: `phase-85-candidate-trend-hint-review-digest-history`
- Push status: pending
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Candidate trend-hint review digest history: local advisory only
- Candidate trend-hint review chain digest: local advisory only
- Candidate trend-hint acknowledgment status history: local advisory only
- Candidate trend-hint acknowledgment status rollup: local advisory only
- Candidate trend-hint review acknowledgments: local acknowledgment only
- Candidate trend hints (Phase 80 chain): local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **85**
- Purpose: Add local bounded history of trend-hint review digests so operators can track digest changes over time without production authorization.
- Main command added: `make mrms-render-candidate-trend-hint-review-digest-history`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest/history`
- Tests: TBD
- Known limitations:
  - History does not clear alerts or mutate digests, rollups, or acknowledgments
  - History appends on review digest refresh only
  - `verified_mrms` remains false

## Current focus

Local visual evidence review block with full candidate sandbox review chain (rollup, history, digest, digest history, trend hints, acknowledgments) before any real MRMS rendering candidate attempt.

Next direction: candidate trend-hint review digest diff.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **86**
- Phase title: Candidate trend-hint review digest diff
- Goal: Add local diff between consecutive trend-hint review digests so operators can see digest change signals without production authorization.
- Why this is next: Phase 85 completes bounded digest history; Phase 86 should compare consecutive digests locally.
- Safety boundaries:
  - local-only diff by default
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 86 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
