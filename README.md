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

**ChatGPT continuation:** [docs/CHATGPT_REVIEW.md](docs/CHATGPT_REVIEW.md) is the concise handoff file for continuing work in ChatGPT without full chat history. Cursor updates it before each phase commit.

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

MRMS validation pipeline (Phase 19–24 — experimental, not verified MRMS):

See **[docs/RUNBOOK_REAL_MRMS_VALIDATION.md](docs/RUNBOOK_REAL_MRMS_VALIDATION.md)** for operator troubleshooting, **[docs/VERIFIED_MRMS_CRITERIA.md](docs/VERIFIED_MRMS_CRITERIA.md)** for future verified MRMS proof requirements (not met today), and **[docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md)** for operator sign-off (does not set `verified_mrms`).

```bash
make validate-real-mrms
make validate-real-mrms-batch
make benchmark-real-mrms
make benchmark-render-queue
make scheduled-validation
make scheduled-proof-bundle
make scheduled-proof-bundle-handoff
make scheduled-proof-bundle-digest
make scheduled-proof-bundle-review-export
make scheduled-proof-bundle-operator-status
make proof-bundle-diff-alert-history
make proof-bundle-diff-alert-trend
make proof-bundle-diff-escalation
make proof-bundle-diff-escalation-history
make proof-bundle-diff-escalation-metrics
make proof-bundle-diff-escalation-digest
make proof-bundle-diff-escalation-digest-history
make proof-bundle-diff-escalation-digest-diff
make proof-bundle-diff-acknowledge ARGS="--operator OP --note 'local review only'"
make validation-failures
make validation-alerts
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make mrms-proof-bundle
make mrms-proof-bundle-diff
make mrms-operator-handoff
make mrms-review-session ARGS="--operator OP --notes 'local review only' --accepted-limitations"
make mrms-review-sessions
make mrms-review-session-compare
make mrms-review-session-export
make mrms-review-session-exports
make mrms-review-session-export-diff
make mrms-review-session-export-diff-history
make mrms-review-session-export-diff-trend
make mrms-review-session-export-diff-trend-hint
make operator-review-status
make mrms-review-session ARGS="--operator OP --notes 'local review only' --accepted-limitations --export-after-create"
make real-mrms-smoke-test
make scheduled-validation ARGS="--proof"
make scheduled-validation ARGS="--json-report"
make catalog-status
MRMS_SOURCE_MODE=real make scheduled-validation ARGS="--real --count 3 --min-zoom 0 --max-zoom 1"
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/scheduled
curl http://127.0.0.1:8000/api/validation/failures
curl http://127.0.0.1:8000/api/validation/alerts
curl http://127.0.0.1:8000/api/validation/proof
curl http://127.0.0.1:8000/api/validation/proof-regression
curl http://127.0.0.1:8000/api/validation/proof/history
curl http://127.0.0.1:8000/api/validation/proof-regression/history
curl http://127.0.0.1:8000/api/validation/proof-bundles
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-alert-history
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-alert-trend
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-history
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-metrics
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-acknowledgments
curl http://127.0.0.1:8000/api/validation/operator-handoff
curl http://127.0.0.1:8000/api/validation/signoffs
curl -X POST http://127.0.0.1:8000/api/validation/signoffs \
  -H 'Content-Type: application/json' \
  -d '{"operator_initials":"OP","operator_notes":"local review only"}'
curl http://127.0.0.1:8000/api/validation/latest
curl http://127.0.0.1:8000/api/validation/operator-review-status
```

Sample cron (not installed automatically):

```cron
0 */6 * * * cd /path/to/radararchive && make scheduled-validation >> data/dev/scheduled_validation.log 2>&1
```

Feature flags:

