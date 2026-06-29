# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 89
- Latest phase: Phase 89 — Resolve preflight blockers
- Latest commit: `ea077aa`
- Latest tag: `phase-89-resolve-preflight-blockers`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Preflight blocker resolution: local advisory only; does not force preflight when gate closed

## Latest phase summary

- Phase: **89**
- Purpose: Run the documented refresh flow, record remaining blockers, and retry gated preflight only when readiness allows.
- Main command added: `make mrms-resolve-preflight-blockers` (alias: `make mrms-render-candidate-preflight-blockers`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/preflight-blockers`
- Local operator run result: **still_blocked** — preflight **not run** (`blocked_by_readiness`)
- Remaining blockers (this dev tree):
  - acknowledgment status rollup is missing
  - review digest is missing
  - visual sample readiness: no_sample_set
  - review readiness gate closed (`overall=blocked`, `chain=blocked`)
- Next commands for operators:
  1. `make mrms-render-candidate-sandbox-comparison-trend-hint --refresh`
  2. `make mrms-render-candidate-trend-hint-ack-status --refresh`
  3. `make mrms-render-candidate-trend-hint-review-digest --refresh`
  4. `make mrms-visual-review` then `make mrms-visual-review-sample-set`
  5. `make mrms-visual-review-readiness --refresh`
  6. `make mrms-resolve-preflight-blockers --refresh` (retry after upstream fixes)
- Tests: backend 1030 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Bootstrap the **sandbox comparison trend-hint chain** and **visual review sample set** so review readiness opens and gated preflight can run.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **90**
- Phase title: Bootstrap sandbox comparison trend-hint chain
- Goal: Seed sandbox comparison history and refresh the candidate trend-hint chain so ack rollup and review digest can reach `current`/`stable`.
- Why this is next: Phase 89 blocker report shows `blocker_category=candidate_trend_hint_chain` with missing ack rollup as primary blocker. Visual sample set is a parallel blocker — address in Phase 90 follow-up or Phase 91 if trend-hint chain alone is insufficient.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 90 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
