# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 96
- Latest phase: Phase 96 — Gated sandbox comparison history
- Latest commit: (pending commit)
- Latest tag: `phase-96-gated-sandbox-comparison-history`
- Push status: pending
- Final git status: source changes staged for commit

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated comparison history: local advisory only; skips comparison history when upstream gates are closed

## Latest phase summary

- Phase: **96**
- Purpose: Run or review local sandbox comparison history only when preflight is `candidate_preflight_ready`, dry-run plan is `dry_run_plan_ready`, scaffold is `scaffold_ready`, sandbox layout is `sandbox_layout_ready`, and manifest IO is `manifest_io_ready`.
- Main command added: `make mrms-review-gated-comparison` (alias: `make mrms-render-candidate-gated-comparison-history`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-comparison-review`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; manifest IO **skipped**; comparison **skipped**
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated reviews through comparison history
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh`
  4. `make mrms-review-gated-scaffold --refresh`
  5. `make mrms-review-gated-sandbox-layout --refresh`
  6. `make mrms-review-gated-manifest-io --refresh`
  7. `make mrms-review-gated-comparison --refresh` (when manifest IO is manifest_io_ready)
- Tests: backend 1102 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated reviews when upstream gates open.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **97**
- Phase title: Gated sandbox comparison trend hint
- Goal: Run gated local sandbox comparison trend hints when comparison history is `comparison_history_ready`.
- Why this is next: Phase 96 correctly gates comparison history on all upstream gates; once comparison history is ready, trend hints are the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 97 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
