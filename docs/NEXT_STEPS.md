# Next Steps

## Phase 62 - TBD (Draft)

Goal: Gated real MRMS rendering candidate preflight — a strictly gated local checklist evaluating readiness to attempt a real MRMS rendering candidate path without enabling production rendering or verifying MRMS.

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 61 verification commands

```bash
make test
make mrms-visual-review-readiness --refresh
cd frontend && npm test
cd frontend && npm run build
```
