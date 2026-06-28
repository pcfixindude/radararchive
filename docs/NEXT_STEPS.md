# Next Steps

## Phase 49 - Review Export History Consolidation (Draft)

Goal: Optional consolidation of export diff history with trend hint regeneration — still local-only.

Suggested work:
1. Tie trend hint to review_export_regeneration_hint consolidation
2. Optional scheduled validation flag to surface hint without running export
3. Link export diff history entries to runbook sections

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 48 verification commands

```bash
make test
make mrms-review-session-export-diff-history
cd frontend && npm run build
```
