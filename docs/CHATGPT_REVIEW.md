# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 104
- Latest phase: Phase 104 — Install decoders and retry MRMS decode
- Latest commit: (pending)
- Latest tag: `phase-104-install-decoders-and-retry-mrms-decode`
- Push status: (pending)
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Local decoded preview: prototype only — not verified MRMS, not production tile serving

## Latest phase summary

- Phase: **104**
- Purpose: Install/wire optional decoder tooling, decode real local MRMS candidate, produce decoded_prototype preview PNG.
- Commands added:
  - `make check-decoders` — report wgrib2/GDAL/rasterio status
  - `make install-decoders` — pip install `requirements-optional-decoders.txt` into `.venv`
  - `make decode-retry` — decode latest MRMS + rerun local render pipeline
- Real decode succeeded? **Yes** — `rasterio` decoder, grid **7000 x 3500**, value range -999 .. 64.5 dBZ (prototype normalized)
- Decoded prototype preview produced? **Yes**
  - `render_mode`: `decoded_prototype`
  - `pipeline_status`: `preview_ok`
  - `decode_retry_status`: `preview_ok`
- Tooling status (local Mac):
  - **rasterio**: installed in project `.venv` (`pip install -r requirements-optional-decoders.txt`)
  - **wgrib2**: not installed (not in default Homebrew formulae)
  - **gdal (python)**: not detected
  - **pygrib / cfgrib**: not installed
- Output paths:
  - Decode artifact: `data/staging/grib2_decode/20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638/`
  - Manifest: `.../decode_manifest.json`, raster: `.../normalized.tif`
  - Preview PNG: `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
  - Reports: `data/dev/decode_retry_latest.json`, `data/dev/decoder_setup_latest.json`, `data/dev/mrms_local_render_pipeline_latest.json`
- Candidate: `data/raw/mrms/reflectivity/20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638.grib2.gz`
- Tests: backend 1160 passed

## Current focus

Local decode + decoded_prototype preview works. Next: wire preview into map overlay or improve color scale/georef/tile slicing — **not** another gated wrapper.

## Next recommended phase

- Phase number: **105**
- Phase title: Wire decoded preview into map overlay (local dev)
- Goal: Show the decoded_prototype preview on the local map (color scale, basic georef or tile slice) while keeping production tile serving off and `verified_mrms` false.
- Why this is next: Phase 104 produced a real decoded grid and local preview PNG; the gap is visual integration on the frontend map shell.
- Safety boundaries:
  - local dev / prototype only
  - keep `ENABLE_PRODUCTION_RADAR_TILES` false
  - no verified MRMS claim
  - no alert clearing

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 105 only.
Wire the local decoded_prototype preview into the map overlay for local dev.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
