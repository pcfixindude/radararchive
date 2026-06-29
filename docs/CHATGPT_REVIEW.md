# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 91
- Latest phase: Phase 91 — Bootstrap visual review sample set
- Latest commit: `980f504`
- Latest tag: `phase-91-bootstrap-visual-review-sample-set`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Visual sample bootstrap: local advisory only; seeds acceptable annotations for drilldown — not production authorization

## Latest phase summary

- Phase: **91**
- Purpose: Create local visual review sample set and annotations so visual sample readiness reaches `candidate_ready` and gated preflight can run.
- Main command added: `make mrms-bootstrap-visual-sample-set` (alias: `make mrms-visual-review-sample-bootstrap`)
- API added: `GET/POST /api/validation/mrms-visual-review/sample-set/bootstrap`
- Local operator run result: **preflight_attempted** — visual **candidate_ready** (`all_samples_acceptable`); review readiness **ready_for_preflight**; gated preflight **ran** (`preflight_not_run=false`)
- Remaining follow-up: review advisory preflight result and complete any preflight evidence blockers before dry-run plan
- Next commands for operators:
  1. `make mrms-render-candidate-preflight --refresh` (review advisory preflight report)
  2. `make mrms-resolve-preflight-blockers --refresh` (if blockers remain)
- Tests: backend 1054 passed; frontend vitest 8 passed; frontend build OK

## Current focus

Review gated preflight advisory result and move toward **dry-run plan review** when `candidate_preflight_ready`.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **92**
- Phase title: Gated render candidate dry-run plan review
- Goal: Evaluate the dry-run plan when preflight reaches `candidate_preflight_ready` or after reviewing the latest gated preflight attempt.
- Why this is next: Phase 91 bootstrap cleared visual sample readiness; gated preflight attempt ran with advisory result captured.
- Safety boundaries:
  - local sandbox metadata only
  - no MRMS verification claim
  - no production rendering or tile serving
  - no alert clearing
  - no gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 92 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
