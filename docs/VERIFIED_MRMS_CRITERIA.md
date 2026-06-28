# Verified MRMS Criteria (Future Phase — Not Met Today)

This document defines what must be true before RadarArchive could ever set `verified_mrms=true` in code, APIs, or reports.

**Current project status: these criteria are NOT met.** The pipeline remains an experimental prototype. `verified_mrms` is **false** everywhere by design.

## Purpose

`verified_mrms` would mean an operator-reviewed, repeatable process has confirmed that downloaded NOAA MRMS data was decoded, georeferenced, and rendered into tiles that pass documented sanity checks — not merely that files exist or jobs succeeded with zero tiles.

## Required criteria (all must pass)

### 1. Real NOAA MRMS source

- [ ] File downloaded from documented NOAA AWS MRMS source (not stub)
- [ ] Checksum (SHA-256) recorded and matches on re-read
- [ ] File size and timestamp recorded in catalog
- [ ] Source URL/object key retained for audit

### 2. Decoder and decode artifacts

- [ ] Named decoder used (wgrib2, rasterio, GDAL, or approved alternative)
- [ ] Decoder version recorded in decode manifest
- [ ] Decode artifacts written under `data/staging/grib2_decode/`
- [ ] `geo_metadata.json` present with bounds, CRS, grid dimensions

### 3. Product and time metadata

- [ ] Product ID matches expected MRMS reflectivity product
- [ ] Valid time / frame timestamp confirmed against catalog row
- [ ] No mismatch between filename stamp and catalog timestamp

### 4. Geospatial correctness

- [ ] Source and output CRS documented
- [ ] Bounds within expected CONUS (or stated region) tolerance
- [ ] Grid width/height consistent with metadata
- [ ] Warping math reviewed for prototype limitations documented

### 5. Visual / sanity checks

- [ ] Known weather feature or null-echo pattern spot-checked (documented)
- [ ] No obvious all-zero or all-NaN raster
- [ ] Tile PNG non-empty and visually plausible at zoom 0 (operator sign-off)

### 6. Tile output from decoded data

- [ ] Tiles built from decode artifacts, not placeholder generator
- [ ] `tiles_written > 0` for validated frame(s) at agreed zoom
- [ ] Tile cache paths recorded
- [ ] Headers report honest mode (not claiming production if prototype)

### 7. Production path used intentionally

- [ ] `ENABLE_PRODUCTION_RADAR_TILES=true` only during controlled validation
- [ ] Catalog gate satisfied (`production_rendering` / render status)
- [ ] Cached production tile exists before serving
- [ ] Serving headers match intentional production-prototype mode

### 8. Repeatable multi-frame validation

- [ ] Same pipeline succeeds across **multiple** frames (minimum count TBD, e.g. 3+)
- [ ] Per-frame metrics recorded (decode, tiles, elapsed)
- [ ] Failures/warnings absent or explicitly accepted and documented

### 9. Failure and alert hygiene

- [ ] No unacknowledged `failed` alert status for validation window
- [ ] Grouped failure causes reviewed
- [ ] `make validation-alerts` status `ok` or accepted warnings only

### 10. Operator review

- [ ] Human operator review recorded (date, reviewer, commit or report ID)
- [ ] Explicit statement that output is still prototype until product launch review
- [ ] Link to validation reports and failure log snapshot

## What does NOT qualify

- Stub/offline validation with zero decoded frames
- Queue jobs that succeed with **0 tiles written**
- Prototype warping without visual sanity check
- Single-frame smoke test only (insufficient for production claim)
- Automatic pass because real download occurred
- Setting `verified_mrms=true` in tests or demo data

## Current status (Phase 26)

| Criterion area | Status |
|----------------|--------|
| Real NOAA download (optional dev) | Partial — not proof |
| Decoder + decode | Optional — often skipped |
| Geo verification | Prototype only |
| Visual sanity | Not formalized |
| Multi-frame proof | Automated draft report (`make mrms-proof-report`) |
| Operator sign-off | Template only — [MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](MRMS_OPERATOR_SIGNOFF_TEMPLATE.md) |
| **verified_mrms** | **false** |

## Automated proof report fields (Phase 26)

`make mrms-proof-report` writes `data/dev/mrms_proof_latest.json` with:

