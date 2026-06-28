# Next Steps

## Phase 32 - Scheduled Proof Bundle Export + Alert Hooks (Draft)

Goal: Optional scheduled/cron-friendly proof bundle export after validation runs, with alert marker hooks when bundle diff status worsens — still without `verified_mrms=true`.

Suggested work:
1. `scheduled-validation --export-bundle` optional step
2. Alert cause bucket when diff status is `worsened`
3. Handoff checklist auto-regenerate hook after bundle export (local only)

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion

## Phase 31 verification commands

```bash
make test
make mrms-proof-bundle
make mrms-proof-bundle-diff
make mrms-operator-handoff
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make validation-alerts
make scheduled-validation
make catalog-status
make render-queue-status
cd frontend && npm run build
```
