# Next Steps

## Phase 47 - Export Diff Trend Alerts (Draft)

Goal: Optional tie between export diff trends and validation summary hints — still local-only.

Suggested work:
1. Export diff trend regeneration hints when worsening streak persists
2. Optional scheduled validation step to surface export diff trend in report
3. Dev Validation history table for export diff entries

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 46 verification commands

```bash
make test
make mrms-review-session-export-diff-trend
make mrms-review-session-export-diff-trend ARGS="--json"
cd frontend && npm run build
```
