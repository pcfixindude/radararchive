# Next Steps

## Phase 36 - Diff Alert Escalation Hints + Runbook Deep Links (Draft)

Goal: Surface escalation hints when trend is worsening with active attention streak, and link trend states to specific runbook sections — still without `verified_mrms=true`.

Suggested work:
1. Trend-based operator guidance items in validation alert
2. Escalation hint when `worsening` trend + acknowledgment stale
3. Dev panel chips for trend state with runbook section labels
4. Optional bounded acknowledgment history in summary API

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion

## Phase 35 verification commands

```bash
make test
make proof-bundle-diff-alert-history
make proof-bundle-diff-alert-trend
make proof-bundle-diff-acknowledge ARGS="--operator TEST --note 'local test acknowledgment only'"
make scheduled-proof-bundle
make validation-alerts
cd frontend && npm run build
```
