# Next Steps

## Phase 29 - Optional Dev Sign-Off Form + Alert Linkage (Draft)

Goal: Optional dev-only sign-off POST behind explicit flag, refresh alerts when sign-off recorded after regression, and scheduled validation compact proof step in summary API — still without `verified_mrms=true`.

Suggested work:
1. Dev-only `POST /api/validation/signoffs` behind env flag (validated, no promotion)
2. Alert refresh hook when sign-off follows regression
3. Summary `scheduled_validation` includes proof step compact when `--proof` used
4. Proof review panel deep-link to runbook sections

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion via sign-off

## Phase 28 verification commands

```bash
make test
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make validation-alerts
make scheduled-validation
cd frontend && npm run build
```
