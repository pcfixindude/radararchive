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

Summary additions (Phase 32): `scheduled_proof_bundle` compact (`bundle_exported`, `bundle_id`, `diff_status`, `evidence_changes_count`, `operator_attention_needed`). Validation alert adds `proof_bundle_diff_status`, `proof_bundle_diff_attention`, `latest_proof_bundle_id`.

Summary additions (Phase 33): `operator_guidance` list (`title`, `path`, `anchor`, `section_label`, `cause`, `suggested_action`) from latest alert when attention needed. `scheduled_proof_bundle` adds `handoff_requested`, `handoff_generated`, `handoff_path`, `handoff_reason`, `diff_status_that_triggered_handoff`. `operator_handoff` adds scheduled handoff status fields. Validation alert compact includes `operator_guidance`.

Scheduled validation report additions (Phase 33): `handoff_requested`, `handoff_generated`, `handoff_path`, `handoff_reason`, `diff_status_that_triggered_handoff`; step `operator_handoff` when `--handoff` passed.

Summary additions (Phase 34): `proof_bundle_diff_alert` compact (latest timeline entry + count), `proof_bundle_diff_alert_history` (last 5 entries). Validation alert adds `proof_bundle_diff_alert_history_count`, `latest_proof_bundle_diff_alert_at`, `latest_proof_bundle_diff_alert_status`.

`GET /api/validation/proof-bundle-diff-alert-history` — bounded diff alert timeline (`?limit=25` max). `verified_mrms: false`, `local_history_only: true`. Read-only; recording happens during diff evaluation.

Summary additions (Phase 35): `proof_bundle_diff_alert_trend` compact (`trend`, streaks, last worsened/mixed/improved timestamps), `proof_bundle_diff_acknowledgment` compact. Validation alert adds `diff_acknowledgment_count`, `latest_diff_acknowledgment_at/operator`, `diff_alert_acknowledged_but_still_active`, `proof_bundle_diff_alert_trend`.

`GET /api/validation/proof-bundle-diff-alert-trend` — trend summary (`?window=10` max 25). `verified_mrms: false`, `local_trend_only: true`.

`GET /api/validation/proof-bundle-diff-acknowledgments` — bounded acknowledgment list (read-only).

`POST /api/validation/proof-bundle-diff-acknowledgments` — dev/local acknowledgment (`operator_initials`/`operator_name`, `note` required). Does **not** clear alerts or set `verified_mrms`. Response includes `diff_alert_still_active`.

`GET /api/validation/proof-bundle-diff-escalation` — escalation hints from trend + history + acknowledgment (`verified_mrms: false`, `local_escalation_only: true`, `does_not_clear_alerts: true`). Read-only.

Summary additions (Phase 36): `proof_bundle_diff_escalation` compact (`escalation_level`, `reason`, `stale_acknowledgment`, `suggested_next_action`, `guidance_items`). Validation alert adds `proof_bundle_diff_escalation_level`, `proof_bundle_diff_escalation_stale_ack`, `proof_bundle_diff_escalation_reason`, `proof_bundle_diff_escalation_suggested_next_action`, `proof_bundle_diff_escalation_guidance_items`.

`GET /api/validation/proof-bundle-diff-escalation-history` — bounded escalation snapshot history (`?limit=25` max). `verified_mrms: false`, `local_history_only: true`. Read-only.

Summary additions (Phase 37): `proof_bundle_diff_escalation_history` compact (`count`, `latest_snapshot_at`, `recent`, `urgent_stdout_notice_triggered/at`). Validation alert adds `proof_bundle_diff_escalation_history_count`, `latest_proof_bundle_diff_escalation_snapshot_at`, `urgent_stdout_notice_triggered/at`.

Scheduled validation: optional `--notify-stdout` / `--urgent-stdout` prints local urgent notice when escalation is urgent; `make scheduled-proof-bundle-notify` runs proof bundle + handoff + notify.

`GET /api/validation/proof-bundle-diff-escalation-metrics` — rollup counts/streaks from bounded history (`verified_mrms: false`, `local_metrics_only: true`).

`GET /api/validation/proof-bundle-diff-escalation-digest` — latest local digest metadata/Markdown (`local_digest_only: true`).

