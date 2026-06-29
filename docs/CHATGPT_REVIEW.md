# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 93
- Latest phase: Phase 93 — Gated render candidate scaffold review
- Latest commit: `7052e72`
- Latest tag: `phase-93-gated-render-candidate-scaffold-review`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated scaffold review: local advisory only; skips scaffold generation when preflight is not `candidate_preflight_ready` or dry-run plan is not `dry_run_plan_ready`

## Latest phase summary

- Phase: **93**
- Purpose: Evaluate disabled-by-default render candidate scaffold only after preflight reaches `candidate_preflight_ready` and dry-run plan reaches `dry_run_plan_ready`.
- Main command added: `make mrms-review-gated-scaffold` (alias: `make mrms-render-candidate-gated-scaffold-review`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-scaffold-review`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; dry-run plan **skipped**; scaffold **skipped**
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated dry-run review and gated scaffold review
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh` (when preflight is candidate_preflight_ready)
  4. `make mrms-review-gated-scaffold --refresh` (when dry-run plan is dry_run_plan_ready)
- Tests: backend 1074 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated dry-run review when `candidate_preflight_ready`, then gated scaffold review when `dry_run_plan_ready`.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **94**
- Phase title: Gated candidate artifact sandbox layout
- Goal: Generate gated local sandbox directory layout when scaffold review is `scaffold_ready`.
- Why this is next: Phase 93 correctly gates scaffold on preflight and dry-run plan; once both gates open and scaffold is ready, sandbox layout is the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 94 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
