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

## Render jobs (Phase 17–18 — dev/prototype)

`POST /api/render/jobs` — enqueue a production tile build job (SQLite queue, not verified MRMS).

```json
{
  "layer": "mrms_reflectivity",
  "min_zoom": 0,
  "max_zoom": 0,
  "force": false,
  "mark_catalog": false,
  "max_attempts": 3
}
```

Response includes `prototype: true`, `verified_mrms: false`, `status: "queued"`, and retry fields (`attempt_count`, `max_attempts`, `next_retry_at`, etc.).

`GET /api/render/jobs` — list recent jobs (query `limit`, default 50). Optional filters: `status`, `layer`, `timestamp`, `job_type`.

`GET /api/render/jobs/summary` — queue metrics: queued/running/succeeded/failed/canceled counts, `total_tiles_written`, `total_output_bytes`.

`GET /api/render/jobs/{id}` — job status with progress and metrics.

`POST /api/render/jobs/{id}/retry` — re-queue a failed job when `attempt_count < max_attempts` (400 otherwise).

`POST /api/render/jobs/{id}/cancel` — cancel queued or running job (idempotent for terminal jobs).

Job statuses: `queued`, `running`, `succeeded`, `failed`, `canceled`.

No delete/reset endpoints. Process jobs with `make render-worker-once` (one job) or `make render-worker` (continuous loop).

## Validation dashboard (Phase 20 — dev/prototype)

`GET /api/validation/summary` — compact dashboard summary:

- `production_rendering_enabled`, `placeholder_default`, `verified_mrms: false`
- `decoder_available`, `decoder_summary`, `stale_running_job_seconds`
- `validation` — latest validation counts (if `make validate-real-mrms` has run)
- `benchmark` — latest benchmark tile/timing metrics (if `make benchmark-real-mrms` has run)
- `queue_benchmark` — latest queue benchmark metrics (if `make benchmark-render-queue` has run)
- `validation_history` — up to 5 most recent compact validation runs (full list: `/api/validation/history`)
- `queue_benchmark_history_count` — number of saved queue benchmark summaries
- `render_queue` — same metrics as `/api/render/jobs/summary`

`GET /api/validation/latest` — full persisted JSON blobs for validation, benchmark, and queue_benchmark reports (or `null`).

Reports are written by CLI commands to `data/dev/`. Not verified MRMS production output.

`GET /api/validation/history` — last 10 compact validation runs (dev/prototype).

`GET /api/validation/benchmarks` — latest queue benchmark report + last 10 compact summaries (dev/prototype).

`GET /api/validation/scheduled` — latest scheduled validation run + last 10 compact summaries (dev/prototype).

Summary additions (Phase 23): `scheduled_validation` compact status, `frame_summaries` per-frame tile metrics (up to 5).

Summary additions (Phase 24): `scheduled_validation.steps` step drill-down, `validation_failures_count`, `validation_failures_recent`.

Summary additions (Phase 25): `validation_alert` compact marker (`status`, counts, `suggested_next_action`, `operator_attention_needed`), `grouped_failure_causes` (top 5 by step + normalized cause).

`GET /api/validation/failures` — recent validation failure log entries (append-only JSONL, max 100).

`GET /api/validation/alerts` — latest persisted validation alert marker (`data/dev/validation_alert_latest.json`). Query `?refresh=true` rebuilds from failure log + scheduled report. `verified_mrms: false`.

Summary additions (Phase 26): `mrms_proof` compact proof status (`overall_status`, `frame_count`, `criteria_counts`, `operator_review_required`), `mrms_proof_available`.

`GET /api/validation/proof` — latest draft MRMS proof report JSON (`data/dev/mrms_proof_latest.json`). `verified_mrms: false`, `proof_only: true`.

Summary additions (Phase 27): `mrms_proof_regression` compact status, `mrms_signoff` summary (`signoff_count`, `latest_signoff_at`).

Summary additions (Phase 29): `scheduled_validation.proof_step` compact (`ran`, `status`, `elapsed_seconds`, `proof_regression_status`); `mrms_signoff` adds `proof_regression_still_active`, `proof_regression_reviewed`; `validation_alert` adds `latest_signoff_at`, `proof_regression_still_active`.

`GET /api/validation/proof-regression` — latest regression report (`?refresh=true` re-runs check). `verified_mrms: false`.

`GET /api/validation/signoffs` — local operator sign-off records (read-only, compact). `verified_mrms: false`.

`POST /api/validation/signoffs` — **dev/local only** — record operator proof review. Required: `operator_name` or `operator_initials`; `operator_notes` or `accepted_limitations`. Optional: `proof_report_timestamp`, `frame_count_reviewed`. Response always includes `verified_mrms: false`, `local_signoff_only: true`, `does_not_enable_production: true`, `production_enabled` (current flag only). Refreshes validation alert marker; does **not** clear proof regression or enable production rendering.

`GET /api/validation/proof/history` — bounded proof report history (last 10) + latest compact. `verified_mrms: false`.

`GET /api/validation/proof-regression/history` — bounded regression history (last 10) + latest compact. `verified_mrms: false`.

Summary additions (Phase 30): `mrms_proof_bundle` compact (`bundle_folder`, `zip_path`, `file_count`, `created_at`), `runbook_references` (repo doc paths + anchors).

`GET /api/validation/proof-bundles` — bounded local proof bundle export history (read-only). `verified_mrms: false`, `local_bundle_only: true`. Does not create bundles (use `make mrms-proof-bundle`).

Summary additions (Phase 31): `mrms_proof_bundle_diff` compact (`overall_diff_status`, `evidence_changes_count`), `operator_handoff` compact (`markdown_path`, `created_at`).

`GET /api/validation/proof-bundle-diff` — latest proof bundle diff report (`?refresh=true` rebuilds). `verified_mrms: false`, `local_diff_only: true`.

`GET /api/validation/operator-handoff` — latest operator handoff checklist metadata (read-only). `verified_mrms: false`, `local_handoff_only: true`.

`GET /api/catalog/status` — MRMS catalog frame counts by download/process/render status, latest timestamps.

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
