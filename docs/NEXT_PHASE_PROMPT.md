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
* Completed through phase: 122
* Latest phase: Phase 122 — Frame catalog browser
* Latest commit: (see CHATGPT_REVIEW.md)
* Latest tag: phase-122-frame-catalog-browser
* Push status: see CHATGPT_REVIEW.md
Important direction:
This is for my own local use right now. I want meaningful, visible progress toward a usable historical radar replay app. Do not make this a tiny safety-wrapper phase. Keep the safety boundaries, but work aggressively inside the local-dev/prototype lane.
Implement the next phase only:
Phase 123 — Playback export clip
Short name: playback-export-clip
Goal:
Export the active replay range (start/end frames) as a bounded local clip manifest the operator can save or share — frame list, timestamps, cache/decode status, and optional preview paths — without running new ingest or decode in the request.
Current project state relevant to this phase:
* Phase 122 added frame catalog browser with jump-to-frame
* Phase 121 added one-shot local replay setup
* Phase 118 added playback range and loop
* Phase 117 added replay session workflow
* Existing APIs/services to reuse where possible:
  * `build_frame_catalog` / frame cache status
  * replay range state from frontend hooks
  * decode preview paths from frame cache manifests
Required implementation work:
1. Add a dev-oriented export API if needed, e.g. `GET /api/dev/playback-export` accepting range timestamps and returning a clip manifest — status/plan only, no long-running work.
2. Add optional CLI `make playback-export` writing manifest JSON under `data/dev/` (gitignored).
3. Add **Export clip** action in replay UI (range & loop or replay session panel):
   * requires complete start/end range
   * shows clip summary (frame count, cache/decode counts)
   * copy manifest JSON or download locally
4. Add/update tests for backend manifest payload and frontend export UX.
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
make local-replay-ready
Git requirements:
Before committing:
* git status --short
* verify only intended files changed
* run all required checks
* do not stage data/dev runtime artifacts
Then:
* git add .
* git commit -m "phase 123: playback export clip"
* git tag phase-123-playback-export-clip
* git push origin main --tags
End-of-phase requirements:
* update docs/CHATGPT_REVIEW.md with completion state, commit, tag, push status, safety state, and next recommended phase
* write the next ready-to-run phase prompt to docs/NEXT_PHASE_PROMPT.md
* include the standard end-of-phase report (summary, files changed, tests, git status, next phase)
