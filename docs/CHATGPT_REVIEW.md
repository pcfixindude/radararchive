# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 95
- Latest phase: Phase 95 — Gated sandbox manifest import/export
- Latest commit: `872da3b`
- Latest tag: `phase-95-gated-sandbox-manifest-import-export`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated manifest import/export: local advisory only; skips manifest IO when upstream gates are closed

## Latest phase summary

- Phase: **95**
- Purpose: Run or review local sandbox manifest import/export only when preflight is `candidate_preflight_ready`, dry-run plan is `dry_run_plan_ready`, scaffold is `scaffold_ready`, and sandbox layout is `sandbox_layout_ready`.
- Main command added: `make mrms-review-gated-manifest-io` (alias: `make mrms-render-candidate-gated-manifest-io`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-manifest-io`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; dry-run plan **skipped**; scaffold **skipped**; sandbox **skipped**; manifest IO **skipped**
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated reviews through manifest IO
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh`
  4. `make mrms-review-gated-scaffold --refresh`
  5. `make mrms-review-gated-sandbox-layout --refresh`
  6. `make mrms-review-gated-manifest-io --refresh` (when sandbox layout is sandbox_layout_ready)
- Tests: backend 1093 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated reviews when upstream gates open.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **96**
- Phase title: Gated sandbox comparison history
- Goal: Run gated local sandbox comparison history when manifest import/export is `manifest_io_ready`.
- Why this is next: Phase 95 correctly gates manifest IO on all upstream gates; once manifest IO is ready, comparison history is the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 96 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
