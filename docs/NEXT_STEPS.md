# Next Steps

## Phase 63 - TBD (Draft)

Goal: Gated real MRMS rendering candidate dry-run plan — local documented commands, prerequisites, expected outputs, rollback/safety checks, and evidence requirements without executing download/decode/render work by default.

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 62 verification commands

```bash
make test
make mrms-render-candidate-preflight --refresh
cd frontend && npm test
cd frontend && npm run build
```
