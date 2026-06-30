# Next Steps

## Phase 107 - Time-synced playback and geo-accurate overlay (Draft)

Goal: Tie decoded overlay to selected catalog timestamp; improve georef placement for local dev.

```bash
make decode-retry
make backend
make frontend
```

## Phase 106 verification commands

```bash
make test
cd frontend && npm test
cd frontend && npm run build
make decode-retry
```

Local result after Phase 106:

- `color_scale_mode`: `reflectivity_dbz`
- `tile_mode`: `local_raster_tiles`
- `tile_count`: 8 (z0–z1, 2×2 per level)
- Color preview: `data/dev/mrms_local_render_preview/preview_z0_x0_y0.png`
- Local tiles: `data/dev/mrms_local_render_tiles/{z}/{x}/{y}.png`
- Map uses raster tile source when tiles available; image overlay fallback otherwise

## Phase 105 verification commands

```bash
make decode-retry
make backend
make frontend
```
