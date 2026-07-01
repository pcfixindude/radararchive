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
* Completed through phase: 123
* Latest phase: Phase 123 — Playback export clip
* Latest commit: (see CHATGPT_REVIEW.md)
* Latest tag: phase-123-playback-export-clip
* Push status: see CHATGPT_REVIEW.md
Important direction:
This is for my own local use right now. I want meaningful, visible progress toward a usable historical radar replay app. Do not make this a tiny safety-wrapper phase. Keep the safety boundaries, but work aggressively inside the local-dev/prototype lane.
Implement the next phase only:
Phase 124 — Frame quality drill-down
Short name: frame-quality-drilldown
Goal:
Show per-frame quality/readiness detail in the replay UI for a selected catalog or clip frame — decode status, cache path hints, preview availability, and suggested remediation commands — without running new ingest or decode in the request.
Current project state relevant to this phase:
* Phase 123 added playback export clip (API, CLI, UI)
* Phase 122 added frame catalog browser with jump-to-frame
* Phase 121 added one-shot local replay setup
* Existing APIs/services to reuse where possible:
  * `build_frame_catalog` / frame cache manifests
  * `frame_quality.py` or similar quality helpers if present
  * decode retry / local render pipeline suggested commands
Required implementation work:
1. Add or extend a dev-oriented quality API if needed, e.g. `GET /api/dev/frame-quality` for one or more timestamps — status/plan only.
2. Add optional CLI `make frame-quality` writing report JSON under `data/dev/` (gitignored).
3. Add **Frame detail** drill-down in replay UI (frame catalog or export summary):
   * select a frame to inspect
   * show decode/cache/quality breakdown
   * show suggested next commands for cold/missing/failed frames
4. Add/update tests for backend quality payload and frontend drill-down UX.
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
Git requirements:
Before committing:
* git status --short
* verify only intended files changed
* run all required checks
* do not stage data/dev runtime artifacts
Then:
* git add .
* git commit -m "phase 124: frame quality drill-down"
* git tag phase-124-frame-quality-drilldown
* git push origin main --tags
End-of-phase requirements:
* update docs/CHATGPT_REVIEW.md with completion state, commit, tag, push status, safety state, and next recommended phase
* write the next ready-to-run phase prompt to docs/NEXT_PHASE_PROMPT.md
* include the standard end-of-phase report (summary, files changed, tests, git status, next phase)
