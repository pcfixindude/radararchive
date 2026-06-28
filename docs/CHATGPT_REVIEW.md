# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 60
- Latest phase: Phase 60 — Visual review artifact drilldown and sample-set selection
- Latest commit: (see git log after push)
- Latest tag: `phase-60-visual-review-sample-sets`
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
- Scheduled visual review: explicit opt-in only via `--visual-review` or `make scheduled-proof-bundle-visual-review`

## Latest phase summary

- Phase: **60**
- Purpose: Add local visual review sample-set selection for closer manual inspection of a small artifact subset.
- Main command added: `make mrms-visual-review-sample-set`
- API added: `GET/POST /api/validation/mrms-visual-review/sample-set`
- Tests: backend 639 passed; frontend vitest 8 passed; frontend build succeeded
- Known limitations:
  - Sample set is advisory/local-only drilldown evidence
  - Requires an existing visual review manifest (`make mrms-visual-review`) for non-empty selection
  - Recommended selection prioritizes missing artifacts and diverse tile modes — not a verification gate
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
- Visual review sample-set JSON/Markdown under `data/dev/` with Dev Validation drilldown UI

## Current focus

The project is in the **local visual evidence review** block.

The next major direction should improve confidence in visual artifacts, then prepare a carefully gated real MRMS rendering candidate path.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **61**
- Phase title: Visual sample-set review annotations and candidate readiness scoring
- Goal: Allow operators to add local notes/status to selected visual review samples and summarize whether the sample set is ready for a later gated real MRMS rendering candidate path.
- Why this is next: Phase 60 organizes a small drilldown sample set; Phase 61 adds operator annotations and a local readiness summary before any gated rendering candidate workflow.
- Safety boundaries:
  - local-only
  - no MRMS verification claim
  - no production rendering
  - no new download/decode
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

Task: Implement Phase 61 only.

Goal: Allow operators to add local notes/status to selected visual review samples and summarize whether the sample set is ready for a later gated real MRMS rendering candidate path.

Requirements (summary):
- Persist local annotation/readiness JSON/Markdown under data/dev/ (gitignored)
- Expose read-only API/status and Dev Validation UI for annotations and readiness summary
- Keep verified_mrms false and production rendering gated
- Do not download/decode MRMS, clear alerts, or mutate catalog/render gates
- Update docs/CHATGPT_REVIEW.md before final commit/tag/push

Run make test, frontend tests, and frontend build before commit.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
5. `docs/RUNBOOK_REAL_MRMS_VALIDATION.md`
