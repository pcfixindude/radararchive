# Next Steps

## Phase 30 - Exportable Proof Bundle + Runbook Deep Links (Draft)

Goal: Package proof/regression/sign-off JSON into a single local export artifact for operator handoff, and add runbook deep-link anchors from the dev validation panel — still without `verified_mrms=true`.

Suggested work:
1. `make mrms-proof-bundle` — zip/tar of latest proof, regression, sign-off, alert JSON (local only)
2. Dev panel links to runbook sections (proof, regression, sign-off)
3. Optional `GET /api/validation/proof-bundle` read-only manifest (no secrets)

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion via sign-off or export

## Phase 29 verification commands

```bash
make test
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make validation-alerts
make scheduled-validation
make catalog-status
make render-queue-status
cd frontend && npm run build
```
