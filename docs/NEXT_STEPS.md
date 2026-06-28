# Next Steps

## Phase 44 - Scheduled Review Export + Digest Automation (Draft)

Goal: Optional scheduled validation step to export review session summary after digest/handoff — still local-only.

Suggested work:
1. `--review-export` flag on scheduled proof bundle / digest sequence
2. Auto-export after review session create (optional, off by default)
3. Export diff between consecutive Markdown exports

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 43 verification commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test review only' --accepted-limitations"
make mrms-review-session-compare
make mrms-review-session-export
make mrms-review-session-exports
cd frontend && npm run build
```
