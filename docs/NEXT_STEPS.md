# Next Steps

## Phase 33 - Handoff Auto-Regenerate + Diff Worsened Runbook Links (Draft)

Goal: Auto-regenerate operator handoff checklist after scheduled proof bundle export, and add runbook deep-link anchors for worsened diff remediation — still without `verified_mrms=true`.

Suggested work:
1. Optional `--handoff` flag on `make scheduled-proof-bundle`
2. Dev panel link to runbook “when diff worsens” section
3. Alert history compact for proof bundle diff status over time

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion

## Phase 32 verification commands

```bash
make test
make scheduled-validation
make scheduled-proof-bundle
make mrms-proof-bundle
make mrms-proof-bundle-diff
make validation-alerts
cd frontend && npm run build
```
