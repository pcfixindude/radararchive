# Project State

Current phase: Phase 108 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Selected-frame decode** — timestamp query resolves/decodes/caches local MRMS frame
- **Per-frame cache** — `data/dev/mrms_frame_cache/{token}/`
- **Time-synced decoded overlay** — overlay visible when selected frame decodes successfully
- **Actionable no-local states** — nearest timestamps + download/decode commands in panel
- **Color decoded overlay** — reflectivity dBZ color scale; local raster tiles z0–z1
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator commands (Phase 108)

```bash
make decode-retry
make backend
make frontend
```

API (local dev):

- `GET /api/dev/decoded-overlay?timestamp=<ISO>&refresh=false`
- `GET /api/dev/decoded-overlay/preview.png?timestamp=<ISO>`
- `GET /api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png?timestamp=<ISO>`

Artifacts:

- Per-frame cache: `data/dev/mrms_frame_cache/{timestamp_token}/`
- Latest fallback: `data/dev/mrms_local_render_preview/`, `data/dev/mrms_local_render_tiles/`

## Verified MRMS

`verified_mrms` is **false** everywhere.
