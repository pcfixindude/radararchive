# Next Steps

## Phase 25 - Validation Alerting Hooks + Deeper Real-MRMS Proof Criteria

Goal: Add optional local-only alert hooks (log file markers only), document explicit proof criteria for a future `verified_mrms` phase, and improve failure triage grouping in the dev panel — still without cloud deployment or verified MRMS claims.

Suggested work:
1. Failure grouping by step/phase in dev panel
2. Optional `data/dev/validation_alert.marker` on scheduled failure (local only)
3. Draft proof checklist for future verified MRMS phase (docs only)
4. Link runbook sections from dev panel help text
5. Keep placeholder default for offline dev

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/PagerDuty
- Setting `verified_mrms=true` without documented proof phase

## Phase 24 verification commands

```bash
make test
make scheduled-validation
make validation-failures
make catalog-status
make render-queue-status
cd frontend && npm run build
```
