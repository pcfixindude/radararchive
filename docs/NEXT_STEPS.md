# Next Steps

## Phase 65 - TBD (Draft)

Goal: Gated candidate artifact sandbox layout — local sandbox directory layout and cleanup/reporting workflow for future real MRMS candidate artifacts, isolated from production tile serving and disabled by default.

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 64 verification commands

```bash
make test
make mrms-render-candidate-scaffold --refresh
cd frontend && npm test
cd frontend && npm run build
```
