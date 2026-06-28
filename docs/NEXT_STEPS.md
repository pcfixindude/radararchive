# Next Steps

## Phase 64 - TBD (Draft)

Goal: Gated real MRMS rendering candidate command scaffold — explicitly disabled-by-default command scaffold with hard safety gates, dry-run-only default behavior, and no production tile serving.

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 63 verification commands

```bash
make test
make mrms-render-candidate-dry-run-plan --refresh
cd frontend && npm test
cd frontend && npm run build
```
