# Next Steps

## Phase 40 - Digest History + Regeneration Hints (Draft)

Goal: Optional bounded digest export history and Dev Validation hints when metrics show urgent streak — still local-only, no external notifications, no `verified_mrms=true`.

Suggested work:
1. Bounded digest history (last 5 exports, gitignored)
2. Digest diff between consecutive exports (metadata only)
3. Dev panel regeneration hint when `current_urgent_streak` exceeds threshold
4. Link digest history from operator checklist

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 39 verification commands

```bash
make test
make scheduled-proof-bundle-digest
make proof-bundle-diff-escalation-digest
make scheduled-validation
make validation-alerts
cd frontend && npm run build
```
