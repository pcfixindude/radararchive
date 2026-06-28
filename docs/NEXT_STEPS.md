# Next Steps

## Phase 27 - Proof Report Regression Hooks + Sign-Off Persistence (Draft)

Goal: Persist completed operator sign-offs locally, tie proof report regressions to validation alerts, and add optional proof-report step to scheduled validation — still without `verified_mrms=true` or production rendering by default.

Suggested work:
1. Optional `data/dev/mrms_operator_signoff.json` record (local only)
2. Alert marker refresh when proof `overall_status` regresses
3. Optional scheduled-validation `--proof` flag (stub default)
4. Dev panel link to sign-off template and latest proof JSON
5. Proof history drill-down in validation latest API

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/PagerDuty
- Setting `verified_mrms=true` without documented launch review phase

## Phase 26 verification commands

```bash
make test
make mrms-proof-report
make validation-alerts
make scheduled-validation
make catalog-status
make render-queue-status
cd frontend && npm run build
```