Summary additions (Phase 38): `proof_bundle_diff_escalation_metrics`, `proof_bundle_diff_escalation_digest` compacts.

Summary additions (Phase 39): `scheduled_digest` compact (`digest_requested`, `digest_generated`, `digest_path`, `digest_metadata_path`, `digest_reason`, `digest_elapsed_seconds`, safety flags). `operator_handoff` compact adds `include_escalation_review`, `digest_path`, `acknowledgment_status`, `stale_acknowledgment`, `escalation_level`, `review_checklist_count`.

Scheduled validation report additions (Phase 39): `digest_requested`, `digest_generated`, `digest_path`, `digest_metadata_path`, `digest_reason`, `digest_elapsed_seconds`; step `escalation_digest` when `--digest` / `--escalation-digest` passed.

Summary additions (Phase 40): `proof_bundle_diff_escalation_digest_history`, `proof_bundle_diff_escalation_digest_diff`, `digest_regeneration_hint` compacts.

New read-only endpoints (Phase 40): `GET /api/validation/proof-bundle-diff-escalation-digest-history`, `GET /api/validation/proof-bundle-diff-escalation-digest-diff`.

Summary additions (Phase 41): `mrms_review_session` compact (`latest_created_at`, `latest_operator`, `latest_escalation_level`, `open_attention_count`, safety flags).

Endpoints (Phase 41): `GET /api/validation/review-sessions`, `POST /api/validation/review-sessions` (local dev only; requires operator, notes or checklist, accepted limitations).

Summary additions (Phase 42): `mrms_review_session.comparison` compact (`overall_review_diff_status`, baseline/latest timestamps, count changes, improvements/regressions); `mrms_review_session.open_attention_guidance` (runbook path, anchor, section_label, suggested_action per open attention item).

Endpoints (Phase 42): `GET /api/validation/review-sessions/comparison`, `GET /api/validation/review-sessions/comparison/history` (read-only; `verified_mrms: false`, `local_comparison_only: true`).

Summary additions (Phase 43): `mrms_review_session_export` compact (`created_at`, `export_path`, `comparison_status`, `open_attention_count`); `review_export_regeneration_hint` (`review_export_regeneration_recommended`, `reason`, `suggested_command`).

Endpoints (Phase 43): `GET /api/validation/review-sessions/export`, `GET /api/validation/review-sessions/export/history` (read-only; `verified_mrms: false`, `local_export_only: true`).

Summary additions (Phase 44): `scheduled_review_export` compact (`review_export_requested`, `review_export_generated`, `review_export_path`, `review_export_reason`, `review_export_elapsed_seconds`).

Scheduled validation report additions (Phase 44): `review_export_requested`, `review_export_generated`, `review_export_path`, `review_export_metadata_path`, `review_export_reason`, `review_export_elapsed_seconds`; step `review_session_export` when `--review-export` / `--export-review` passed. Skips with `skipped_no_review_session` without failing the run.

Summary additions (Phase 45): `mrms_review_session_export_diff` compact (`overall_export_diff_status`, `latest_export_created_at`, `baseline_export_created_at`, `session_changed`, `open_attention_count_change`, `improvements`, `regressions`).

Endpoints (Phase 45): `GET /api/validation/review-sessions/export/diff`, `GET /api/validation/review-sessions/export/diff/history` (read-only; register before `/review-sessions/export`; `verified_mrms: false`, `local_export_diff_only: true`).

`POST /api/validation/review-sessions` additions (Phase 45): optional `export_after_create: true` — creates session, runs comparison as normal, exports Markdown, records export diff; response includes `export_generated`, `export_path`, `export_error` (session is **not** rolled back on export failure).

Export diff `overall_export_diff_status`: `no_baseline` (first export), `unchanged`, `improved`, `worsened`, `mixed`, `unknown`. Persisted under gitignored `data/dev/mrms_review_session_export_diff_latest.json` + bounded history (max 25).

Summary additions (Phase 46): `mrms_review_session_export_diff_trend` compact (`trend`, `latest_status`, counts, streaks, `last_worsened_at`, `last_improved_at`, `suggested_next_action`).

Endpoints (Phase 46): `GET /api/validation/review-sessions/export/diff/trend` (read-only; register before `/export/diff`; `verified_mrms: false`, `local_trend_only: true`). Optional `window` query (1–25).

