# Real MRMS Validation Runbook (Dev/Prototype)

This runbook explains how to run, inspect, and troubleshoot the **experimental** MRMS validation pipeline in RadarArchive.

**Important:** All validation output is prototype tooling. `verified_mrms` remains **false**. This is **not** verified production radar.

Future proof criteria (not met today): **[VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md)**.

## What the pipeline does

1. **Discover/register** MRMS catalog candidates (stub or real NOAA AWS)
2. **Download** pending frames (real mode only, when configured)
3. **Inspect/decode** `.grib2.gz` when optional decoders exist
4. **Build prototype tiles** (warping math; not production-verified)
5. **Enqueue/process** render jobs via local SQLite queue (no Redis/Celery)
6. **Persist dev reports** under `data/dev/`

Default map serving remains **placeholder tiles** unless feature flags and catalog gates are explicitly enabled.

## Prerequisites for full real validation

| Requirement | Purpose |
|-------------|---------|
| Network access | Download NOAA MRMS from AWS in `real` mode |
| `MRMS_SOURCE_MODE=real` or `--real` | Intentional real mode (never default) |
| Optional decoder (wgrib2 / rasterio / GDAL) | Inspect and decode real GRIB2 |
| Local disk | Raw downloads + decode artifacts + tile cache |
| `ENABLE_PRODUCTION_RADAR_TILES=false` (default) | Production serving stays off |

Without a decoder, real downloads may succeed but decode/tile steps will warn and write **0 tiles**.

## Stub validation (safe, offline default)

```bash
make validate-real-mrms-batch
make benchmark-render-queue
make scheduled-validation
make catalog-status
make render-queue-status
```

Stub mode uses offline catalog fixtures. Expect warnings about non-real GRIB2 and zero decoded frames — that is normal.

## Real one-frame smoke test (intentional, limited)

```bash
make real-mrms-smoke-test
# equivalent limits: --real, count=1, zoom 0 only, mark_catalog=false
```

Or via scheduled validation:

```bash
make scheduled-validation ARGS="--real --count 1 --min-zoom 0 --max-zoom 0"
```

**Warnings:** May download NOAA MRMS data. Still prototype — not verified MRMS.

## Scheduled validation (cron-friendly)

```bash
make scheduled-validation
make scheduled-validation ARGS="--json-report"
make scheduled-validation ARGS="--real --count 3 --min-zoom 0 --max-zoom 1"
```

Sample cron (not installed automatically):

```cron
0 */6 * * * cd /path/to/radararchive && make scheduled-validation >> data/dev/scheduled_validation.log 2>&1
```

Exit code: **0** success, **1** failure (suitable for cron monitoring).

## Check dashboard / API status

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/latest
curl http://127.0.0.1:8000/api/validation/scheduled
curl http://127.0.0.1:8000/api/validation/failures
curl http://127.0.0.1:8000/api/validation/alerts
curl http://127.0.0.1:8000/api/catalog/status
```

Frontend: Dev Validation panel shows alert status, grouped failure causes, suggested next action, scheduled steps, failure count, and **Show details** JSON drill-down.

## Check validation alerts

```bash
make validation-alerts
make validation-alerts ARGS="--refresh"
make validation-alerts ARGS="--json"
```

Alert file: `data/dev/validation_alert_latest.json` (local dev only; rebuilt after scheduled validation).

## Generate draft proof report

```bash
make mrms-proof-report
make mrms-proof-report ARGS="--json-report"
make mrms-proof-report ARGS="--real --count 3"
```

Proof file: `data/dev/mrms_proof_latest.json` — draft evidence only, **not verified MRMS**.

Operator sign-off template: [MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](MRMS_OPERATOR_SIGNOFF_TEMPLATE.md) — completing sign-off does **not** set `verified_mrms=true`.

```bash
curl http://127.0.0.1:8000/api/validation/proof
curl http://127.0.0.1:8000/api/validation/proof-regression
curl http://127.0.0.1:8000/api/validation/signoffs
curl http://127.0.0.1:8000/api/validation/proof/history
curl http://127.0.0.1:8000/api/validation/proof-regression/history
```

## Proof regression and sign-off (Phase 27)

```bash
make mrms-proof-regression
make mrms-proof-regression ARGS="--refresh-alert"
make mrms-signoff ARGS="--initials OP --notes 'reviewed draft proof' --accepted-limitations 'prototype only'"
make scheduled-validation ARGS="--proof"
```

Regression file: `data/dev/mrms_proof_regression_latest.json`. Sign-offs: `data/dev/mrms_signoffs.json`.

**Sign-off does not set `verified_mrms=true` or enable production rendering.**

## Proof review history UI (Phase 28)

```bash
make mrms-proof-history
make mrms-proof-history ARGS="--regression"
make mrms-proof-history ARGS="--signoffs"
```

Dev Validation panel: **Show proof review** — proof history, regression history, sign-off list (local only, not verified MRMS).

## Dev sign-off form and API (Phase 29)

Dev-only operator review — **does not verify MRMS** and **does not enable production rendering**.

```bash
# CLI (refreshes alert marker after sign-off)
make mrms-signoff ARGS="--initials OP --notes 'reviewed draft proof' --accepted-limitations 'prototype only'"

