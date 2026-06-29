# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 88
- Latest phase: Phase 88 — Gated real MRMS render candidate preflight attempt
- Latest commit: `cd6e8d2`
- Latest tag: `phase-88-gated-real-mrms-candidate-preflight`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated preflight attempt: local advisory only; skips preflight when review readiness has blockers
- Candidate review readiness: local advisory consolidation only

## Latest phase summary

- Phase: **88**
- Purpose: Gate the existing MRMS render candidate preflight behind Phase 87 review readiness — run preflight only when `ready_for_preflight`, otherwise record blockers without forcing preflight.
- Main command added: `make mrms-render-candidate-preflight-attempt`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/preflight-attempt`
- Local operator run (this dev tree): **blocked_by_readiness** — preflight **not run**
  - Review readiness: `chain_readiness_level=blocked`, `overall_readiness_level=blocked`
  - Primary blocker: acknowledgment status rollup missing
  - Regeneration hint: digest not persisted
- Operator commands to clear blockers before retrying gated preflight:
  1. `make mrms-render-candidate-trend-hint-ack-status --refresh`
  2. `make mrms-render-candidate-trend-hint-review-digest --refresh`
  3. `make mrms-render-candidate-review-readiness --refresh`
  4. When readiness shows `ready_for_preflight`: `make mrms-render-candidate-preflight-attempt --refresh`
  5. Visual evidence still required for preflight pass: `make mrms-visual-review-readiness --refresh` then `make mrms-render-candidate-preflight --refresh` (or use gated attempt after chain is ready)
- Tests: backend 1019 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Clear review-chain blockers, then retry gated preflight. When preflight reaches `candidate_preflight_ready`, move to dry-run plan review — not production rendering.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **89**
- Phase title: Resolve visual evidence preflight blockers
- Goal: Clear the remaining review-chain and visual-evidence blockers so gated preflight can run and reach `candidate_preflight_ready`.
- Why this is next: Phase 88 local attempt was `blocked_by_readiness` with missing ack rollup/digest; preflight was correctly not forced. Operators must complete the trend-hint chain and visual sample readiness before dry-run evaluation.
- If preflight already `candidate_preflight_ready` on your tree: skip to **Phase 89 alternate — gated render candidate dry-run plan review**.
- Safety boundaries:
  - no MRMS verification claim
  - no production rendering or tile serving by default
  - no alert clearing
  - no catalog/render gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 89 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
