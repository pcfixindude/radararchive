# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 92
- Latest phase: Phase 92 — Gated render candidate dry-run plan review
- Latest commit: `b16e3c0`
- Latest tag: `phase-92-gated-render-candidate-dry-run-plan`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated dry-run review: local advisory only; skips dry-run plan generation when preflight is not `candidate_preflight_ready`

## Latest phase summary

- Phase: **92**
- Purpose: Review gated preflight advisory result and evaluate/generate dry-run plan only when preflight evidence supports it.
- Main command added: `make mrms-review-gated-dry-run-plan` (alias: `make mrms-render-candidate-gated-dry-run-review`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-dry-run-review`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; dry-run plan **skipped** (`dry_run_plan_skipped=true`)
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated dry-run review
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh` (retry after preflight is candidate_preflight_ready)
- Tests: backend 1063 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated dry-run review when `candidate_preflight_ready`.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **93**
- Phase title: Gated render candidate scaffold review
- Goal: Evaluate the disabled-by-default render candidate scaffold when dry-run plan is `dry_run_plan_ready`.
- Why this is next: Phase 92 correctly gates dry-run plan on preflight; once preflight reaches `candidate_preflight_ready` and dry-run plan is ready, scaffold review is the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 93 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
