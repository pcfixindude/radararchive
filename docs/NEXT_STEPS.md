# Next Steps

## Phase 105 - Wire decoded preview into map overlay (Draft)

Goal: Display local decoded_prototype preview on the map shell (color scale / georef / tile slice) while production tile serving stays off.

```bash
make decode-retry
# then frontend work to overlay data/dev/mrms_local_render_preview/ or decoded tile endpoint
```

## Phase 104 verification commands

```bash
make test
make check-decoders
make install-decoders
make decode-grib2 ARGS="--latest-mrms"
make decode-retry
make mrms-local-render-pipeline
```

Local result after Phase 104:

- `decode_success`: true
- `decoder_used`: rasterio
- `decode_grid`: 7000 x 3500
- `pipeline_status`: `preview_ok`
- `render_mode`: `decoded_prototype`
- `produced_decoded_preview`: true
- Preview: `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
- Decode output: `data/staging/grib2_decode/20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638/`

Decoder install (Mac, project venv only):

```bash
make install-decoders
```

Note: `wgrib2` is not in default Homebrew; rasterio wheels are the preferred path documented in `requirements-optional-decoders.txt`.

## Phase 103 verification commands

```bash
make mrms-local-render-pipeline
```
