You are working in the RadarArchive repo.
Project:
* Repo: pcfixindude/radararchive
* Local path: ~/Projects/radararchive
Required docs to read first:
1. docs/CHATGPT_REVIEW.md
2. docs/CURSOR_RULES.md
3. docs/PHASE_WORKFLOW_RULES.md
4. docs/PROJECT_STATE.md
5. docs/NEXT_STEPS.md
6. docs/PHASE_LOG.md
7. README.md
8. docs/API_SPEC.md, if API schemas or endpoint contracts are touched
9. docs/ARCHITECTURE.md, only if architecture changes
Current completed phase and latest commit/tag/push status from docs/CHATGPT_REVIEW.md:
* Completed through phase: 125
* Latest phase: Phase 125 — Clip manifest import replay
* Latest commit: (see CHATGPT_REVIEW.md)
* Latest tag: phase-125-clip-manifest-import-replay
* Push status: see CHATGPT_REVIEW.md
Important direction:
This is for my own local use right now. I want meaningful, visible progress toward a usable historical radar replay app. Do not make this a tiny safety-wrapper phase. Keep the safety boundaries, but work aggressively inside the local-dev/prototype lane.
Implement the next phase only:
Phase 126 — Imported clip batch remediation plan
Short name: imported-clip-batch-remediation
Goal:
From imported clip problem frames, generate a bounded warm/decode command plan (copy-ready checklist) in the replay UI and CLI — without auto-running ingest, decode, or real MRMS downloads.
Current project state relevant to this phase:
* Phase 125 added clip manifest import replay (API, CLI, UI)
* Phase 124 added frame quality drill-down with per-frame suggested_commands
* Phase 123 added playback export clip
* Existing APIs/services to reuse where possible:
  * `build_clip_import_report` / problem_frames / suggested_commands
  * `build_frame_quality_report` for per-frame remediation detail
  * `make mrms-warm-frame-cache`, `make decode-grib2`, ingest window presets
Required implementation work:
1. Add remediation plan builder (backend) that groups problem frames by readiness type and emits bounded copy-ready commands (max N frames).
2. Add optional CLI `make clip-remediation` reading clip import report or manifest file; writes plan under `data/dev/` (gitignored).
3. Add **Remediation plan** section in Import clip panel (or adjacent):
   * show grouped problem summary (cold/missing/failed counts)
   * copy-ready command block for bounded warm/decode steps
   * explicit note that commands are not auto-run
4. Add/update tests for plan builder and frontend remediation UX.
5. Update docs:
   * docs/CHATGPT_REVIEW.md
   * docs/PROJECT_STATE.md
   * docs/NEXT_STEPS.md
   * docs/PHASE_LOG.md
   * docs/NEXT_PHASE_PROMPT.md — write the next self-contained phase prompt when this phase completes
Things to avoid:
* Do not silently run real MRMS downloads
* Do not add unbounded ingest or auto-execute warm/decode from UI
* Do not add cloud workers, auth, billing, alerts, or new weather layers
* Do not mutate catalog/render gates or claim verified MRMS
* Do not commit generated data/dev artifacts
Hard safety boundaries:
* keep verified_mrms false
* keep ENABLE_PRODUCTION_RADAR_TILES false by default
* placeholder tiles remain default
* decoded tiles remain local-dev/prototype only
Tests:
Run:
make test
If frontend is touched, also run:
cd frontend && npm test
cd frontend && npm run build
Phase-relevant local run commands:
make backend
make frontend
make clip-import ARGS="--file data/dev/playback_export_latest.json"
make frame-quality ARGS="--timestamps ..."
Git requirements:
Before committing:
* git status --short
* verify only intended files changed
* run all required checks
* do not stage data/dev runtime artifacts
Then:
* git add .
* git commit -m "phase 126: imported clip batch remediation plan"
* git tag phase-126-imported-clip-batch-remediation
* git push origin main --tags
End-of-phase requirements:
* update docs/CHATGPT_REVIEW.md with completion state, commit, tag, push status, safety state, and next recommended phase
* write the next ready-to-run phase prompt to docs/NEXT_PHASE_PROMPT.md
* include the standard end-of-phase report (summary, files changed, tests, git status, next phase)
