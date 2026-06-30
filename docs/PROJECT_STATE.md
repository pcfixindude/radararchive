# Project State

Current phase: Phase 107 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Time-synced decoded overlay** — overlay visible only when selected catalog timestamp matches decoded candidate
- **Mismatch/stale UI** — panel shows sync status, selected vs candidate timestamps
- **Color decoded overlay** — reflectivity dBZ color scale; local raster tiles z0–z1
- **Decoded map overlay** — `/api/dev/decoded-overlay?timestamp=` + tile endpoints
- **Local decode + preview** — `make decode-retry`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator commands (Phase 107)

```bash
make decode-retry
make backend
make frontend
```

API (local dev):

- `GET /api/dev/decoded-overlay?timestamp=<ISO>`
- `GET /api/dev/decoded-overlay/preview.png`
- `GET /api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png`

Artifacts:

- `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png` (colorized)
- `data/dev/mrms_local_render_tiles/` (8 prototype tiles)
- Candidate timestamp from pipeline/decode manifest: `2026-06-28T13:26:38Z`

## Georef (prototype)

- `georef_quality`: `rasterio_bounds` or `rasterio_wgs84_affine` when rasterio-enriched metadata present
- `geo_accurate`: **false** — local dev placement only

## Verified MRMS

`verified_mrms` is **false** everywhere.
