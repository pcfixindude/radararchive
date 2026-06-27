# API Spec

## Health
GET /api/health

Response:
```json
{"status":"ok","version":"0.1.0"}
```

## Layers
GET /api/layers

## Times
GET /api/times?layer=mrms_reflectivity

## Latest
GET /api/latest?layer=mrms_reflectivity

## Tiles
GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png

## Access
Plan limits:
- free: recent only
- basic: 7 days
- pro: 90 days
- business: custom
