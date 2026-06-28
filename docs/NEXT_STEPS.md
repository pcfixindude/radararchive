# Next Steps

## Phase 35 - Diff Alert Trend Summary + Operator Ack (Draft)

Goal: Add compact trend summary over diff alert history (worsened→improved transitions, attention streaks) and optional explicit operator acknowledgment notes — still without `verified_mrms=true`.

Suggested work:
1. Trend compact on summary API (`attention_streak`, `last_improved_at`, `status_changes_count`)
2. Optional local ack record when operator reviews worsened/mixed timeline (does not clear alerts automatically)
3. Dev panel trend chips alongside timeline list
4. Runbook note: improving diff status requires evidence review, not silent alert clear

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion

## Phase 34 verification commands

```bash
make test
make proof-bundle-diff-alert-history
make scheduled-validation
make scheduled-proof-bundle
make scheduled-proof-bundle-handoff
make mrms-proof-bundle
make mrms-proof-bundle-diff
make validation-alerts
cd frontend && npm run build
```