- `overall_status`: `not_started` | `insufficient_evidence` | `failed` | `ready_for_operator_review`
- `criteria_counts`: passed / failed / warning / skipped / unknown
- `aggregate_criteria`: per-criterion status from this checklist
- `frames[]`: per-frame evidence (checksum, paths, geo sanity, tiles, warnings)
- Always: `verified_mrms: false`, `proof_only: true`, `operator_review_required: true`

Criterion IDs evaluated: `real_noaa_source`, `decoder_and_artifacts`, `product_time_metadata`, `geospatial_correctness`, `visual_sanity_checks` (manual/skipped), `tile_output_from_decoded`, `production_path_intentional`, `repeatable_multi_frame`, `failure_alert_hygiene`, `operator_review` (manual/skipped).

**Signing the operator template does NOT set `verified_mrms=true`.**

## Regression and sign-off workflow (Phase 27)

After each `make mrms-proof-report`, the previous latest report is snapshotted for comparison.

```bash
make mrms-proof-regression
make mrms-signoff ARGS="--initials OP --notes 'reviewed' --accepted-limitations 'prototype only'"
```

- Regression report: `data/dev/mrms_proof_regression_latest.json`
- Sign-offs: `data/dev/mrms_signoffs.json` (local only)
- Validation alerts include `proof_regression` cause when regression detected
- `make scheduled-validation ARGS="--proof"` runs proof + regression after validation

Sign-off records `verified_mrms: false`, `does_not_set_verified_mrms: true`, and `does_not_enable_production: true` always.

## Dev sign-off API (Phase 29)

Optional dev/local `POST /api/validation/signoffs` shares the same validation as `make mrms-signoff`. Response always includes `verified_mrms: false` and `local_signoff_only: true`. Sign-off refreshes the validation alert but does **not** clear proof regression automatically.

## Proof bundle export (Phase 30)

`make mrms-proof-bundle` packages local proof/regression/sign-off/alert JSON into a timestamped folder + ZIP. Bundles are **supporting evidence only** — they do **not** verify MRMS or enable production rendering. Manifest always includes `verified_mrms: false`.

## Proof bundle diff + operator handoff (Phase 31)

`make mrms-proof-bundle-diff` compares the latest bundle to the previous bundle baseline. `make mrms-operator-handoff` writes a local Markdown checklist. Both are **supporting review evidence only** — `verified_mrms` stays false.

## Operator guidance + scheduled handoff (Phase 33)

Validation alert `operator_guidance` and scheduled `--handoff` auto-regeneration are **review aids only**. They map alert causes to runbook sections and may refresh the handoff checklist when proof bundle diff is worsened or mixed. They do **not** set `verified_mrms=true`, enable production rendering, mutate catalog gates, or clear validation alerts.

## Proof bundle diff alert history (Phase 34)

`make proof-bundle-diff-alert-history` and `GET /api/validation/proof-bundle-diff-alert-history` expose a bounded local timeline of diff alert states. This is **supporting review evidence only** — `verified_mrms` stays false and history does not verify MRMS or enable production rendering.

## Proof bundle diff alert trend + acknowledgment (Phase 35)

Trend summary (`make proof-bundle-diff-alert-trend`) and local acknowledgment notes are **supporting review evidence only**. Acknowledgment records operator review but does **not** clear alerts, verify MRMS, or enable production rendering.

## Proof bundle diff alert escalation (Phase 36)

Escalation hints (`make proof-bundle-diff-escalation`) are **supporting review evidence only**. They surface worsening streaks and stale acknowledgments with runbook section links. Escalation does **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Proof bundle diff escalation history + stdout notices (Phase 37)

Bounded escalation history (`make proof-bundle-diff-escalation-history`) and optional `--notify-stdout` urgent terminal notices are **supporting review evidence only**. They help operators track escalation over time and see urgent conditions during scheduled runs. They do **not** verify MRMS, clear alerts, enable production rendering, or send external notifications.

## Proof bundle diff escalation metrics + digest (Phase 38)

Escalation metrics (`make proof-bundle-diff-escalation-metrics`) and local Markdown digest export (`make proof-bundle-diff-escalation-digest`) are **supporting review evidence only**. They summarize bounded history and export operator review notes locally. They do **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Scheduled digest + operator review checklist (Phase 39)

