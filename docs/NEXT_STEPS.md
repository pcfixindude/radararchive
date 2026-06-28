# Next Steps

## Phase 28 - Proof History Drill-Down + Sign-Off Review UI (Draft)

Goal: Dev panel drill-down for proof/regression history, optional sign-off form in UI (local API POST behind dev flag), and tighter alert ↔ proof linkage — still without `verified_mrms=true`.

Suggested work:
1. Proof/regression history endpoints with bounded entries
2. Optional dev-only sign-off POST (validated, no verified_mrms)
3. Alert refresh when sign-off recorded after regression
4. Scheduled validation report includes proof step summary in API compact view

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion via sign-off

## Phase 27 verification commands

```bash
make test
make mrms-proof-report
make mrms-proof-regression
make validation-alerts
make scheduled-validation ARGS="--proof"
make catalog-status
make render-queue-status
cd frontend && npm run build
```
