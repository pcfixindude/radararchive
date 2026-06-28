# RadarArchive

RadarArchive is a cloud-first historical weather replay app focused on radar history.

Primary purpose:
- Archive public NOAA/NWS weather data automatically in the cloud.
- Let users replay historical radar and weather layers from a mobile-friendly app.

Initial scope:
- MRMS radar archive
- Mobile PWA map
- Time slider playback
- Layer toggles
- Subscription-ready structure

Not initial scope:
- Native Android app
- Global weather coverage
- Full Level-II radar viewer
- AI forecasting

## Local development

```bash
make setup
make seed
make test
make backend
```

Simulate one collector run (optional):

```bash
make collect-once
make process-once
```

Discover MRMS object metadata (Phase 8):

```bash
make discover-mrms
make discover-mrms -- --register --limit 5
MRMS_SOURCE_MODE=real make discover-mrms -- --limit 5
```

Download MRMS GRIB2.gz files (Phase 9 — no GRIB2 parse):

```bash
make download-mrms -- --register-discovered --limit 5
make download-mrms -- --limit 5
make download-mrms -- --limit 5 --force
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 3
```

Process raw files into placeholder PNGs (Phase 10 — no GRIB2 decode):

```bash
make process-once
```

Inspect GRIB2.gz metadata (Phase 11 — evaluation spike, no rendering):

```bash
make inspect-grib2
PYTHONPATH=. python scripts/inspect_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1
make inspect-grib2
```

See `docs/GRIB2_DECODE.md` for decoder options and the intended future pipeline.

Decode GRIB2 prototype raster (Phase 12 — optional deps):

```bash
make decode-grib2
PYTHONPATH=. python scripts/decode_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz
```

Build prototype tile cache (Phase 13 — feature-flagged, default off):

```bash
make build-tile-cache
ENABLE_DECODED_TILES=true make backend
curl http://127.0.0.1:8000/tiles/config
```

Render status report (Phase 14 — production guardrails):

```bash
make render-status
make render-status -- --sync --dry-run
```

Build production warped tiles (Phase 15–16 — prototype, default off):

```bash
make build-production-tiles
make build-production-tiles ARGS="--dry-run --json-report"
make build-production-tiles ARGS="--min-zoom 0 --max-zoom 2 --force"
```

Render queue + worker (Phase 17–18 — local dev, SQLite only):

```bash
make enqueue-render-job
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"
make render-worker-once
make render-worker ARGS="--max-jobs 5 --sleep 0.5"
make render-queue-status
make render-status
curl http://127.0.0.1:8000/api/render/jobs/summary
```

Feature flags:

```bash
ENABLE_DECODED_TILES=false          # default — placeholder tiles
ENABLE_PRODUCTION_RADAR_TILES=false  # default — production geo-accurate tiles blocked
```

Behavior:
- Demo/collector/MRMS stub raw files → `placeholder_processed` (map tiles work)
- Real downloaded `.grib2.gz` → `placeholder_for_real_raw` preview by default
- With `ENABLE_DECODED_TILES=true` + decode artifacts → optional `decoded-prototype` tiles
- Production warping prototype: `make build-production-tiles` + `ENABLE_PRODUCTION_RADAR_TILES=true` + catalog gate → optional `production-prototype` tiles
- Headers: `X-RadarArchive-Tile`, `X-RadarArchive-Production-Rendering`, `X-RadarArchive-Render-Status`

Limitations:
- Default `MRMS_SOURCE_MODE=stub` uses offline sample listings and stub downloads
- Real mode downloads public NOAA AWS GRIB2.gz but does not render verified production radar
- `make inspect-grib2` reports metadata when wgrib2/optional decoders are installed
- `make decode-grib2` writes prototype artifacts + `geo_metadata.json` to `data/staging/grib2_decode/` when decoders exist
- `make build-production-tiles` warps normalized grids to EPSG:3857 tiles (stdlib math; default zoom 0 only)
- `make enqueue-render-job` + `make render-worker-once` / `make render-worker` process builds via SQLite queue (no Redis)
- `make render-queue-status` reports queue counts and tile/byte totals (prototype — not verified MRMS)
- Build supports `ARGS=` forwarding on Makefile targets (e.g. `make build-production-tiles ARGS="--dry-run"`)
- `ENABLE_DECODED_TILES=false` by default — map `/tiles` serves placeholders only
- `ENABLE_PRODUCTION_RADAR_TILES=false` by default — production prototype tiles blocked
- Production prototype is not verified real MRMS; decoded prototype uses simple grid sampling

In another terminal:

```bash
make frontend
```

Open http://127.0.0.1:5173.

Process frames before tiles appear on the map:

```bash
make process-once
```

Then open http://127.0.0.1:5173 — use **Play** for playback and the **Demo Plan** selector to test Free vs Pro history limits.
