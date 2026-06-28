# Next Steps

## Phase 39 - Escalation Digest Scheduling + Operator Review Checklist (Draft)

Goal: Optional scheduled digest regeneration after proof bundle runs and a lightweight operator review checklist tied to digest metrics — still without `verified_mrms=true` or external notifications.

Suggested work:
1. `--digest` flag on scheduled proof bundle (local file only)
2. Digest diff between exports (gitignored metadata)
3. Dev panel: digest regeneration hint when metrics show urgent streak
4. Optional bounded digest history (last 5 exports)

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 38 verification commands

```bash
make test
make proof-bundle-diff-escalation-metrics
make proof-bundle-diff-escalation-digest
make proof-bundle-diff-escalation-history
make scheduled-proof-bundle-notify
cd frontend && npm run build
```
