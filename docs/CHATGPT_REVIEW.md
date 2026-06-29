# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 90
- Latest phase: Phase 90 — Bootstrap sandbox comparison trend-hint chain
- Latest commit: `b5361ee`
- Latest tag: `phase-90-bootstrap-sandbox-trend-hint-chain`
- Push status: pushed
- Final git status: source changes staged for commit

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Trend-hint chain bootstrap: local advisory only; skips gated preflight when visual sample readiness is blocked

## Latest phase summary

- Phase: **90**
- Purpose: Seed sandbox comparison history and refresh the candidate trend-hint chain so ack rollup and review digest reach current/stable without forcing preflight.
- Main command added: `make mrms-bootstrap-trend-hint-chain` (alias: `make mrms-render-candidate-trend-hint-chain-bootstrap`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap`
- Local operator run result: **chain_ready_visual_blocked** — trend-hint chain **ready** (`rollup=not_needed`, `digest=stable`, `chain=chain_ready`, `overall=ready_for_preflight`); preflight **not run** (`preflight_not_run=true`)
- Remaining blockers (this dev tree):
  - visual sample readiness: no_sample_set
- Next commands for operators:
  1. `make mrms-visual-review`
  2. `make mrms-visual-review-sample-set`
  3. `make mrms-visual-review-readiness --refresh`
  4. `make mrms-resolve-preflight-blockers --refresh` (retry after visual bootstrap)
- Tests: backend 1041 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Bootstrap **visual review sample set** so gated preflight can run when review readiness opens fully.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **91**
- Phase title: Bootstrap visual review sample set
- Goal: Create local visual review sample set and annotations so visual sample readiness reaches `candidate_ready` and gated preflight can run.
- Why this is next: Phase 90 bootstrap cleared trend-hint chain blockers; visual `no_sample_set` is the sole remaining preflight gate.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 91 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