```bash
ENABLE_DECODED_TILES=false          # default — placeholder tiles
ENABLE_PRODUCTION_RADAR_TILES=false  # default — production geo-accurate tiles blocked
STALE_RUNNING_JOB_SECONDS=3600       # stale running job recovery threshold
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
- `make validate-real-mrms-batch` validates up to 3 frames by default (max 10; prototype only)
- `make benchmark-render-queue` enqueues multi-zoom jobs (default count 3, zoom 0–1; use `--dry-run` to plan only)
- `make scheduled-validation` runs catalog + batch + queue benchmark pipeline (cron-friendly; `--real` intentional; `--proof`, `--bundle`, `--diff-bundle` optional)
- `make scheduled-proof-bundle` runs scheduled validation with proof report, bundle export, and diff (local monitoring only)
- `make scheduled-proof-bundle-handoff` adds optional operator handoff auto-regeneration when diff is worsened/mixed (does not verify MRMS)
- `make scheduled-proof-bundle-digest` runs proof bundle pipeline with escalation digest export and extended operator review checklist (local only; does not verify MRMS or notify externally)
- `make scheduled-proof-bundle-review-export` runs the digest sequence plus review session Markdown export (`--review-export`; skips safely when no review session exists; also consolidates operator review status)
- `make scheduled-proof-bundle-operator-status` runs the full proof/review sequence with explicit `--operator-status` and runbook guidance in the scheduled report
- `make proof-bundle-diff-alert-history` shows bounded diff alert timeline (local evidence monitoring only)
- `make proof-bundle-diff-alert-trend` summarizes worsening/improving/mixed/stable trend over recent history
- `make proof-bundle-diff-escalation` shows escalation level and runbook guidance for worsening/stale-ack trends (local only)
- `make proof-bundle-diff-escalation-history` shows bounded escalation snapshots over time
- `make proof-bundle-diff-escalation-metrics` summarizes urgent/attention/watch counts and streaks
- `make proof-bundle-diff-escalation-digest` exports local Markdown digest (not a notification system)
- `make proof-bundle-diff-escalation-digest-history` shows bounded digest export history (local review only)
- `make proof-bundle-diff-escalation-digest-diff` compares consecutive digest exports and shows regeneration hints
- `make scheduled-proof-bundle-notify` runs proof bundle pipeline with optional local stdout urgent notice
- `make proof-bundle-diff-acknowledge` records local acknowledgment (does not clear alerts or verify MRMS)
- `make validation-failures` shows recent local failure log entries
- `make validation-alerts` shows local validation alert marker and grouped failure causes
- `make mrms-proof-report` generates draft verified-MRMS proof evidence report (not verified MRMS)
- `make mrms-proof-regression` detects proof evidence regressions vs previous report
- `make mrms-proof-history` shows bounded proof/regression/sign-off history (read-only)
- `make mrms-proof-bundle` exports local proof evidence folder + ZIP (does not verify MRMS)
- `make mrms-proof-bundle-diff` compares latest vs baseline bundle evidence (local review only)
- `make mrms-operator-handoff` generates local operator handoff Markdown checklist
- `make mrms-review-session` records local MRMS proof review session linking digest/escalation/diff evidence (does not verify MRMS)
- `make mrms-review-sessions` lists bounded review session history (read-only)
- `make mrms-review-session-compare` compares latest vs previous review session (local comparison only; does not verify MRMS)
- `make mrms-review-session-export` exports latest review session to local Markdown + JSON metadata (does not verify MRMS)
- `make mrms-review-session-exports` lists bounded review session export history (read-only)
- `make mrms-review-session-export-diff` shows latest export diff vs previous export (local review only; `improved`/`worsened`/`mixed`/`unchanged`/`no_baseline`)
- `make mrms-review-session-export-diff-history` lists bounded export diff history (`--json`, `--limit`); Dev Validation collapsible **Review export diff history** shows recent entries when expanded
- `make mrms-review-session-export-diff-trend` summarizes export diff trend (`improving`/`worsening`/`mixed`/`stable`/`no_data`; `--json`, `--limit`)
- `make mrms-review-session-export-diff-trend-hint` shows when a new review session/export is recommended (`--json`)
- `make operator-review-status` prints consolidated local operator review status with runbook guidance and visual review recommendation fields (`--json`); Dev Validation **Operator Review Status** block shows visual review staleness (Phase 58)
- `make operator-workflow-presets` lists grouped local workflow presets with runbook guidance, short reasons, and copy-ready commands (`--json`); includes `regenerate-visual-review` when visual review is stale (Phase 58)
- `make mrms-visual-review` generates a local visual review manifest (JSON + Markdown) of existing tile/render artifacts (`--json-report`, `--history`); Dev Validation **MRMS Visual Review** collapsible section (Phase 56)
- `make mrms-visual-review-compare` compares latest vs previous visual review manifests; `make mrms-visual-review-hint` suggests when to regenerate (Phase 57)
- `make mrms-visual-review-sample-set` builds a local recommended sample subset for manual drilldown inspection (Phase 60)
- `make mrms-visual-review-readiness` computes local sample-set annotations/readiness summary (`--refresh` persists Markdown; Phase 61)
- `make mrms-render-candidate-preflight` generates local render candidate preflight checklist (`--refresh` persists JSON/Markdown; Phase 62)
- `make mrms-render-candidate-dry-run-plan` generates local render candidate dry-run plan (`--refresh` persists JSON/Markdown; Phase 63)
- `make mrms-render-candidate-scaffold` generates local render candidate command scaffold (`--refresh` persists JSON/Markdown; Phase 64)
- `make mrms-render-candidate-sandbox` creates/validates local render candidate artifact sandbox layout (`--refresh` persists manifest/report; Phase 65)
- `make mrms-render-candidate-sandbox-export` exports local candidate sandbox manifest metadata (`--export`; Phase 66)
- `make mrms-render-candidate-sandbox-import-export` exports then validates/imports latest export metadata (`--export --import`; Phase 66)
- `make mrms-render-candidate-sandbox-comparison-history` refreshes local sandbox comparison history summary (`--refresh`; Phase 67)
- `make mrms-render-candidate-sandbox-comparison-trend-hint` refreshes local sandbox comparison trend hints (`--refresh`; Phase 68)
- `make mrms-render-candidate-sandbox-comparison-review-acknowledgment` records local sandbox comparison review acknowledgment (`--operator`, `--note`; Phase 69)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status` refreshes local sandbox comparison acknowledgment status rollup (`--refresh`; Phase 70)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history` refreshes local sandbox comparison acknowledgment status history (`--refresh`; Phase 71)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint` refreshes local sandbox comparison acknowledgment status trend hints (`--refresh`; Phase 72)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment` records local sandbox comparison acknowledgment status trend review acknowledgment (`--operator`, `--note`; Phase 73)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status` refreshes local sandbox comparison acknowledgment status trend review acknowledgment status rollup (`--refresh`; Phase 74)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-history` refreshes local sandbox comparison acknowledgment status trend review acknowledgment status history (`--refresh`; Phase 75)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint` refreshes local sandbox comparison acknowledgment status trend review acknowledgment status trend hints (`--refresh`; Phase 76)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment` records local sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment (`--operator`, `--note`; Phase 77)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status` refreshes local sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status rollup (`--refresh`; Phase 78)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-history` refreshes local sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status history (`--refresh`; Phase 79)
- `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint` refreshes local sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status trend hints (`--refresh`; Phase 80)
- `make mrms-render-candidate-trend-hint-review-acknowledgment` records local candidate trend-hint review acknowledgment (`--operator`, `--note`; Phase 81)
- `make scheduled-proof-bundle-visual-review` runs full scheduled proof/digest/export/operator-status with explicit visual review generation (Phase 59; `--visual-review` opt-in)
- `make mrms-review-session ARGS="... --export-after-create"` creates a session and immediately exports Markdown (session is kept if export fails)
- `make mrms-signoff` records local operator sign-off (does not set verified_mrms)
- `POST /api/validation/signoffs` — dev-only sign-off API (same validation as CLI; does not verify MRMS)
- Dev Validation panel (Phase 51): collapsible detail sections for alerts, proof, digest, review/export/diff/history, scheduled status, and raw JSON — **Operator Review Status** remains the top-level summary; local-only UI polish (no API or verification changes)
- Dev Validation **Proof review & sign-off** collapsible includes sign-off form + scheduled proof-step compact status
- `make real-mrms-smoke-test` runs intentional real-mode smoke test (count 1, zoom 0)
- Operator runbook: [docs/RUNBOOK_REAL_MRMS_VALIDATION.md](docs/RUNBOOK_REAL_MRMS_VALIDATION.md)
- Verified MRMS proof criteria (not met): [docs/VERIFIED_MRMS_CRITERIA.md](docs/VERIFIED_MRMS_CRITERIA.md)
- Operator sign-off template: [docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md)
- `make catalog-status` reports MRMS catalog counts by status
- Dev validation dashboard: summary/history/benchmarks/scheduled APIs + panel with Refresh, collapsible sections, and Show details (raw JSON)
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
