# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 61
- Latest phase: Phase 61 — Visual sample-set review annotations and candidate readiness scoring
- Latest commit: `d90e939`
- Latest tag: `phase-61-visual-sample-readiness`
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
- Scheduled visual review: explicit opt-in only via `--visual-review` or `make scheduled-proof-bundle-visual-review`

## Latest phase summary

- Phase: **61**
- Purpose: Add local operator annotations and conservative candidate readiness scoring for visual review sample sets.
- Main command added: `make mrms-visual-review-readiness`
- API added: `GET/POST /api/validation/mrms-visual-review/sample-set/readiness`, `POST /api/validation/mrms-visual-review/sample-set/annotations`
- Tests: backend 656 passed; frontend vitest 8 passed; frontend build succeeded
- Known limitations:
  - Readiness scoring is advisory/local-only — does not verify MRMS or authorize production rendering
  - Conservative scoring blocks `candidate_ready` when any sample is rejected, missing artifacts, stale, unreviewed, questionable, or tagged for follow-up
  - Requires an existing sample set from Phase 60 before annotations apply
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

## Current focus

The project is in the **local visual evidence review** block.

The next major direction should evaluate a strictly gated real MRMS rendering candidate preflight without enabling production rendering or verifying MRMS.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **62**
- Phase title: Gated real MRMS rendering candidate preflight
- Goal: Add a strictly gated local preflight checklist that evaluates whether the project is ready to attempt a real MRMS rendering candidate path, without enabling production rendering or verifying MRMS.
- Why this is next: Phase 61 adds operator annotations and conservative sample-set readiness scoring; Phase 62 should assemble a broader gated preflight before any real MRMS rendering candidate attempt.
- Safety boundaries:
  - local-only
  - no MRMS verification claim
  - no production rendering
  - no new download/decode unless explicitly scoped and gated in the preflight design
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

Task: Implement Phase 62 only.

Goal: Add a strictly gated local preflight checklist that evaluates whether the project is ready to attempt a real MRMS rendering candidate path, without enabling production rendering or verifying MRMS.

Requirements (summary):
- Persist local preflight JSON/Markdown under data/dev/ (gitignored)
- Expose read-only API/status and Dev Validation UI
- Keep verified_mrms false and production rendering gated
- Do not download/decode MRMS, clear alerts, or mutate catalog/render gates unless explicitly scoped as advisory checks only
- Update docs/CHATGPT_REVIEW.md before final commit/tag/push

Run make test, frontend tests, and frontend build before commit.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
5. `docs/RUNBOOK_REAL_MRMS_VALIDATION.md`