Export diff trend values: `no_data`, `stable`, `improving`, `worsening`, `mixed` — derived from bounded export diff history; does not verify MRMS or clear alerts.

Summary additions (Phase 47): `mrms_review_session_export_diff_trend_hint` compact (`review_trend_regeneration_recommended`, `reason`, `suggested_command`, `trend`, `latest_export_diff_status`, streaks, `export_is_stale`).

Endpoints (Phase 47): `GET /api/validation/review-sessions/export/diff/trend-hint` (read-only; register before `/export/diff/trend`; `verified_mrms: false`, `local_hint_only: true`).

Scheduled validation report additions (Phase 47): when `review_export_requested`, `review_export_trend_hint` compact on report and in `scheduled_review_export` summary (does not auto-create sessions or export unless `--review-export` requested).

Summary additions (Phase 48): `mrms_review_session_export_diff_history` compact (`count`, `latest_status`, `latest_created_at`, `recent` max 5 entries with status, session change, attention/comparison changes, improvement/regression counts).

Summary additions (Phase 49): `operator_review_status` compact (`status_level` `ok`/`watch`/`attention`/`urgent`/`unknown`, `status_reason`, `top_recommended_action`, `top_suggested_command`, `review_session_recommended`, `review_export_recommended`, `digest_regeneration_recommended`, `evidence_trend`, latest session/export/digest timestamps, `open_attention_count`, `active_guidance_count`, safety flags).

Endpoints (Phase 49): `GET /api/validation/operator-review-status` (read-only consolidation; `verified_mrms: false`, `local_status_only: true`, `does_not_clear_alerts: true`, `does_not_enable_production: true`).

Summary additions (Phase 50): `operator_review_status` adds `guidance_items`, `top_guidance_item`, `runbook_path`, `runbook_section`, `suggested_action`. `scheduled_operator_status` compact from latest scheduled report (`operator_status_level`, `operator_status_reason`, `operator_status_top_suggested_command`, …).

Scheduled validation report additions (Phase 50): when `operator_status_requested` (explicit `--operator-status` or implicit with `--review-export`), report includes operator status fields and `operator_review_status` step. Generation failure sets `operator_status_generated: false` and `operator_status_error` without failing the whole run.

Summary additions (Phase 52): `operator_workflow_presets` compact (`recommended_count`, `presets[]` with `preset_id`, `title`, `when_to_use`, `command`, `expected_outputs`, `safety_notes`, `recommended`, `recommendation_reason`, safety flags). Presets are read-only workflow guidance derived from `operator_review_status` — do not verify MRMS, clear alerts, or enable production rendering.

Endpoints (Phase 52): `GET /api/validation/operator-workflow-presets` (read-only preset list; `verified_mrms: false`, `local_workflow_only: true`, `does_not_clear_alerts: true`, `does_not_enable_production: true`).

**Preset IDs:** `quick-status-check`, `full-local-proof-review`, `create-review-session-and-export`, `regenerate-digest-checklist-export`, `regenerate-visual-review`, `inspect-worsening-export-trend`, `review-proof-bundle-diff`, `run-scheduled-proof-bundle-operator-status`, `full-scheduled-proof-review-with-visual-review`.

**Recommendation rules:** digest stale → `regenerate-digest-checklist-export`; visual review stale → `regenerate-visual-review` or `full-scheduled-proof-review-with-visual-review`; no session or worsening/mixed export trend → `create-review-session-and-export`; ok/watch status → `quick-status-check`.

Summary additions (Phase 53): each preset object adds `runbook_path`, `runbook_section`, `runbook_anchor`, `suggested_action`. Presets remain read-only advisory guidance — commands are copy-ready for manual terminal use; the API/UI does not execute commands.

Summary additions (Phase 54): each preset adds `group_id`, `group_title`, `priority`, `recommended_priority`, `short_reason`. Compact `operator_workflow_preset_groups` lists groups (`status-checks`, `full-review`, `review-session-export`, `troubleshooting`, `scheduled-workflows`) with per-group preset summaries. Sort order: recommended first, then `recommended_priority` (lower = higher urgency: no session → worsening/mixed trend → digest stale → session recommended → ok/watch), then `priority`.

