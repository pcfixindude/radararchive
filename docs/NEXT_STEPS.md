# Next Steps

## Phase 48 - Export Diff Trend History UI (Draft)

Goal: Optional Dev Validation table for export diff history entries — still local-only.

Suggested work:
1. Expandable export diff history in Dev Validation panel
2. Tie trend hint to review_export_regeneration_hint consolidation
3. Optional scheduled validation flag to surface hint without running export

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 47 verification commands

```bash
make test
make mrms-review-session-export-diff-trend-hint
make mrms-review-session-export-diff-trend-hint ARGS="--json"
make scheduled-proof-bundle-review-export
cd frontend && npm run build
```
