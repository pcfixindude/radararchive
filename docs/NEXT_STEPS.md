# Next Steps

## Phase 37 - Escalation Notification Hooks + Bounded Escalation History (Draft)

Goal: Optional bounded persistence of escalation snapshots over time and lightweight notification hooks (stdout/email stub) for urgent levels — still without `verified_mrms=true` or production promotion.

Suggested work:
1. Bounded escalation history JSON (gitignored) on scheduled validation
2. Optional `--notify-urgent` flag on escalation script (stdout only by default)
3. Summary API: latest escalation history entries
4. Dev panel: escalation history show/hide toggle

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion
- Auto-clearing alerts when escalation improves

## Phase 36 verification commands

```bash
make test
make proof-bundle-diff-alert-history
make proof-bundle-diff-alert-trend
make proof-bundle-diff-escalation
make proof-bundle-diff-acknowledge ARGS="--operator TEST --note 'local test acknowledgment only'"
make scheduled-validation
make scheduled-proof-bundle
make scheduled-proof-bundle-handoff
make validation-alerts
cd frontend && npm run build
```