# API (dev/local only)
curl -X POST http://127.0.0.1:8000/api/validation/signoffs \
  -H 'Content-Type: application/json' \
  -d '{"operator_initials":"OP","operator_notes":"local review only"}'
```

Dev Validation panel: **Show proof review** → dev sign-off form with honest local-only wording.

After sign-off:
- Validation alert refreshes with `latest_signoff_at`
- If proof regression was active, it **remains active** until evidence improves (sign-off records review only)
- Summary shows `scheduled_validation.proof_step` when scheduled validation ran with `--proof`

## Proof bundle export (Phase 30)

Package local proof evidence for operator handoff — **does not verify MRMS** and **does not enable production rendering**.

```bash
make mrms-proof-bundle
make mrms-proof-bundle ARGS="--json-report"
make mrms-proof-bundle ARGS="--include-history"
curl http://127.0.0.1:8000/api/validation/proof-bundles
```

Output:
- Folder: `data/dev/proof_bundles/mrms_proof_bundle_{timestamp}/`
- ZIP: `data/dev/proof_bundles/mrms_proof_bundle_{timestamp}.zip`
- Manifest: `manifest.json` inside bundle (`verified_mrms: false`, `files_included`, `files_missing`)
- README inside bundle explains non-verification warnings
- Runbook copies: `docs/RUNBOOK_REAL_MRMS_VALIDATION.md`, `docs/VERIFIED_MRMS_CRITERIA.md`, etc. (when present in repo)

Dev Validation panel shows latest bundle path and runbook doc references.

## Proof bundle diff + operator handoff (Phase 31)

Compare bundles and generate a local review checklist — **does not verify MRMS**.

```bash
make mrms-proof-bundle-diff
make mrms-proof-bundle-diff ARGS="--json-report"
make mrms-operator-handoff
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff?refresh=true
curl http://127.0.0.1:8000/api/validation/operator-handoff
```

**Diff overall status meanings (local review only):**
- `no_baseline` — fewer than two bundles exported; run `make mrms-proof-bundle` twice first
- `unchanged` — key proof/regression/alert metrics match between bundles
- `improved` — evidence signals moved in a positive direction (e.g. fewer failed criteria, regression cleared)
- `worsened` — evidence signals degraded (e.g. regression detected, alert status worse)
- `mixed` — some signals improved and others worsened
- `unknown` — insufficient evidence files to classify

Handoff output: `data/dev/mrms_operator_handoff_latest.md` (checklist with explicit non-verification statements).

Generated bundle/diff/handoff artifacts are gitignored under `data/dev/`.

## Scheduled proof bundle monitoring (Phase 32)

Run proof report, bundle export, and diff in one scheduled local flow — **does not verify MRMS**.

```bash
make scheduled-proof-bundle
make scheduled-proof-bundle ARGS="--json-report"
make scheduled-validation ARGS="--proof --bundle --diff-bundle"
```

When proof bundle diff status is **worsened** or **mixed**:
- Validation alert sets `operator_attention_needed` and adds `proof_bundle_diff_worsened` cause
- Review `make mrms-proof-bundle-diff` output and compare bundle `evidence/` JSON
- Re-run `make mrms-proof-report` after fixes, then `make scheduled-proof-bundle` again
- Improving diff status does **not** silently clear unrelated validation failures — review `make validation-failures`

Alert fields: `proof_bundle_diff_status`, `latest_proof_bundle_id`, `latest_proof_bundle_created_at`.

## Scheduled handoff auto-regeneration (Phase 33)

Optional `--handoff` on scheduled proof bundle monitoring — **does not verify MRMS**.

```bash
make scheduled-proof-bundle-handoff
make scheduled-proof-bundle-handoff ARGS="--json-report"
make scheduled-validation ARGS="--proof --bundle --diff-bundle --handoff"
```

When diff status is **worsened** or **mixed** and `--handoff` is set, the operator handoff checklist is regenerated with diff context and runbook references. Unchanged/improved/no_baseline skips handoff with a recorded reason (not a failure).

## Proof bundle diff alert history (Phase 34)

Bounded timeline of proof bundle diff alert states — **does not verify MRMS**.

```bash
make proof-bundle-diff-alert-history
make proof-bundle-diff-alert-history ARGS="--json"
make proof-bundle-diff-alert-history ARGS="--limit 5"
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-alert-history
```

History is recorded automatically when:
- `make mrms-proof-bundle-diff` runs
- `make scheduled-proof-bundle` or `make scheduled-proof-bundle-handoff` runs diff step

Persisted to `data/dev/proof_bundle_diff_alert_history.json` (last 25 entries, gitignored).

**Interpreting status over time (local monitoring only):**
- `worsened` — evidence degraded vs baseline bundle; operator attention likely needed
- `mixed` — some signals improved, some worsened; triage each change
- `improved` — evidence moved positively; does **not** auto-clear unrelated alerts
- `unchanged` — key metrics match; monitor for drift on next export
- `no_baseline` — fewer than two bundles; export twice before trend analysis
- `unknown` — insufficient evidence files

Timeline history does **not** verify MRMS, enable production rendering, or mutate catalog gates.

## Proof bundle diff alert trend + acknowledgment (Phase 35)

Trend summary and optional local operator acknowledgment — **does not verify MRMS** or clear alerts silently.

```bash
make proof-bundle-diff-alert-trend
make proof-bundle-diff-alert-trend ARGS="--json"
make proof-bundle-diff-acknowledge ARGS="--operator OP --note 'Reviewed worsened diff locally'"
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-alert-trend
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-acknowledgments
curl -X POST http://127.0.0.1:8000/api/validation/proof-bundle-diff-acknowledgments \
  -H 'Content-Type: application/json' \
  -d '{"operator_initials":"OP","note":"local acknowledgment only"}'
