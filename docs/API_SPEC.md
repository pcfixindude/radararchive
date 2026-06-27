# API Spec

## Health
GET /api/health

Response:
```json
{"status":"ok","version":"0.1.0"}
```

## Layers
GET /api/layers

Returns layer metadata including:
- `id`, `name`, `type`, `available`, `source`
- `bounds` — optional `[west, south, east, north]` for tile-enabled layers
- `minzoom`, `maxzoom` — optional zoom range hints
- `tile_support` — whether placeholder tiles are available
- `placeholder` — true when tiles are stubs, not real radar

Example (`mrms_reflectivity`):
```json
{
  "id": "mrms_reflectivity",
  "name": "MRMS Reflectivity",
  "type": "raster",
  "available": true,
  "source": "demo",
  "bounds": [-125.0, 24.0, -66.0, 50.0],
  "minzoom": 3,
  "maxzoom": 8,
  "tile_support": true,
  "placeholder": true
}
```

## Times
GET /api/times?layer=mrms_reflectivity

Returns ascending UTC ISO timestamp strings for the layer.

Optional query param (backward-compatible):
- `processed_only=true` — return only timestamps with `processed_status=processed`

## Latest
GET /api/latest?layer=mrms_reflectivity

Response:
```json
{"layer":"mrms_reflectivity","timestamp":"2026-06-27T20:20:00Z"}
```

## Tiles
GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png

Behavior (Phase 4+ placeholder):
- Returns `image/png` when the layer is available and the timestamp has been processed
- Returns `404` when the layer is unknown, unavailable, or the timestamp is missing/unprocessed
- Tiles are generated stub PNG placeholders (not real radar imagery)
- Response header: `X-RadarArchive-Tile: placeholder`

Example:
```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```

Note: URL-encode the timestamp if needed (`2026-06-27T20:00:00Z` → `2026-06-27T20%3A00%3A00Z`).

## Access
Plan limits:
- free: recent only
- basic: 7 days
- pro: 90 days
- business: custom

Access plan enforcement on API routes is not implemented yet.
