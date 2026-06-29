# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 99
- Latest phase: Phase 99 — Gated sandbox acknowledgment history
- Latest commit: `993336b`
- Latest tag: `phase-99-gated-sandbox-acknowledgment-history`
- Push status: pushed
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Gated acknowledgment history: local advisory only; skips history when upstream gates are closed

## Latest phase summary

- Phase: **99**
- Purpose: Run or review local sandbox acknowledgment history only when all upstream gates are open through comparison acknowledgment (`comparison_ack_ready` or `comparison_ack_needs_acknowledgment`).
- Main command added: `make mrms-review-gated-ack-history` (alias: `make mrms-render-candidate-gated-ack-history`)
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-ack-history`
- Local operator run result: **preflight_not_candidate_ready** — preflight `needs_review`; ack **skipped**; history **skipped**
- Remaining follow-up: resolve preflight warnings/blockers until `candidate_preflight_ready`, then re-run gated reviews through acknowledgment history
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh`
  2. `make mrms-resolve-preflight-blockers --refresh`
  3. `make mrms-review-gated-dry-run-plan --refresh`
  4. `make mrms-review-gated-scaffold --refresh`
  5. `make mrms-review-gated-sandbox-layout --refresh`
  6. `make mrms-review-gated-manifest-io --refresh`
  7. `make mrms-review-gated-comparison --refresh`
  8. `make mrms-review-gated-trend --refresh`
  9. `make mrms-review-gated-ack --refresh`
  10. `make mrms-review-gated-ack-history --refresh` (when comparison acknowledgment is ready)
- Tests: backend 1129 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Resolve preflight `needs_review` blockers, then re-run gated reviews when upstream gates open.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **100**
- Phase title: Gated sandbox acknowledgment trend hint
- Goal: Run gated local sandbox acknowledgment trend hints when acknowledgment history is `ack_history_ready`.
- Why this is next: Phase 99 correctly gates acknowledgment history on all upstream gates; once history is ready, trend hints are the next gated evaluation step.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 100 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
