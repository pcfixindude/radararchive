# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 63
- Latest phase: Phase 63 — Gated real MRMS rendering candidate dry-run plan
- Latest commit: `0a7940e`
- Latest tag: `phase-63-render-candidate-dry-run-plan`
- Push status: pushed to origin main with tag
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- External notifications: **none**
- MRMS visual review: local-only; does not download/decode MRMS; does not create tiles; does not verify MRMS
- Visual review sample set: local drilldown only; does not verify MRMS, clear alerts, or enable production rendering
- Sample-set annotations/readiness: local advisory only; `candidate_ready` is **not** production authorization
- Render candidate preflight: local advisory only; `candidate_preflight_ready` is **not** production authorization
- Render candidate dry-run plan: local advisory only; does not download/decode/render by default; `dry_run_plan_ready` is **not** production authorization
- Scheduled visual review: explicit opt-in only via `--visual-review` or `make scheduled-proof-bundle-visual-review`

## Latest phase summary

- Phase: **63**
- Purpose: Add a local dry-run plan documenting prerequisites, safety checks, future operator commands, expected artifacts, rollback/stop conditions, and evidence checklist without executing candidate steps.
- Main command added: `make mrms-render-candidate-dry-run-plan`
- API added: `GET/POST /api/validation/mrms-render-candidate/dry-run-plan`
- Tests: backend 687 passed; frontend vitest 8 passed; frontend build succeeded
- Known limitations:
  - Dry-run plan is advisory/local-only — listed commands are NOT run by this phase
  - Conservative blocking when Phase 62 preflight is missing/blocked or sample readiness is not candidate_ready
  - `needs_review` when preflight has warnings but no blockers
  - `verified_mrms` remains false

## Current capabilities

- Local radar archive app with placeholder-first tile serving
- MRMS discovery, download, inspection, and decode prototype history
- Render queue/status and Dev Validation dashboard
- Proof reports, proof history, regression checks, proof bundles, and proof bundle diffs
- Operator handoff, validation alerts, escalation, digest, and acknowledgments
- Review sessions, comparisons, Markdown exports, export diffs/trends/hints
- Operator Review Status and grouped workflow presets with copy-ready commands
- Dev Validation UX with collapsible sections, preset filters, and safety wording
- MRMS visual review manifests, Markdown reports, history, comparison, and stale hints
- Scheduled proof, review export, operator status, and optional visual review workflows
- Visual review sample-set JSON/Markdown with drilldown UI
- Sample-set annotations JSON, readiness Markdown, and Dev Validation annotation/readiness UI
- Render candidate preflight JSON/Markdown with Dev Validation preflight UI
- Render candidate dry-run plan JSON/Markdown with Dev Validation dry-run plan UI

## Current focus

The project is in the **local visual evidence review** block with gated preflight and dry-run planning before any real MRMS rendering candidate attempt.

The next major direction should add an explicitly disabled-by-default command scaffold for a future candidate attempt.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **64**
- Phase title: Gated real MRMS rendering candidate command scaffold
- Goal: Add an explicitly disabled-by-default command scaffold for a future real MRMS rendering candidate attempt, with hard safety gates, dry-run-only default behavior, and no production tile serving.
- Why this is next: Phase 63 documents the gated dry-run operator path; Phase 64 should scaffold future commands with hard safety gates while remaining disabled by default.
- Safety boundaries:
  - local-only scaffold by default
  - no MRMS verification claim
  - no production rendering
  - no download/decode/render execution unless explicitly gated and disabled by default
  - no alert clearing
  - no mutation of catalog/render gates

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.

Read first:
- docs/CHATGPT_REVIEW.md
- README.md
- docs/PROJECT_STATE.md
- docs/NEXT_STEPS.md
- docs/PHASE_LOG.md
- docs/ARCHITECTURE.md
- docs/API_SPEC.md
- docs/RUNBOOK_REAL_MRMS_VALIDATION.md
- docs/VERIFIED_MRMS_CRITERIA.md
- docs/GRIB2_DECODE.md

Task: Implement Phase 64 only.

Goal: Add an explicitly disabled-by-default command scaffold for a future real MRMS rendering candidate attempt, with hard safety gates, dry-run-only default behavior, and no production tile serving.

Requirements (summary):
- Persist local scaffold JSON/Markdown under data/dev/ (gitignored)
- Expose read-only API/status and Dev Validation UI
- Keep verified_mrms false and production rendering gated
- Do not download/decode/render by default, clear alerts, or mutate catalog/render gates
- Update docs/CHATGPT_REVIEW.md before final commit/tag/push

Run make test, frontend tests, and frontend build before commit.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
5. `docs/RUNBOOK_REAL_MRMS_VALIDATION.md`
