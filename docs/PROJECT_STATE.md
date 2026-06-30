# Project State

Current phase: Phase 103 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Local render pipeline** — fast-track candidate → inspect → decode → preview path with local report under `data/dev/`
- **Validation remediation** — classifies stub-mode validation/proof failures; documents for preflight without clearing alerts
- **Preflight**: `candidate_preflight_ready` (stub-mode documented; not verified MRMS)
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 103)

```bash
make mrms-local-render-pipeline
make decode-grib2 ARGS="--latest-mrms"
make build-tile-cache
```

Artifacts:

- `data/dev/mrms_local_render_pipeline_latest.json`
- `data/dev/mrms_local_render_pipeline_latest.md`
- `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`

Local Phase 103 result: real `.grib2.gz` candidate selected; **decoder_missing**; placeholder preview PNG produced (not real radar imagery).

## Prior operator commands (Phase 102)

```bash
make mrms-remediate-validation ARGS="--refresh"
make mrms-resolve-preflight-attention ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```

Validation alert remains `failed` by design — stub-mode limitations documented for preflight path only.

## Verified MRMS

`verified_mrms` is **false** everywhere.
