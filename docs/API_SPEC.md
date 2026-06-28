# API Spec

## Health
GET /api/health

Response:
```json
{"status":"ok","version":"0.1.0"}
```

## Demo plan selection (Phase 7)

Most catalog/tile endpoints accept a demo plan for stub subscription enforcement:

- Query param: `?plan=free|basic|pro|business`
- Header: `X-Demo-Plan: pro`

Default when omitted: `pro` (local development).

Invalid plan → `400`:
```json
{
  "detail": {
    "error": "invalid_plan",
    "message": "Unknown plan 'foo'. Use one of: basic, business, free, pro."
  }
}
```

History windows are calculated relative to the **latest catalog timestamp** for the layer, not wall-clock time.

## Access

GET /api/access/plans

Returns configured demo plans from SQLite.

GET /api/access/current?plan=pro

Returns current plan context:
```json
{
  "plan": "pro",
  "name": "Pro",
  "history_days": 90,
  "history_limit_label": "Last 90 days",
  "reference_latest": "2026-06-27T20:20:00Z",
  "demo_mode": true,
  "upgrade_message": "Upgrade to Business for unrestricted historical replay."
}
```

Plan limits (demo):
- free: latest frame only (`history_days=0`)
- basic: 7 days
- pro: 90 days
- business: unrestricted

## Layers
GET /api/layers

Returns layer metadata including:
- `id`, `name`, `type`, `available`, `source`
- `bounds` — optional `[west, south, east, north]` for tile-enabled layers
- `minzoom`, `maxzoom` — optional zoom range hints
- `tile_support` — whether placeholder tiles are available
- `placeholder` — true when tiles are stubs, not real radar

## Times
GET /api/times?layer=mrms_reflectivity

Returns ascending UTC ISO timestamp strings **allowed by the selected demo plan**.

Optional query params:
- `processed_only=true` — return only processed timestamps
- `plan=pro` — demo plan (default `pro`)

## Latest
GET /api/latest?layer=mrms_reflectivity

Returns the latest timestamp allowed by the selected demo plan.

Response:
```json
{"layer":"mrms_reflectivity","timestamp":"2026-06-27T20:20:00Z"}
```

## Tiles
GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png

Query param: `?plan=pro` (recommended for browser tile requests)

Behavior:
- Returns `image/png` when layer/timestamp is processed **and** within plan window
- **Default (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`):** placeholder PNG tiles
- **Optional (`ENABLE_DECODED_TILES=true`):** decoded-prototype PNG when Phase 12 artifacts exist; otherwise placeholder fallback
- **Production (`ENABLE_PRODUCTION_RADAR_TILES=true`):** serves `production-prototype` when catalog `production_rendering=true`, `render_status=production_rendered`, and cached tile exists; otherwise honest placeholder fallback
- Returns `404` when layer/timestamp is unavailable or unprocessed
- Returns `403` JSON when timestamp exists but is outside the demo plan window:

```json
{
  "detail": {
    "error": "plan_limit_exceeded",
    "message": "Timestamp is outside the selected demo plan history window.",
    "plan": "free",
    "plan_name": "Free",
    "timestamp": "2026-06-27T20:00:00Z",
    "reference_latest": "2026-06-27T20:20:00Z",
    "history_limit_label": "Latest frame only",
    "upgrade_message": "Upgrade to Basic, Pro, or Business to unlock more historical radar replay."
  }
}
```

Example:
```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:20:00Z/0/0/0.png?plan=free"
```

Note: URL-encode the timestamp if needed.

Response headers:
- `X-RadarArchive-Tile`: `placeholder` | `placeholder_for_real_raw` | `decoded-prototype` | `production-prototype`
- `X-RadarArchive-Production-Rendering`: `true` when serving `production-prototype`; otherwise `false`
- `X-RadarArchive-Render-Status`: `placeholder` | `decoded_prototype` | `production_pending` | `production_rendered` | `production_failed`
- `X-RadarArchive-Tile-Fallback`: `true` when decode/production enabled but artifact missing or gate blocked
- `X-RadarArchive-Tile-Cache`: `hit` when served from pre-built cache

GET /tiles/config

Returns tile serving configuration (dev):

```json
{
  "enable_decoded_tiles": false,
  "enable_production_radar_tiles": false,
  "default_mode": "placeholder",
  "decoded_mode": "decoded-prototype",
  "production_mode": "production-prototype",
  "production_rendering": false,
  "production_rendering_enabled": false,
  "note": "Placeholder default; production warping prototype requires ENABLE_PRODUCTION_RADAR_TILES plus catalog gate and built tiles."
}
```

Access plan enforcement uses demo plans only — no real auth, JWT, or Stripe yet.

## MRMS source discovery (Phase 8 — dev/metadata)

GET /api/sources/mrms/latest?product=MRMS_ReflectivityAtLowestAltitude&limit=5

Lists latest discovered MRMS object metadata. Does not download or render GRIB2.

Query params:
- `product` — MRMS product name (default `MRMS_ReflectivityAtLowestAltitude`)
- `limit` — max files (1–50, default 5)

Response:
```json
{
  "mode": "stub",
  "product": "MRMS_ReflectivityAtLowestAltitude",
  "count": 3,
  "items": [
    {
      "product": "MRMS_ReflectivityAtLowestAltitude",
      "timestamp": "2026-06-26T20:00:00Z",
      "object_key": "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz",
      "source_url": "https://noaa-mrms-pds.s3.amazonaws.com/CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz",
      "file_name": "MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz",
      "size_bytes": 123456,
      "source_provider": "noaa_aws",
      "catalog_product_id": "mrms_reflectivity"
    }
  ]
}
```

Network failure in `MRMS_SOURCE_MODE=real` → `503` with friendly message. Use `stub` mode for offline dev.

Example:
```bash
curl "http://127.0.0.1:8000/api/sources/mrms/latest?limit=3"
```

## MRMS download status (Phase 9 — dev/metadata)

GET /api/sources/mrms/download-status

Returns download counts for `mrms_discovered` catalog rows.

Response:
```json
{
  "mode": "stub",
  "total": 5,
  "pending": 2,
  "downloaded": 3,
  "failed": 0,
  "note": "Download status for mrms_discovered catalog rows. Rendering remains placeholder."
}
```

Example:
```bash
curl "http://127.0.0.1:8000/api/sources/mrms/download-status"
```

## MRMS processing status (Phase 10 — dev/metadata)

GET /api/sources/mrms/processing-status

Returns processing status counts for all catalog rows.

Response:
```json
{
  "total": 8,
  "pending": 0,
  "placeholder_processed": 5,
  "placeholder_for_real_raw": 3,
  "real_decode_not_implemented": 3,
  "failed": 0,
  "note": "Processing status for catalog rows. GRIB2 decode and real radar rendering are not implemented."
}
```

Tile response headers when placeholders are served:
- `X-RadarArchive-Tile: placeholder` — stub/demo processed frames
- `X-RadarArchive-Tile: placeholder_for_real_raw` — real GRIB2.gz with preview only
- `X-RadarArchive-Raw-Kind: mrms_real_grib2` — raw file kind hint

Example:
```bash
curl "http://127.0.0.1:8000/api/sources/mrms/processing-status"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```
