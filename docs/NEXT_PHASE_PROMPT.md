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
* Completed through phase: 124
* Latest phase: Phase 124 — Frame quality drill-down
* Latest commit: (see CHATGPT_REVIEW.md)
* Latest tag: phase-124-frame-quality-drilldown
* Push status: see CHATGPT_REVIEW.md
Important direction:
This is for my own local use right now. I want meaningful, visible progress toward a usable historical radar replay app. Do not make this a tiny safety-wrapper phase. Keep the safety boundaries, but work aggressively inside the local-dev/prototype lane.
Implement the next phase only:
Phase 125 — Clip manifest import replay
Short name: clip-manifest-import-replay
Goal:
Load a saved playback clip JSON (from Phase 123 export) to restore replay range, loop suggestion, and frame list in the replay UI — with clip-level readiness summary and batch remediation hints — without running ingest or decode.
Current project state relevant to this phase:
* Phase 124 added frame quality drill-down (API, CLI, UI)
* Phase 123 added playback export clip (API, CLI, UI)
* Phase 122 added frame catalog browser with jump-to-frame
* Existing APIs/services to reuse where possible:
  * `build_playback_export` / clip manifest schema
  * `build_frame_quality_report` for batch readiness
  * replay range/loop state in frontend (`useReplayRange`)
Required implementation work:
1. Add clip import validation helper (backend or shared) if needed, e.g. parse/validate exported clip JSON shape.
2. Add optional CLI `make clip-import` to validate a manifest file and print readiness summary (writes report under `data/dev/`, gitignored).
3. Add **Import clip** in Range & loop panel:
   * paste JSON or upload file from Phase 123 export
   * restore range start/end and loop suggestion
   * show clip readiness summary (cache/decode counts, cold/missing frames)
   * link to frame detail inspect for problem frames
4. Add/update tests for import validation and frontend import UX.
5. Update docs:
   * docs/CHATGPT_REVIEW.md
   * docs/PROJECT_STATE.md
   * docs/NEXT_STEPS.md
   * docs/PHASE_LOG.md
   * docs/NEXT_PHASE_PROMPT.md — write the next self-contained phase prompt when this phase completes
Things to avoid:
* Do not silently run real MRMS downloads
* Do not add unbounded ingest
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
make playback-export ARGS="--start ... --end ..."
make frame-quality ARGS="--timestamps ..."
Git requirements:
Before committing:
* git status --short
* verify only intended files changed
* run all required checks
* do not stage data/dev runtime artifacts
Then:
* git add .
* git commit -m "phase 125: clip manifest import replay"
* git tag phase-125-clip-manifest-import-replay
* git push origin main --tags
End-of-phase requirements:
* update docs/CHATGPT_REVIEW.md with completion state, commit, tag, push status, safety state, and next recommended phase
* write the next ready-to-run phase prompt to docs/NEXT_PHASE_PROMPT.md
* include the standard end-of-phase report (summary, files changed, tests, git status, next phase)
