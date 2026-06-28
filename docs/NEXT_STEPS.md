# Next Steps

## Phase 61 - TBD (Draft)

Goal: Visual sample-set review annotations and candidate readiness scoring — local operator notes on selected samples plus a readiness summary for a later gated real MRMS rendering candidate path.

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 60 verification commands

```bash
make test
make mrms-visual-review-sample-set
cd frontend && npm test
cd frontend && npm run build
```
