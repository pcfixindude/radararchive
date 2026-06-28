# Next Steps

## Phase 46 - Review Export Diff Trends (Draft)

Goal: Optional trend summaries across export diff history — still local-only.

Suggested work:
1. Compact trend metrics from bounded export diff history
2. Tie export diff regeneration hints to scheduled validation history
3. Optional dashboard sparkline or history table in Dev Validation

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 45 verification commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test review only' --accepted-limitations"
make mrms-review-session ARGS="--operator TEST --notes 'local test review with export' --accepted-limitations --export-after-create"
make mrms-review-session-export-diff
make mrms-review-session-export-diff-history
cd frontend && npm run build
```
