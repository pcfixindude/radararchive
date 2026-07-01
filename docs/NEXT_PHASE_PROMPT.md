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
* Completed through phase: 121
* Latest phase: Phase 121 — One-shot local replay setup
* Latest commit: 547216f
* Latest tag: phase-121-one-shot-local-replay-setup
* Push status: pushed to origin/main with tag
Important direction:
This is for my own local use right now. I want meaningful, visible progress toward a usable historical radar replay app. Do not make this a tiny safety-wrapper phase. Keep the safety boundaries, but work aggressively inside the local-dev/prototype lane.
Implement the next phase only:
Phase 122 — Frame catalog browser
Short name: frame-catalog-browser
Goal:
Add a local frame catalog browser in the replay UI so the operator can see available MRMS frames with cache/decode readiness and jump directly to a frame without hunting on the time slider alone.
Current project state relevant to this phase:
* Phase 121 added one-shot local replay setup (`make local-replay-ready`, `GET /api/dev/local-replay-ready`, replay session checklist)
* Phase 120 added saved replay bookmarks
* Phase 119 added ingest date window UX
* Phase 118 added playback range and loop
* Phase 117 added replay session workflow
* Existing APIs/services to reuse where possible:
  * layer timestamps from catalog routes
  * `build_playback_cache_status` / dev overlay cache status
  * decode retry / frame quality artifacts if already exposed
  * `local_replay_ready` frame selection patterns
Required implementation work:
1. Add a dev-oriented frame catalog status API if needed, e.g. `GET /api/dev/frame-catalog` returning local frames with cache/decode flags and counts — status/plan only, no long-running work in the request.
2. Add a **Frame catalog** panel (or section) in the replay UI:
   * list local frames for the active layer/window
   * show cache ready / decode ready / missing indicators
   * click or button to jump playback to that frame
   * compact sort/filter (newest first; optional text filter on timestamp)
3. Wire jump-to-frame into existing playback state (selected frame, slider, range highlights unchanged unless helpful).
4. Add/update tests for backend catalog payload and frontend list/jump behavior.
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
* git commit -m "phase 122: frame catalog browser"
* git tag phase-122-frame-catalog-browser
* git push origin main --tags
End-of-phase requirements:
* update docs/CHATGPT_REVIEW.md with completion state, commit, tag, push status, safety state, and next recommended phase
* write the next ready-to-run phase prompt to docs/NEXT_PHASE_PROMPT.md
* include the standard end-of-phase report (summary, files changed, tests, git status, next phase)
