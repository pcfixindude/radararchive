# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 65
- Latest phase: Phase 65 — Gated candidate artifact sandbox layout
- Latest commit: `f241370`
- Latest tag: `phase-65-candidate-artifact-sandbox`
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
- Render candidate scaffold: disabled-by-default local scaffold; dry-run/no-op only; `scaffold_ready` is **not** production authorization
- Render candidate sandbox: local-only artifact layout under `data/dev/`; cleanup report-only by default; `ready` is **not** production authorization
- Scheduled visual review: explicit opt-in only via `--visual-review` or `make scheduled-proof-bundle-visual-review`

## Latest phase summary

- Phase: **65**
- Purpose: Add a local sandbox directory layout and cleanup/reporting workflow for future real MRMS candidate artifacts, isolated from production tile serving and disabled by default.
- Main command added: `make mrms-render-candidate-sandbox`
- API added: `GET/POST /api/validation/mrms-render-candidate/sandbox`
- Tests: backend 727 passed; frontend vitest 8 passed; frontend build succeeded
- Known limitations:
  - Sandbox is local-only under `data/dev/mrms_render_candidate_sandbox/`
  - Cleanup is report-only — no file deletion in Phase 65 even with `--confirm-delete-dev-sandbox`
  - Conservative blocking when sandbox path escapes `data/dev/` or overlaps production tile paths
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
- Render candidate command scaffold JSON/Markdown with Dev Validation scaffold UI
- Render candidate artifact sandbox layout/manifest/report with Dev Validation sandbox UI

## Current focus

The project is in the **local visual evidence review** block with gated preflight, dry-run planning, disabled-by-default scaffold, and local artifact sandbox before any real MRMS rendering candidate attempt.

The next major direction should add local import/export for candidate sandbox manifests and reports.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **66**
- Phase title: Gated candidate sandbox manifest import/export
- Goal: Add local import/export support for candidate sandbox manifests and reports so future candidate artifacts can be reviewed, archived, and compared without touching production tile serving or verifying MRMS.
- Why this is next: Phase 65 defines the isolated sandbox layout; Phase 66 should add manifest import/export for review/archive/compare workflows.
- Safety boundaries:
  - local-only import/export by default
  - no MRMS verification claim
  - no production rendering or tile serving
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

Task: Implement Phase 66 only.

Goal: Add local import/export support for candidate sandbox manifests and reports so future candidate artifacts can be reviewed, archived, and compared without touching production tile serving or verifying MRMS.

Requirements (summary):
- Persist local import/export JSON/Markdown under data/dev/ (gitignored)
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
