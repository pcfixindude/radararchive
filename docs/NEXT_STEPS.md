# Next Steps

## Phase 67 - TBD (Draft)

Goal: Gated candidate sandbox manifest comparison history — local comparison history for candidate sandbox exports/imports so operators can review changes across candidate artifact reports without touching production tile serving or verifying MRMS.

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 66 verification commands

```bash
make test
make mrms-render-candidate-sandbox-export
make mrms-render-candidate-sandbox-import-export
cd frontend && npm test
cd frontend && npm run build
```
