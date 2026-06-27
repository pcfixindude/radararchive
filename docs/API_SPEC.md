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

Access plan enforcement uses demo plans only — no real auth, JWT, or Stripe yet.
