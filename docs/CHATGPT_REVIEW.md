# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 97
- Latest phase: Phase 97 — Gated sandbox comparison trend hint
- Latest commit: (pending)
- Latest tag: `phase-97-gated-sandbox-comparison-trend-hint`
- Push status: pending
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated trend hint review: local advisory only; skips trend hints when upstream gates are closed

## Latest phase summary

- Phase: **97**
- Purpose: Run or review local sandbox comparison trend hints only when preflight is `candidate_preflight_ready`, dry-run plan is `dry_run_plan_ready`, scaffold is `scaffold_ready`, sandbox layout is `sandbox_layout_ready`, manifest IO is `manifest_io_ready`, and comparison history is `comparison_history_ready`.
- Main command added: `make mrms-review-gated-trend` (alias: `make mrms-render-candidate-gated-trend-review`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-trend-review`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; comparison **skipped**; trend hint **skipped**
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated reviews through trend hint
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh`
  4. `make mrms-review-gated-scaffold --refresh`
  5. `make mrms-review-gated-sandbox-layout --refresh`
  6. `make mrms-review-gated-manifest-io --refresh`
  7. `make mrms-review-gated-comparison --refresh`
  8. `make mrms-review-gated-trend --refresh` (when comparison history is comparison_history_ready)
- Tests: backend 1111 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated reviews when upstream gates open.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **98**
- Phase title: Gated sandbox comparison acknowledgment
- Goal: Run gated local sandbox comparison acknowledgment when trend hint is `trend_hint_ready` or `trend_hint_needs_review`.
- Why this is next: Phase 97 correctly gates trend hints on all upstream gates; once trend hints are ready, acknowledgment is the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 98 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
