# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 94
- Latest phase: Phase 94 — Gated candidate artifact sandbox layout
- Latest commit: (pending commit)
- Latest tag: `phase-94-gated-candidate-artifact-sandbox-layout`
- Push status: pending
- Final git status: source changes staged for commit

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated sandbox layout: local advisory only; skips sandbox generation when preflight, dry-run plan, or scaffold gates are closed

## Latest phase summary

- Phase: **94**
- Purpose: Generate or review local candidate artifact sandbox layout only when preflight is `candidate_preflight_ready`, dry-run plan is `dry_run_plan_ready`, and scaffold is `scaffold_ready`.
- Main command added: `make mrms-review-gated-sandbox-layout` (alias: `make mrms-render-candidate-gated-sandbox-layout`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-layout-review`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; dry-run plan **skipped**; scaffold **skipped**; sandbox **skipped**
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated dry-run, scaffold, and sandbox layout reviews
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh`
  4. `make mrms-review-gated-scaffold --refresh`
  5. `make mrms-review-gated-sandbox-layout --refresh` (when scaffold is scaffold_ready)
- Tests: backend 1084 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated reviews when upstream gates open.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **95**
- Phase title: Gated candidate sandbox manifest import/export
- Goal: Run gated local sandbox manifest import/export when sandbox layout is `sandbox_layout_ready`.
- Why this is next: Phase 94 correctly gates sandbox layout on preflight, dry-run plan, and scaffold; once layout is ready, manifest import/export is the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 95 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
