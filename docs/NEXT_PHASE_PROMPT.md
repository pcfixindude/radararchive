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
* Completed through phase: 127
* Latest phase: Phase 127 — Import clip frame list sync
* Latest commit: (see CHATGPT_REVIEW.md)
* Latest tag: phase-127-import-clip-frame-list-sync
* Push status: see CHATGPT_REVIEW.md
Important direction:
This is for my own local use right now. I want meaningful, visible progress toward a usable historical radar replay app. Do not make this a tiny safety-wrapper phase. Keep the safety boundaries, but work aggressively inside the local-dev/prototype lane.
Implement the next phase only:
Phase 128 — Applied clip sequence position
Short name: applied-clip-sequence-position
Goal:
After applying an imported clip frame list, show current position within the clip sequence in replay UI (e.g. “Clip frame 4/26”) and warn when the selected frame is outside the applied sequence.
Current project state relevant to this phase:
* Phase 127 added clip frame list sync on apply (`clipImportTimes` in App.tsx, apply preview in Import clip panel)
* Phase 125 added clip manifest import replay (range/loop + readiness)
* Existing replay position UI: range position label in ReplayRangeControls, TimeSlider, PlaybackControls
Required implementation work:
1. Track applied clip frame sequence in replay state (clip id + ordered timestamps) separate from generic playback merge.
2. Show clip sequence position in Range & loop panel when an applied clip sequence is active (e.g. “Clip frame 4/26 · clip_…”).
3. Warn when selected frame is outside the applied clip sequence or not yet in catalog.
4. Clear clip sequence indicator when range is cleared or a new clip is applied.
5. Add frontend tests for position helpers and UI labels.
6. Update docs:
   * docs/CHATGPT_REVIEW.md
   * docs/PROJECT_STATE.md
   * docs/NEXT_STEPS.md
   * docs/PHASE_LOG.md
   * docs/NEXT_PHASE_PROMPT.md — write the next self-contained phase prompt when this phase completes
Things to avoid:
* Do not silently run real MRMS downloads
* Do not auto-execute warm/decode
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
make playback-export ARGS="--start 2026-06-28T13:00:00Z --end 2026-06-28T13:26:38Z --timestamps 2026-06-28T13:00:00Z,2026-06-28T13:26:38Z"
make clip-import ARGS="--file data/dev/playback_export_latest.json"
Git requirements:
Before committing:
* git status --short
* verify only intended files changed
* run all required checks
* do not stage data/dev runtime artifacts
Then:
* git add .
* git commit -m "phase 128: applied clip sequence position"
* git tag phase-128-applied-clip-sequence-position
* git push origin main --tags
End-of-phase requirements:
* update docs/CHATGPT_REVIEW.md with completion state, commit, tag, push status, safety state, and next recommended phase
* write the next ready-to-run phase prompt to docs/NEXT_PHASE_PROMPT.md
* include the standard end-of-phase report (summary, files changed, tests, git status, next phase)
