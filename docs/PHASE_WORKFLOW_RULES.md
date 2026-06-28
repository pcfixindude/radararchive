# Phase Workflow Rules

Standing instructions for RadarArchive phase work. Future phase prompts should reference this file instead of repeating the full rule set.

See also: [CURSOR_RULES.md](CURSOR_RULES.md), [PROJECT_STATE.md](PROJECT_STATE.md), [NEXT_STEPS.md](NEXT_STEPS.md).

## Scope

- Implement **only** the requested phase.
- Do not rewrite unrelated subsystems or redo completed phases unless explicitly asked.
- Preserve existing API contracts unless the phase explicitly changes them.

## Tiles and production rendering

- **Placeholder tiles remain the default** map behavior.
- Keep `ENABLE_PRODUCTION_RADAR_TILES=false` by default.
- Do **not** enable production rendering by default.
- Production tiles require the feature flag **plus** catalog gates **plus** cached tiles.
- Do **not** mutate production/catalog/render gates unless the phase explicitly requires it.

## Verified MRMS

- **`verified_mrms` must remain `false`** everywhere unless a future phase explicitly authorizes verified MRMS promotion.
- Do **not** claim real MRMS tiles are verified production output.
- Local validation, digest, handoff, review sessions, and sign-offs are **supporting review evidence only** — not verification.

## Validation and alerts

- Do **not** clear validation alerts silently.
- Operator acknowledgments, digests, and review sessions do **not** clear alerts unless a phase explicitly documents otherwise.

## Out of scope (unless explicitly requested)

Do **not** add:

- Stripe or billing
- Real auth / JWT
- HRRR, WPC, or new weather layers
- Native Android
- Cloud deployment infrastructure
- Redis / Celery
- Mandatory GDAL / rasterio / wgrib2 dependency
- External notifications: email, SMS, Slack, webhooks, push notifications

## Testing and dependencies

- Add or update tests for every backend change in the phase.
- Tests must **not** depend on live internet.
- Tests must **not** require GDAL / rasterio / wgrib2 unless the phase explicitly adds optional integration.
- Run `make test` and `cd frontend && npm run build` before committing.
- Run phase-relevant Makefile targets listed in the phase prompt.

## Runtime artifacts and Git

Generated local artifacts under `data/dev/` (proof bundles, diffs, digests, handoff, escalation, acknowledgment, review sessions, scheduled reports, etc.) must:

- Remain listed in `.gitignore`
- **Not** be committed or staged accidentally

Before commit:

1. Run `git status --short` and verify only intended phase files changed.
2. Do **not** commit if unexpected unrelated files are in the working tree.
3. Do **not** commit or push if any required test or build command fails.

## Git workflow (after checks pass)

```bash
git status --short
git add .
git commit -m "phase XX: short description"
git tag phase-XX-short-name
git push origin main --tags
```

## Documentation (each phase)

Update as applicable:

- `docs/PHASE_LOG.md` — what changed in this phase
- `docs/PROJECT_STATE.md` — current status
- `docs/NEXT_STEPS.md` — next recommended phase
- `docs/ARCHITECTURE.md` — if architecture changed
- `docs/API_SPEC.md` — if API/summary response changed
- `docs/RUNBOOK_REAL_MRMS_VALIDATION.md` — if operator commands changed
- `docs/VERIFIED_MRMS_CRITERIA.md` — if review/verification boundaries changed
- `README.md` — command examples and links

## Phase completion report

End every phase with:

1. Phase purpose
2. Files changed
3. What changed
4. Commands run
5. Test results
6. Feature-specific behavior (as listed in the phase prompt)
7. Git ignore / runtime artifact behavior
8. Tile/render mode behavior (placeholders default, production disabled, `verified_mrms` false)
9. Known limitations
10. Next recommended phase
11. Commit hash
12. Tag name
13. Push result
14. Final `git status --short`

## Read-first docs (typical phase)

Before implementing a phase, read:

- `README.md`
- `docs/CURSOR_RULES.md`
- `docs/PHASE_WORKFLOW_RULES.md` (this file)
- `docs/PROJECT_STATE.md`
- `docs/NEXT_STEPS.md`
- `docs/PHASE_LOG.md`
- `docs/ARCHITECTURE.md`
- `docs/API_SPEC.md`
- `docs/RUNBOOK_REAL_MRMS_VALIDATION.md`
- `docs/VERIFIED_MRMS_CRITERIA.md`
- Phase-specific docs referenced in the prompt (e.g. `docs/GRIB2_DECODE.md`)