```

**Trend values (local monitoring only):**
- `worsening` — recent worsened signals dominate or attention streak active
- `improving` — recent improved signals exceed worsened
- `mixed` — mixed diff statuses in recent window
- `stable` — mostly unchanged
- `no_data` — no diff alert history yet

**Acknowledgment means:**
- Operator recorded a local review note tied to latest diff context
- Does **not** clear validation alerts, proof regressions, or production gates
- Does **not** set `verified_mrms=true` or enable production rendering
- Alert may remain active after acknowledgment (`diff_alert_acknowledged_but_still_active`)

Acknowledgments persist to `data/dev/proof_bundle_diff_acknowledgments.json` (gitignored, max 50).

## Proof bundle diff escalation history + stdout urgent notice (Phase 37)

Bounded escalation snapshots and optional **local terminal stdout** urgent notices — **does not verify MRMS**, clear alerts, enable production rendering, or send external notifications.

```bash
make proof-bundle-diff-escalation
make proof-bundle-diff-escalation-history
make proof-bundle-diff-escalation-history ARGS="--json"
make scheduled-proof-bundle-notify
make scheduled-proof-bundle ARGS="--notify-stdout"
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-history
```

**Escalation history:**
- Recorded when running `make proof-bundle-diff-escalation` and scheduled proof bundle diff steps
- Persisted to `data/dev/proof_bundle_diff_escalation_history.json` (gitignored, max 25)
- Duplicate exact snapshots in the same run are skipped

**Stdout urgent notice (`--notify-stdout` / `--urgent-stdout`):**
- Only prints when escalation level is **urgent**
- Header: `URGENT LOCAL VALIDATION NOTICE`
- Includes reason, suggested action, runbook path/section
- States `verified_mrms: false` and production rendering status
- **Local terminal only** — no email, SMS, Slack, webhooks, or push notifications
- Latest notice metadata: `data/dev/proof_bundle_diff_escalation_stdout_latest.json` (gitignored)

<a id="proof-bundle-diff-escalation-stdout-urgent"></a>

**What urgent stdout notice means:** Operator should review escalation history and runbook guidance immediately in the local dev environment. The notice is a review aid only — it does **not** verify MRMS, clear alerts, or enable production rendering.

## Proof bundle diff escalation metrics + digest (Phase 38)

Trend metrics and optional local Markdown digest export — **local review only**, not a notification system.

```bash
make proof-bundle-diff-escalation-metrics
make proof-bundle-diff-escalation-metrics ARGS="--json"
make proof-bundle-diff-escalation-digest
make proof-bundle-diff-escalation-digest ARGS="--json-report"
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-metrics
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest
```

**Interpreting streaks:**
- `current_urgent_streak` — consecutive urgent snapshots from latest history entry backward
- `current_attention_or_urgent_streak` — consecutive attention or urgent snapshots from latest backward
- `longest_*` — maximum consecutive run across full bounded history (oldest → newest)

**Digest export:**
- Writes `data/dev/proof_bundle_diff_escalation_digest_latest.md` + `.json` (gitignored)
- Includes metrics, recent snapshots, acknowledgment, guidance, validation alert status
- Does **not** verify MRMS, clear alerts, enable production rendering, or send external notifications

## Scheduled proof bundle digest + operator review checklist (Phase 39)

Optional one-shot local/dev sequence: proof report → bundle export → diff → handoff → escalation evaluation → digest export → extended operator checklist.

```bash
make scheduled-proof-bundle-digest
make scheduled-proof-bundle-digest ARGS="--json-report"
# Equivalent flags:
# python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle --handoff --digest
```

**When to use:**
- After repeated worsened/mixed diff alerts or urgent escalation streaks
- When you want a single local run that refreshes proof bundle evidence, diff, escalation digest, and operator checklist
- Before a local operator review session (not before production launch)

**Operator checklist covers:**
- Latest proof bundle and diff status
- Escalation metrics and current escalation level
- Latest acknowledgment status (current / stale / missing)
- Recent validation failures and decoder availability
- Tile write counts from batch/queue steps when present
- Explicit checklist items (review bundle, diff, metrics, failures, decoder, tiles, production disabled, `verified_mrms` false, record acknowledgment/sign-off)
- Runbook guidance links from validation alert

**Warnings:**
- Digest and checklist are **local review evidence only**
- They do **not** verify MRMS, clear validation alerts, enable production rendering, or send external notifications
- Default `make scheduled-validation` is unchanged (no digest unless `--digest` / `make scheduled-proof-bundle-digest`)

Summary API adds `scheduled_digest` compact (`digest_requested`, `digest_generated`, `digest_path`, `digest_reason`, …). `operator_handoff` compact adds escalation review fields when checklist was regenerated with `--digest`.

## Digest export history + diff + regeneration hints (Phase 40)

Bounded digest export history, diff metadata between consecutive exports, and Dev Validation regeneration hints — **local review only**.

```bash
make proof-bundle-diff-escalation-digest-history
make proof-bundle-diff-escalation-digest-history ARGS="--json"
make proof-bundle-diff-escalation-digest-diff
make proof-bundle-diff-escalation-digest-diff ARGS="--json"
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest-history
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation-digest-diff
```

**Digest history:**
- `data/dev/proof_bundle_diff_escalation_digest_history.json` (gitignored, max 25)
- Recorded automatically on each `make proof-bundle-diff-escalation-digest` or scheduled digest export

**Digest diff:**
- Compares latest export vs previous export metadata
- `overall_digest_diff_status`: `no_baseline`, `unchanged`, `improved`, `worsened`, `mixed`, `unknown`
- Persisted to `proof_bundle_diff_escalation_digest_diff_latest.json` + bounded diff history

**When to regenerate digest/checklist:**
- Urgent escalation and no digest exported yet
- Latest digest older than latest escalation snapshot
- Attention/urgent streak ≥ 2 with stale digest
- Digest diff status `worsened` or `mixed`
- Suggested command: `make scheduled-proof-bundle-digest`

**Warnings:** Digest history/diff/hints do **not** verify MRMS, clear alerts, or enable production rendering.

## MRMS proof review sessions (Phase 41)

Local review session records link escalation snapshot, digest export, operator handoff, acknowledgment, proof bundle, diff, and proof report metadata — **local operator evidence only**.

```bash
make mrms-review-session ARGS="--operator TEST --notes 'reviewed local digest only' --accepted-limitations"
make mrms-review-session ARGS="--json --operator TEST --notes 'review notes' --accepted-limitations"
make mrms-review-sessions
make mrms-review-sessions ARGS="--json"
curl http://127.0.0.1:8000/api/validation/review-sessions
curl -X POST http://127.0.0.1:8000/api/validation/review-sessions \
  -H 'Content-Type: application/json' \
  -d '{"operator_initials":"API","session_notes":"local review","accepted_limitations":true}'
