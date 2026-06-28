# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 59
- Latest phase: Phase 59 — Scheduled visual review workflow
- Latest commit: `5b7e90235f37931db00b711baccaf9ff5a2e6782`
- Latest tag: `phase-59-scheduled-visual-review-workflow`
- Push status: pushed to origin main with tag
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- External notifications: **none**
- MRMS visual review: local-only; does not download/decode MRMS; does not create tiles; does not verify MRMS
- Scheduled visual review: explicit opt-in only via `--visual-review` or `make scheduled-proof-bundle-visual-review`

## Latest phase summary

- Phase: **59**
- Purpose: Add optional scheduled visual review generation and improve visual review workflow presets.
- Main command added: `make scheduled-proof-bundle-visual-review`
- Scheduled validation flag added: `--visual-review`
- Tests: backend 626 passed; frontend vitest 8 passed; frontend build succeeded
- Known limitations:
  - Visual review remains advisory/local-only
  - Standalone `make mrms-visual-review` is faster when only visual review refresh is needed
  - Scheduled visual review is explicit opt-in
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

## Current focus

The project is in the **local visual evidence review** block.

The next major direction should improve confidence in visual artifacts, then prepare a carefully gated real MRMS rendering candidate path.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **60**
- Phase title: Visual review artifact drilldown and sample-set selection
- Goal: Let operators choose a small local sample set of visual review frames/artifacts for closer manual inspection without enabling production rendering.
- Why this is next: Phases 56–59 created visual review generation, comparison, stale hints, recommendations, and scheduled tie-ins. The next useful step is to make visual artifacts easier to inspect and organize into a candidate sample set.
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

Task: Implement Phase 60 only.

Goal: Add local visual review sample-set selection so operators can pick a small set of frames/artifacts for closer manual inspection.

Requirements (summary):
- Persist local sample-set JSON/Markdown under data/dev/ (gitignored)
- Expose read-only API/status and Dev Validation UI
- Keep verified_mrms false and production rendering gated
- Do not download/decode MRMS, clear alerts, or mutate catalog/render gates
- Update docs/CHATGPT_REVIEW.md before final commit/tag/push

Run make test, frontend tests, and frontend build before commit.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PHASE_WORKFLOW_RULES.md`
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_STEPS.md`
5. `docs/RUNBOOK_REAL_MRMS_VALIDATION.md`
