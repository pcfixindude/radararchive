# Project State

Current phase: Phase 104 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Local decode + preview** — rasterio decode of real MRMS `.grib2.gz`; decoded_prototype preview PNG under `data/dev/`
- **Decoder setup** — `make check-decoders`, `make install-decoders`, `make decode-retry`
- **Local render pipeline** — `make mrms-local-render-pipeline`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator commands (Phase 104)

```bash
make check-decoders
make install-decoders
make decode-grib2 ARGS="--latest-mrms"
make decode-retry
make mrms-local-render-pipeline
```

Artifacts:

- `data/staging/grib2_decode/20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638/`
- `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
- `data/dev/decode_retry_latest.json`
- `data/dev/decoder_setup_latest.json`

Local Phase 104 result: **decode success** (rasterio, 7000×3500); **decoded_prototype preview** produced.

Optional decoders: `requirements-optional-decoders.txt` (not part of `make setup`).

## Verified MRMS

`verified_mrms` is **false** everywhere.
