# Next Steps

## Phase 38 - Escalation History Trend Charts + Operator Digest Export (Draft)

Goal: Summarize escalation history into simple trend metrics (urgent/attention counts over time) and optional local markdown digest export — still without `verified_mrms=true` or external notifications.

Suggested work:
1. Escalation history digest script (`--markdown` export to gitignored path)
2. Summary API: escalation level counts over recent window
3. Dev panel: compact urgent/attention count chips
4. Optional weekly operator digest Makefile target (stdout/file only)

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 37 verification commands

```bash
make test
make proof-bundle-diff-escalation
make proof-bundle-diff-escalation-history
make proof-bundle-diff-acknowledge ARGS="--operator TEST --note 'local test acknowledgment only'"
make scheduled-proof-bundle
make scheduled-proof-bundle-notify
make validation-alerts
cd frontend && npm run build
```