```

**What a review session means:**
- A timestamped local record of what evidence the operator reviewed (digest path, handoff path, bundle/diff status, escalation level)
- Captures open attention items still needing follow-up at review time
- Optional checklist items marked reviewed vs not reviewed
- Does **not** certify verified MRMS or replace sign-off

**Dev Validation UI:**
- Summary shows latest session operator, escalation level, open attention count
- Optional form: operator, notes, accepted limitations checkbox
- Refresh reloads summary after submit

**Warnings:** Review sessions do **not** verify MRMS, clear validation alerts, enable production rendering, or send external notifications.

## Proof bundle diff alert escalation (Phase 36)

Escalation hints combine trend summary, diff alert history, and acknowledgment state — **local operator guidance only**. Escalation does **not** verify MRMS, clear alerts, enable production rendering, or mutate catalog gates.

```bash
make proof-bundle-diff-escalation
make proof-bundle-diff-escalation ARGS="--json"
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-escalation
```

**Escalation levels:**
- `none` — no history, stable/unchanged, or no attention needed
- `watch` — first worsened/mixed signal, or no acknowledgment yet
- `attention` — worsened/mixed for **2+** consecutive attention-needed entries
- `urgent` — worsened/mixed for **3+** consecutive attention entries **and** no current acknowledgment

<a id="proof-bundle-diff-escalation-watch"></a>

**Watch:** Review latest diff alert timeline entry and trend summary. Record a local acknowledgment if you have reviewed evidence — acknowledgment does not clear alerts.

<a id="proof-bundle-diff-escalation-attention"></a>

**Attention:** Two or more consecutive worsened/mixed diff alerts. Compare bundle evidence, re-run `make scheduled-proof-bundle`, and refresh acknowledgment with notes if review is complete.

<a id="proof-bundle-diff-escalation-urgent"></a>

**Urgent:** Three or more consecutive attention-needed alerts without a current acknowledgment. Prioritize bundle diff review and runbook sections linked in Dev Validation escalation guidance.

<a id="proof-bundle-diff-stale-acknowledgment"></a>

**Stale acknowledgment** means the latest acknowledgment was created **before** the latest worsened/mixed diff alert, or the attention streak continued **after** the acknowledgment. Submit a new local acknowledgment after re-review — this still does **not** clear alerts or set `verified_mrms=true`.

## Proof bundle diff worsened

<a id="proof-bundle-diff-worsened"></a>

When scheduled or manual diff reports `overall_diff_status: worsened`:

1. Run `make mrms-proof-bundle-diff ARGS="--json-report"` and inspect `evidence_changes`
2. Compare `evidence/mrms_proof_latest.json` and regression JSON between bundles
3. Re-run `make mrms-proof-report` after fixes, then `make scheduled-proof-bundle-handoff`
4. Review validation alert `operator_guidance` in Dev Validation panel or `GET /api/validation/summary`
5. Handoff auto-regeneration does **not** clear alerts or set `verified_mrms=true`

## Proof bundle diff mixed

<a id="proof-bundle-diff-mixed"></a>

When diff status is **mixed** (some evidence improved, some worsened):

1. Triage each `evidence_changes` entry — do not assume overall improvement
2. Run `make scheduled-proof-bundle-handoff` after intentional fixes to refresh handoff
3. Review grouped failure causes alongside diff status
4. Mixed diff still requires operator attention — not verified MRMS

## No decoder available

<a id="no-decoder-available"></a>

When validation reports decoder unavailable (no wgrib2/GDAL/rasterio):

1. Run `make inspect-grib2` to see detected tools
2. Install optional decoder locally if real decode is required
3. Expect stub/offline validation to skip full decode — this is normal without optional tools
4. See [GRIB2_DECODE.md](GRIB2_DECODE.md) for optional install notes

## Zero tiles written

<a id="zero-tiles-written"></a>

When batch/queue benchmarks report zero tiles written:

1. Confirm decode artifacts exist (`make decode-grib2` after real download)
2. Lower zoom/count for prototype runs (`--min-zoom 0 --max-zoom 0`)
3. Stub mode may legitimately write zero production tiles — check `placeholder_default`
4. Review `make validation-failures` for the specific step message

## Production flag off

<a id="production-flag-off"></a>

Default: `ENABLE_PRODUCTION_RADAR_TILES=false`. Placeholder tiles are served.

1. This is expected by default — not a validation failure
2. Enable production serving only with explicit ops intent
3. Handoff/guidance reminders do **not** enable production rendering
4. Tile responses include `x-radararchive-production-rendering: false` when flag is off

## Catalog gate missing

<a id="catalog-gate-missing"></a>

When catalog status shows frames without production render gate satisfied:

1. Run `make catalog-status` and `make render-queue-status`
2. Build production tiles when intentional: `make build-production-tiles`
3. Production tile **serving** still requires `ENABLE_PRODUCTION_RADAR_TILES=true` plus cached tiles
4. Proof bundle / handoff workflows do not mutate catalog gates

## What to do before sign-off

<a id="what-to-do-before-sign-off"></a>

Before `make mrms-signoff` (local review record only):

1. Review latest proof report and regression (`make mrms-proof-regression`)
2. Resolve or acknowledge proof bundle diff if `operator_attention_needed`
3. Read [VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md) — criteria are **not** met in prototype
4. Confirm `verified_mrms` remains false and production flag state is intentional
5. Sign-off does **not** verify MRMS or enable production rendering

## Check recent failures

```bash
make validation-failures
make validation-failures ARGS="--limit 20"
make validation-failures ARGS="--json"
```

Log file: `data/dev/validation_failures.jsonl` (append-only, bounded to last 100 entries).

## Common failure causes

| Symptom | Likely cause | What to check |
|---------|--------------|---------------|
| Discovery/download errors | No network or AWS unreachable | Run stub mode first; verify network |
| `decoder unavailable` | No wgrib2/GDAL/rasterio | `make inspect-grib2`; install optional tools |
| No inspectable GRIB2 | Stub downloads or missing files | `MRMS_SOURCE_MODE=real make download-mrms` |
| Zero tiles written | No decode artifacts or zoom too high | `make decode-grib2`; lower zoom/count |
| Production tiles not served | Flag off (default) | `ENABLE_PRODUCTION_RADAR_TILES` + catalog gate + cached tile |
| Queue jobs failed | Missing artifacts or worker error | `make render-queue-status`; `make validation-failures` |
| `verified_mrms: false` | Always (by design) | Not a failure — prototype only |

## What success looks like (prototype)

- Scheduled validation **exit code 0**
- Steps show `succeeded` or `warning` (warnings are expected in stub mode)
- Catalog counts update in summary/API
- Optional: decoded frames and tiles written when decoder + real files exist

## What does NOT count as verified production MRMS

- Tiles built by prototype warping pipeline
- Queue benchmark or batch validation reports
- `production_rendering_enabled: false` (default)
- Any report with `verified_mrms: false` (all dev reports)
- Serving production-prototype tiles without explicit ops review and future validation phase

See **[VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md)** for the full checklist required before `verified_mrms` could ever become true.

## Verification commands

```bash
make test
make mrms-proof-report
make validation-alerts
make scheduled-validation
make validation-failures
make catalog-status
make render-queue-status
cd frontend && npm run build
```