Summary additions (Phase 56): `mrms_visual_review` compact (`available`, `created_at`, `json_path`, `markdown_path`, `layers_inspected`, `timestamp_count`, `frame_count`, `artifact_count`, `missing_artifact_count`, `tile_modes_found`, `suggested_next_command`, `history_count`, safety flags). `operator_review_status` may include optional `latest_visual_review_at`, `latest_visual_review_json_path`, `latest_visual_review_markdown_path` when a report exists.

Endpoints (Phase 56): `GET /api/validation/mrms-visual-review` (latest manifest or safe empty state); `GET /api/validation/mrms-visual-review/history` (`limit` max 25). Read-only — inspects existing artifacts only; `verified_mrms: false`, `local_visual_review_only: true`, `does_not_clear_alerts: true`, `does_not_enable_production: true`.

Summary additions (Phase 57): `mrms_visual_review_comparison` compact (`overall_visual_review_diff_status`, `artifact_count_change`, `missing_artifact_count_change`, `tile_modes_added`, `tile_modes_removed`, …); `mrms_visual_review_hint` compact (`visual_review_regeneration_recommended`, `reason`, `stale_visual_review`, `latest_relevant_evidence_at`, …).

Endpoints (Phase 57): `GET /api/validation/mrms-visual-review/comparison`; `GET /api/validation/mrms-visual-review/comparison/history`; `GET /api/validation/mrms-visual-review/hint`. Comparison persists `mrms_visual_review_comparison_latest.json` + bounded history when `make mrms-visual-review-compare` runs. Hints are read-only guidance — do not download/decode MRMS or enable production rendering.

Summary additions (Phase 58): `operator_review_status` adds `visual_review_regeneration_recommended`, `visual_review_hint_reason`, `latest_visual_review_path`, `latest_visual_review_comparison_status`, `visual_review_artifact_count`, `visual_review_missing_artifact_count`. Workflow preset `regenerate-visual-review` recommended when visual review hint recommends regeneration. Visual review recommendation is local review guidance only — does not verify MRMS, clear alerts, download/decode MRMS, or enable production rendering.

Summary additions (Phase 59): `scheduled_visual_review` compact (`visual_review_requested`, `visual_review_generated`, `visual_review_path`, `visual_review_markdown_path`, `visual_review_history_count`, `visual_review_reason`, `visual_review_elapsed_seconds`, `visual_review_error`). `operator_review_status` may include nested `scheduled_visual_review` from latest scheduled report. Scheduled validation accepts `--visual-review` (explicit opt-in; default unchanged). Workflow preset `full-scheduled-proof-review-with-visual-review` → `make scheduled-proof-bundle-visual-review`.

Scheduled validation report additions (Phase 59): when `visual_review_requested`, report includes visual review fields and `mrms_visual_review` step after operator status. Generation failure sets `visual_review_generated: false` and `visual_review_error` without failing the whole run.

**`status_level` interpretation:** `urgent` — failed validation alert, urgent escalation, or worsening export-diff streak ≥2; `attention` — regeneration hints (digest, visual review, export), worsened/mixed latest export diff, or open attention items; `watch` — stable/mixed export trend with history, visual review comparison mixed/unknown, or escalation/alert watch; `ok` — improving/stable evidence without recommendations; `unknown` — insufficient local review data (except sparse visual-review-only attention when regeneration is recommended).

**Runbook guidance mapping:** urgent/attention/watch status levels; digest/review-export/review-session recommendations; evidence trend worsening/mixed/stable/improving — each maps to a runbook anchor under `docs/RUNBOOK_REAL_MRMS_VALIDATION.md`.

**`top_suggested_command` priority:** (1) digest stale → `make scheduled-proof-bundle-review-export`; (2) no session → initial `make mrms-review-session` with `--export-after-create`; (3) session exists, export stale → `make mrms-review-session-export`; (4) trend/session attention → `make mrms-review-session` with `--export-after-create`; (5) visual review stale → `make mrms-visual-review`.

Existing endpoint unchanged: `GET /api/validation/review-sessions/export/diff/history` (full bounded history up to 25).

Scheduled validation report additions (Phase 32): `bundle_requested`, `diff_bundle_requested`, `mrms_proof_bundle`, `mrms_proof_bundle_diff`; steps `proof_report`, `proof_regression`, `proof_bundle_export`, `proof_bundle_diff`.

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
