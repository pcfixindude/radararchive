# Next Steps

## Phase 31 - Proof Bundle Diff + Operator Handoff Checklist (Draft)

Goal: Compare two local proof bundles for operator handoff and add a printable checklist tied to `VERIFIED_MRMS_CRITERIA.md` — still without `verified_mrms=true`.

Suggested work:
1. `make mrms-proof-bundle-diff` — compare manifests and key evidence between two bundle folders
2. Operator handoff checklist markdown generated inside bundle export
3. Dev panel link to latest bundle README path

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion via bundle export

## Phase 30 verification commands

```bash
make test
make mrms-proof-bundle
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make validation-alerts
make scheduled-validation
make catalog-status
make render-queue-status
cd frontend && npm run build
```
