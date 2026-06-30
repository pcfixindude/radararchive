# Project State

Current phase: Phase 105 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Decoded map overlay** — local dev preview on MapLibre map via `/api/dev/decoded-overlay`
- **Local decode + preview** — rasterio decode; preview PNG under `data/dev/`
- **Decoder setup** — `make check-decoders`, `make install-decoders`, `make decode-retry`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator commands (Phase 105)

```bash
make decode-retry
make mrms-local-render-pipeline
make backend
make frontend
```

Then open the app and use **Refresh** in the Local decoded preview panel.

API (local dev):

- `GET /api/dev/decoded-overlay`
- `GET /api/dev/decoded-overlay/preview.png`

Artifacts:

- `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
- `data/dev/decode_retry_latest.json`

## Verified MRMS

`verified_mrms` is **false** everywhere.