`make scheduled-proof-bundle-digest` and the extended operator handoff checklist (`mrms_operator_handoff_latest.md` with `include_escalation_review`) are **supporting review evidence only**. They combine proof bundle diff, escalation metrics, digest path, and acknowledgment status for local operator review. They do **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Digest export history + diff (Phase 40)

Bounded digest export history (`make proof-bundle-diff-escalation-digest-history`), digest diff metadata (`make proof-bundle-diff-escalation-digest-diff`), and regeneration hints in the Dev Validation summary are **supporting review evidence only**. They help operators track digest exports over time and decide when to re-run `make scheduled-proof-bundle-digest`. They do **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## MRMS proof review sessions (Phase 41)

Local review session records (`make mrms-review-session`, `POST /api/validation/review-sessions`) are **supporting review evidence only**. They snapshot links to escalation, digest, handoff, acknowledgment, bundle, diff, and proof report metadata at review time. They do **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Review session comparison + open attention guidance (Phase 42)

Review session comparison (`make mrms-review-session-compare`, `GET /api/validation/review-sessions/comparison`) and open attention runbook guidance in the Dev Validation summary are **supporting local review aids only**. They help operators see what changed between consecutive review sessions and which runbook sections apply to remaining open attention items. They do **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Review session Markdown export (Phase 43)

Review session Markdown export (`make mrms-review-session-export`, `GET /api/validation/review-sessions/export`) and export regeneration hints (`review_export_regeneration_hint` in summary) are **supporting local review aids only**. They help operators keep a readable local summary of the latest review session, comparison, and runbook guidance. They do **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Scheduled review session export (Phase 44)

Scheduled review session export (`make scheduled-proof-bundle-review-export`, `--review-export` on scheduled validation) is **supporting local review evidence only**. It optionally exports the latest review session Markdown after digest/handoff steps in one local sequence. `skipped_no_review_session` means no session was recorded yet — the scheduled run does not fail. This does **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Review session export diff + auto-export (Phase 45)

Review session export diff (`make mrms-review-session-export-diff`, `GET /api/validation/review-sessions/export/diff`) compares consecutive Markdown export snapshots. Auto-export after session create (`--export-after-create`, `export_after_create: true`) is **supporting local review evidence only**. Export diff statuses (`improved`, `worsened`, `mixed`, `unchanged`, `no_baseline`) help operators see whether the latest exported summary changed vs the previous export. Failed auto-export does **not** roll back the review session. This does **not** verify MRMS, clear alerts, enable production rendering, or satisfy any verified-MRMS criterion.

## Review session export diff trend (Phase 46)

Review session export diff trend (`make mrms-review-session-export-diff-trend`, `GET /api/validation/review-sessions/export/diff/trend`) summarizes bounded export diff history into `improving`, `worsening`, `mixed`, `stable`, or `no_data`. It includes streaks, status counts, and suggested local next actions. This is **supporting local review evidence only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Review session export diff trend hint (Phase 47)

Review session export diff trend hint (`make mrms-review-session-export-diff-trend-hint`, `GET /api/validation/review-sessions/export/diff/trend-hint`) recommends when operators should create a new review session or re-export based on trend, diff, session/export staleness, and digest regeneration signals. Scheduled validation includes `review_export_trend_hint` when review export is requested — it does **not** auto-create sessions. This is **supporting local review evidence only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Review session export diff history (Phase 48)

Review session export diff history in the Dev Validation summary (`mrms_review_session_export_diff_history`, `make mrms-review-session-export-diff-history`) shows recent consecutive export comparisons (`improved`, `worsened`, `mixed`, `unchanged`, `no_baseline`) for local operator review. This is **supporting local review evidence only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Operator review status consolidation (Phase 49)

Consolidated operator review status (`operator_review_status`, `make operator-review-status`, `GET /api/validation/operator-review-status`) summarizes validation alerts, escalation/trend hints, digest and export regeneration hints, review session/export/diff/trend/history into one local Dev Validation block. `status_level` (`ok`/`watch`/`attention`/`urgent`/`unknown`) and `top_suggested_command` follow documented priority rules. This is **local consolidation only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Scheduled operator review status + runbook guidance (Phase 50)

