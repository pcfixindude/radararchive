# Cursor Rules

## Phase workflow

All phase implementation work must follow [PHASE_WORKFLOW_RULES.md](PHASE_WORKFLOW_RULES.md) in addition to the rules below.

## Development Rules
1. Work in small phases.
2. Do not rewrite the whole project unless explicitly asked.
3. Keep API, worker, storage, and frontend concerns separated.
4. Do not put radar collection inside request/response API routes.
5. Use UTC internally for all timestamps.
6. Keep raw source data immutable.
7. Processed data may be regenerated.
8. Add or update tests for every backend change.
9. Update docs/PHASE_LOG.md, docs/NEXT_STEPS.md, docs/PROJECT_STATE.md, docs/CHATGPT_REVIEW.md, and docs/NEXT_PHASE_PROMPT.md after each phase (see [PHASE_WORKFLOW_RULES.md](PHASE_WORKFLOW_RULES.md)).
10. Keep secrets out of git.
11. Do not scrape commercial weather sites.
12. Add NOAA/NWS attribution/disclaimer where public data is displayed.
13. Prefer simple working vertical slices over broad unfinished features.
14. Use typed models/schemas.
15. Use clear filenames and avoid giant files.
16. If something is stubbed, label it clearly as stubbed.
17. Keep local development working without cloud credentials.
18. Do not introduce a paid service dependency without documenting why.
19. Before changing architecture, update docs/ARCHITECTURE.md.
20. Every phase must end with exact run/test commands.

## Git requirements (all phases)

See [PHASE_WORKFLOW_RULES.md](PHASE_WORKFLOW_RULES.md) for the full Git, testing, and completion-report checklist. Summary:

1. Run `git status --short` and verify only intended phase files changed.
2. Update `docs/CHATGPT_REVIEW.md` before final commit/tag/push.
3. Write the next self-contained phase prompt to `docs/NEXT_PHASE_PROMPT.md`.
4. Stage and commit: `git add .` then `git commit -m "phase XX: short description"`.
5. Tag: `git tag phase-XX-short-name`.
6. Push: `git push origin main --tags`.

Do **not** commit or push if:

- Any required test/build command fails.
- Unexpected unrelated files are in the working tree.

The phase completion response must include: commit hash, tag name, push result, and final `git status --short`.

## Initial MVP
Build:
- FastAPI health endpoint
- layer list endpoint
- fake/demo radar timestamps
- frontend map shell
- time slider
- layer panel
- PWA manifest

Do not build yet:
- Stripe
- native Android
- HRRR
- storm tracking
- full GRIB2 processing
