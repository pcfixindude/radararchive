# Next Steps

## Phase 104 - Install wgrib2/GDAL and retry real MRMS decode (Draft)

Goal: Unblock local decoded preview for the existing real `.grib2.gz` candidate found in Phase 103.

```bash
# install decoder tooling (example)
brew install wgrib2
# or install rasterio/GDAL in the venv

make decode-grib2 ARGS="--latest-mrms"
make mrms-local-render-pipeline
```

Success criteria:

- `pipeline_status`: `preview_ok`
- `render_mode`: `decoded_prototype`
- Preview at `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png` from decoded grid (still not verified MRMS / not production)

## Phase 103 verification commands

```bash
make test
make mrms-local-render-pipeline
```

Local result after Phase 103 local render pipeline:

- `pipeline_status`: `decoder_missing`
- `render_attempt_status`: `preview_produced`
- `produced_local_artifact`: true (placeholder — decoder missing)
- `blocker`: `decoder_missing`
- Candidate: `data/raw/mrms/reflectivity/20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638.grib2.gz`
- Preview: `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`

Retry sequence when decoders are installed:

```bash
make decode-grib2 ARGS="--latest-mrms"
make mrms-local-render-pipeline
make build-tile-cache
```

## Phase 102 verification commands

```bash
make mrms-remediate-validation ARGS="--refresh"
make mrms-resolve-preflight-attention ARGS="--refresh"
make operator-review-status ARGS="--refresh"
make mrms-render-candidate-preflight ARGS="--refresh"
make mrms-readiness-milestone-audit ARGS="--refresh"
```
