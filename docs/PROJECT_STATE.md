# Project State

Current phase: Phase 33 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Scheduled validation** with optional `--proof`, `--bundle`, `--diff-bundle`, `--handoff`
- **Operator guidance** runbook links when validation attention is needed
- **Scheduled handoff auto-regeneration** when diff is worsened/mixed (explicit `--handoff` only)
- **Exportable local MRMS proof bundles** and operator handoff checklist
- **Default tile serving: placeholder**
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Operator commands (Phase 33)

```bash
make scheduled-validation
make scheduled-proof-bundle
make scheduled-proof-bundle-handoff
make mrms-proof-bundle
make mrms-proof-bundle-diff
make mrms-operator-handoff
make validation-alerts
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/proof-bundle-diff?refresh=true
curl http://127.0.0.1:8000/api/validation/operator-handoff
```

Summary includes `operator_guidance`, `scheduled_proof_bundle` handoff fields, and extended `operator_handoff` status from latest scheduled run.

## Verified MRMS

`verified_mrms` is **false** everywhere. Operator guidance and handoff are review aids only.
