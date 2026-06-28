# Project State

Current phase: Phase 34 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with optional `--proof`, `--bundle`, `--diff-bundle`, `--handoff`
- **Proof bundle diff alert history** — bounded local timeline of diff alert states
- **Operator guidance** runbook links when validation attention is needed
- **Exportable local MRMS proof bundles** and operator handoff checklist
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 34)

```bash
make scheduled-validation
make scheduled-proof-bundle
make scheduled-proof-bundle-handoff
make mrms-proof-bundle
make mrms-proof-bundle-diff
make proof-bundle-diff-alert-history
make mrms-operator-handoff
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff-alert-history
curl http://127.0.0.1:8000/api/validation/operator-handoff
```

Summary includes `proof_bundle_diff_alert`, `proof_bundle_diff_alert_history` (last 5), and alert timeline count fields.

## Verified MRMS

`verified_mrms` is **false** everywhere. Diff alert history is local evidence monitoring only.
