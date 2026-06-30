# Next Steps

## Phase 106 - Improve decoded preview color scale and tile slicing (Draft)

Goal: Better reflectivity colors and multi-tile/zoom preview for local decoded prototype overlay.

```bash
make decode-retry
make build-tile-cache
# optional: ENABLE_DECODED_TILES=true for catalog frame tiles (still prototype)
```

## Phase 105 verification commands

```bash
make test
cd frontend && npm test
cd frontend && npm run build
make decode-retry
make backend
make frontend
```

Local result after Phase 105:

- Decoded preview visible on map when preview PNG exists
- API: `/api/dev/decoded-overlay`, `/api/dev/decoded-overlay/preview.png`
- Frontend: `DecodedOverlayPanel`, `WeatherMap` decoded overlay layer
- Georef: rasterio bounds when available; else prototype CONUS bounds
- Labels: prototype, local dev only, NOT verified MRMS

Refresh after pipeline:

```bash
make decode-retry
# click Refresh in Local decoded preview panel
```

## Phase 104 verification commands

```bash
make install-decoders
make decode-retry
make mrms-local-render-pipeline
```
