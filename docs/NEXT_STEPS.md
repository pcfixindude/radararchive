# Next Steps

## Phase 51 - Dev Validation UX Polish (Draft)

Goal: Optional collapsible detail sections in Dev Validation panel — still local-only.

Suggested work:
1. Collapse/expand toggles for detailed review/export/diff/history blocks
2. Link scheduled operator status causes to runbook anchors in UI
3. Optional scheduled validation flag to surface operator status without review export

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 50 verification commands

```bash
make test
make operator-review-status
make scheduled-proof-bundle-operator-status
cd frontend && npm run build
```
