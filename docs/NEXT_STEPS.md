# Next Steps

## Phase 66 - TBD (Draft)

Goal: Gated candidate sandbox manifest import/export — local import/export support for candidate sandbox manifests and reports so future candidate artifacts can be reviewed, archived, and compared without touching production tile serving or verifying MRMS.

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 65 verification commands

```bash
make test
make mrms-render-candidate-sandbox --refresh
cd frontend && npm test
cd frontend && npm run build
```
