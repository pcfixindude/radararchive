# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 66
- Latest phase: Phase 66 — Gated candidate sandbox manifest import/export
- Latest commit: `95e6f04`
- Latest tag: `phase-66-sandbox-manifest-import-export`
- Push status: pushed to origin main with tag
- Final git status: source clean; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- External notifications: **none**
- Render candidate sandbox import/export: local metadata/report-only; no binary artifacts by default; `imported` is **not** production authorization
- Render candidate sandbox: local-only artifact layout under `data/dev/`; cleanup report-only by default
- Render candidate scaffold: disabled-by-default local scaffold; dry-run/no-op only
- Scheduled visual review: explicit opt-in only via `--visual-review` or `make scheduled-proof-bundle-visual-review`

## Latest phase summary

- Phase: **66**
- Purpose: Add local import/export support for candidate sandbox manifests and reports for review/archive/compare without touching production tile serving.
- Main commands added: `make mrms-render-candidate-sandbox-export`, `make mrms-render-candidate-sandbox-import-export`
- API added: `GET /api/validation/mrms-render-candidate/sandbox/import-export`, `POST .../export`, `POST .../import`
- Tests: backend 751 passed; frontend vitest 8 passed; frontend build succeeded
- Known limitations:
  - Import/export is metadata/report-only — no binary artifacts, no production tile paths
  - Conservative blocking on verified_mrms claims, production rendering claims, path traversal, or paths outside `data/dev/`
  - Advisory comparison between current sandbox manifest and imported manifest
  - `verified_mrms` remains false

## Current focus

The project is in the **local visual evidence review** block with gated preflight, dry-run planning, disabled-by-default scaffold, local artifact sandbox, and manifest import/export before any real MRMS rendering candidate attempt.

The next major direction should add comparison history for sandbox exports/imports.

Do **not** promote to verified MRMS yet.

## Next recommended phase

- Phase number: **67**
- Phase title: Gated candidate sandbox manifest comparison history
- Goal: Add local comparison history for candidate sandbox exports/imports so operators can review changes across candidate artifact reports without touching production tile serving or verifying MRMS.
- Why this is next: Phase 66 adds manifest import/export; Phase 67 should persist comparison history across exports/imports for operator review.
- Safety boundaries:
  - local-only comparison history by default
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

Task: Implement Phase 67 only.

Goal: Add local comparison history for candidate sandbox exports/imports so operators can review changes across candidate artifact reports without touching production tile serving or verifying MRMS.

Requirements (summary):
- Persist local comparison history JSON/Markdown under data/dev/ (gitignored)
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
