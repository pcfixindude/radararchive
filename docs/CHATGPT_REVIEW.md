# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 87
- Latest phase: Phase 87 — Candidate review readiness consolidation
- Latest commit: `bddaf0f`
- Latest tag: `phase-87-candidate-review-readiness-consolidation`
- Push status: pushed
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Candidate review readiness: local advisory consolidation only
- Candidate trend-hint review chain (hints, acks, rollup, history, digest, diff): local advisory only
- Render candidate sandbox import/export: local metadata/report-only

## Latest phase summary

- Phase: **87**
- Purpose: Consolidate the candidate trend-hint review chain into one operator readiness summary with blockers, regeneration hints, and gated preflight status — without another metadata-only layer.
- Main command added: `make mrms-render-candidate-review-readiness`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox/review-readiness`
- Tests: backend 1008 passed; frontend vitest 8 passed; frontend build OK
- Known limitations:
  - Readiness summary does not clear alerts or mutate gates, digests, or acknowledgments
  - `gated_preflight_ready` / `preflight_candidate_ready` are not production authorization
  - `verified_mrms` remains false
  - Review chain is typically **not** complete on a fresh dev tree — blockers are expected until operators refresh the chain

## Current focus

Use the consolidated readiness summary to decide when to attempt a **gated real MRMS render candidate preflight** (Phase 62 command) after visual evidence and the trend-hint review chain are in order.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **88**
- Phase title: Gated real MRMS render candidate preflight attempt
- Goal: Run the existing gated preflight workflow deliberately when review readiness shows `ready_for_preflight`, resolving any remaining visual-evidence blockers first.
- Why this is next: Phase 87 consolidates the review chain; the next meaningful step is operator execution of the existing preflight gate — not another digest/rollup/history layer.
- If blockers remain (typical on fresh dev): resolve them with the suggested commands in the readiness summary before Phase 88.
- Safety boundaries:
  - preflight remains advisory and gated
  - no MRMS verification claim
  - no production rendering or tile serving by default
  - no alert clearing
  - no catalog/render gate mutation

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 88 only.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
