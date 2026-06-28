# Next Steps

## Phase 41 - Operator Digest Review Sessions (Draft)

Goal: Lightweight local “review session” records tying digest export, checklist acknowledgment, and escalation snapshot — still no external notifications, no `verified_mrms=true`.

Suggested work:
1. Optional local review session JSON (gitignored) linking digest path + operator note
2. Dev panel link from regeneration hint to runbook section
3. Bounded review session history (last 10)
4. Compare review sessions across digest exports

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 40 verification commands

```bash
make test
make proof-bundle-diff-escalation-digest-history
make proof-bundle-diff-escalation-digest-diff
make proof-bundle-diff-escalation-digest
make scheduled-proof-bundle-digest
cd frontend && npm run build
```
