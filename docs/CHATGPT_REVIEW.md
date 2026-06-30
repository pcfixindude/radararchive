# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 103
- Latest phase: Phase 103 — Fast track local MRMS render pipeline
- Latest commit: (pending)
- Latest tag: `phase-103-fast-track-local-mrms-render-pipeline`
- Push status: (pending)
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Local render pipeline: prototype only — does not enable production serving or claim verified MRMS

## Latest phase summary

- Phase: **103**
- Purpose: Fast-track end-to-end local MRMS render path (candidate → inspect → decode → preview) without another gated review wrapper.
- Main command: `make mrms-local-render-pipeline`
- Service: `backend/app/services/mrms_local_render_pipeline.py`
- Local run result:
  - `pipeline_status`: **decoder_missing**
  - `render_attempt_status`: **preview_produced**
  - `produced_local_artifact`: **true** (placeholder preview PNG — not real radar imagery)
  - `render_mode`: `placeholder_decoder_missing`
  - `blocker`: **decoder_missing** — no wgrib2/GDAL/rasterio detected locally
  - Candidate used: `data/raw/mrms/reflectivity/20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638.grib2.gz` (real `.grib2.gz` on disk)
  - Preview output: `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
  - Report: `data/dev/mrms_local_render_pipeline_latest.json` / `.md`
- Did local rendering produce a real radar artifact? **No** — placeholder preview only because decoders are missing. A real GRIB2 candidate was selected; decode was skipped with a clear blocker message.
- Tests: backend 1154 passed

## Current focus

Local render pipeline path exists and documents failures actionably. Next step is a practical dependency/decode fix — **not** another gated review wrapper.

## Next recommended phase

- Phase number: **104**
- Phase title: Install wgrib2/GDAL and retry real MRMS decode for local preview
- Goal: Install decoder tooling (or rasterio/GDAL), run `make decode-grib2 ARGS='--latest-mrms'`, rerun `make mrms-local-render-pipeline`, and produce a **decoded_prototype** preview PNG from the existing real `.grib2.gz` candidate.
- Why this is next: Phase 103 found a real MRMS file locally and wrote a placeholder preview because no decoder is installed. The pipeline, report, and retry commands are ready; the blocker is environmental, not architectural.
- Safety boundaries:
  - local dev only
  - keep `verified_mrms` false
  - keep production tile serving off
  - no alert clearing
  - artifacts under `data/dev/` unless existing docs say otherwise

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 104 only.
Install or wire wgrib2/GDAL decode for the existing local MRMS candidate and rerun make mrms-local-render-pipeline until decoded_prototype preview is produced.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
