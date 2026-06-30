# Project State

Current phase: Phase 106 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Color decoded overlay** — reflectivity dBZ color scale; local raster tiles z0–z1
- **Decoded map overlay** — `/api/dev/decoded-overlay` + tile endpoints
- **Local decode + preview** — `make decode-retry`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator commands (Phase 106)

```bash
make decode-retry
make mrms-local-render-pipeline
make backend
make frontend
```

API (local dev):

- `GET /api/dev/decoded-overlay`
- `GET /api/dev/decoded-overlay/preview.png`
- `GET /api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png`

Artifacts:

- `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png` (colorized)
- `data/dev/mrms_local_render_tiles/` (8 prototype tiles)

## Verified MRMS

`verified_mrms` is **false** everywhere.
