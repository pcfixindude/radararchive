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
* Completed through phase: 126
* Latest phase: Phase 126 — Imported clip batch remediation plan
* Latest commit: (see CHATGPT_REVIEW.md)
* Latest tag: phase-126-imported-clip-batch-remediation
* Push status: see CHATGPT_REVIEW.md
Important direction:
This is for my own local use right now. I want meaningful, visible progress toward a usable historical radar replay app. Do not make this a tiny safety-wrapper phase. Keep the safety boundaries, but work aggressively inside the local-dev/prototype lane.
Implement the next phase only:
Phase 127 — Import clip frame list sync
Short name: import-clip-frame-list-sync
Goal:
When applying an imported clip, sync the playback timestamp list from manifest frames (not just range endpoints) so replay matches the exported clip frame sequence.
Current project state relevant to this phase:
* Phase 126 added bounded remediation plan from import problem frames (API, CLI, UI)
* Phase 125 added clip manifest import replay (apply range/loop only today)
* Phase 123 added playback export clip with per-frame list in manifest
* Existing apply flow: `ClipImportPanel` → `buildApplyPayload` → range start/end + loop suggestion
Required implementation work:
1. Extend clip apply payload to include manifest frame timestamps (bounded, same max as export).
2. Wire apply handler in replay UI to set playback timestamp list from imported frames when present.
3. Show apply preview: “Will restore N frames” vs range-only fallback.
4. Add/update backend tests if apply validation helpers added; frontend tests for apply payload and UI preview.
5. Update docs:
   * docs/CHATGPT_REVIEW.md
   * docs/PROJECT_STATE.md
   * docs/NEXT_STEPS.md
   * docs/PHASE_LOG.md
   * docs/NEXT_PHASE_PROMPT.md — write the next self-contained phase prompt when this phase completes
Things to avoid:
* Do not silently run real MRMS downloads
* Do not auto-execute warm/decode from apply
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
* git commit -m "phase 127: import clip frame list sync"
* git tag phase-127-import-clip-frame-list-sync
* git push origin main --tags
End-of-phase requirements:
* update docs/CHATGPT_REVIEW.md with completion state, commit, tag, push status, safety state, and next recommended phase
* write the next ready-to-run phase prompt to docs/NEXT_PHASE_PROMPT.md
* include the standard end-of-phase report (summary, files changed, tests, git status, next phase)
