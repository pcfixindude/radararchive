# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 98
- Latest phase: Phase 98 — Gated sandbox comparison acknowledgment
- Latest commit: (pending)
- Latest tag: `phase-98-gated-sandbox-comparison-acknowledgment`
- Push status: pending
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated comparison acknowledgment: local advisory only; skips acknowledgment when upstream gates are closed

## Latest phase summary

- Phase: **98**
- Purpose: Run or review local sandbox comparison acknowledgment only when preflight is `candidate_preflight_ready`, dry-run plan is `dry_run_plan_ready`, scaffold is `scaffold_ready`, sandbox layout is `sandbox_layout_ready`, manifest IO is `manifest_io_ready`, comparison history is `comparison_history_ready`, and trend hint is `trend_hint_ready` or `trend_hint_needs_review`.
- Main command added: `make mrms-review-gated-ack` (alias: `make mrms-render-candidate-gated-comparison-ack`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-ack-review`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; trend **skipped**; acknowledgment **skipped**
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated reviews through acknowledgment
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh`
  4. `make mrms-review-gated-scaffold --refresh`
  5. `make mrms-review-gated-sandbox-layout --refresh`
  6. `make mrms-review-gated-manifest-io --refresh`
  7. `make mrms-review-gated-comparison --refresh`
  8. `make mrms-review-gated-trend --refresh`
  9. `make mrms-review-gated-ack --refresh` (when trend hint is trend_hint_ready or trend_hint_needs_review)
- Tests: backend 1120 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated reviews when upstream gates open.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **99**
- Phase title: Gated sandbox acknowledgment history
- Goal: Run gated local sandbox acknowledgment history when comparison acknowledgment is `comparison_ack_ready` or `comparison_ack_needs_acknowledgment`.
- Why this is next: Phase 98 correctly gates acknowledgment on all upstream gates; once acknowledgment status is ready, history is the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 99 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