Scheduled operator review status (`make scheduled-proof-bundle-operator-status`, `--operator-status` on scheduled validation; also runs automatically with `--review-export`) adds consolidated status fields to the scheduled report and runbook deep-links (`guidance_items`, `top_guidance_item`, `runbook_path`, `runbook_section`). Operator status guidance maps urgent/attention/watch levels, regeneration recommendations, and evidence trends to runbook sections. This is **local review guidance only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Operator workflow presets (Phase 52)

Operator workflow presets (`operator_workflow_presets`, `make operator-workflow-presets`, `GET /api/validation/operator-workflow-presets`) organize existing local commands into guided presets with `recommended` flags derived from operator review status. Presets include quick status check, full local proof review, create review session and export, regenerate digest/checklist/export, inspect worsening export trend, review proof bundle diff, and scheduled proof bundle with operator status. This is **local workflow guidance only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Operator workflow preset runbook guidance (Phase 53)

Each preset includes `runbook_path`, `runbook_section`, `runbook_anchor`, and `suggested_action` for runbook deep-links. Dev Validation and `make operator-workflow-presets` show copy-ready commands for manual terminal use — presets do **not** execute commands automatically. This remains **local advisory guidance only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Operator workflow preset groups (Phase 54)

Grouped presets (`operator_workflow_preset_groups`, `group_id`, `group_title`, `priority`, `recommended_priority`, `short_reason`) organize workflows into status checks, full review, review session/export, troubleshooting, and scheduled workflows. Recommended presets sort by urgency-derived `recommended_priority`. This is **local presentation and guidance only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Operator workflow preset command UX (Phase 55)

Dev Validation adds client-side preset filters (recommended-only, optional group) and Copy-to-clipboard on command blocks. **Copy does not execute commands** — operators paste into a terminal manually. This is **local UI polish only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## MRMS visual review artifacts (Phase 56)

`make mrms-visual-review` inspects existing local catalog/tile artifacts and writes JSON + Markdown manifests under `data/dev/`. Tile modes distinguish placeholder, decoded prototype, and production-gated/cache paths. This is **local visual evidence only** — it does **not** verify MRMS, clear alerts, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## MRMS visual review comparison and hints (Phase 57)

`make mrms-visual-review-compare` and `make mrms-visual-review-hint` compare manifests and suggest regeneration when proof/validation evidence is newer. This is **local review guidance only** — it does **not** verify MRMS, clear alerts, download/decode MRMS, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Visual review operator integration (Phase 58)

Operator review status and workflow presets consume visual review comparison/hint data. When visual review is stale, status may rise to `attention`, `top_suggested_command` may recommend `make mrms-visual-review`, and the `regenerate-visual-review` workflow preset is recommended. This is **local review guidance only** — it does **not** verify MRMS, clear alerts, download/decode MRMS, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Scheduled visual review workflow (Phase 59)

`make scheduled-proof-bundle-visual-review` and `--visual-review` on scheduled validation optionally generate visual review artifacts after proof/review steps. Explicit opt-in — default scheduled validation unchanged. This is **local workflow tooling only** — it does **not** verify MRMS, clear alerts, download/decode MRMS, notify externally, enable production rendering, or satisfy any verified-MRMS criterion.

## Scheduled proof bundle monitoring (Phase 32)

`make scheduled-proof-bundle` runs scheduled validation with `--proof --bundle --diff-bundle`. This is **local evidence monitoring only** — it does not verify MRMS or enable production rendering. Alerts may flag `worsened` or `mixed` diff status for operator review.

## Proof review history (Phase 28)

Bounded read-only history for dev panel drill-down:

```bash
make mrms-proof-history
make mrms-proof-history ARGS="--json"
curl http://127.0.0.1:8000/api/validation/proof/history
curl http://127.0.0.1:8000/api/validation/proof-regression/history
curl http://127.0.0.1:8000/api/validation/signoffs
```

Dev Validation panel: **Show proof review** toggles proof history, regression history, and sign-off lists.

## Related docs

- [RUNBOOK_REAL_MRMS_VALIDATION.md](RUNBOOK_REAL_MRMS_VALIDATION.md) — how to run and troubleshoot
- [MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](MRMS_OPERATOR_SIGNOFF_TEMPLATE.md) — operator review template
- [GRIB2_DECODE.md](GRIB2_DECODE.md) — decode prototype limitations
- [ARCHITECTURE.md](ARCHITECTURE.md) — pipeline architecture

A future phase may gate `verified_mrms` behind documented operator approval — never by default.
