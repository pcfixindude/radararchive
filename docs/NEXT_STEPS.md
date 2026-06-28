# Next Steps

## Phase 42 - Review Session Comparison + Runbook Links (Draft)

Goal: Compare review sessions across time and surface runbook deep-links from open attention items — still local-only.

Suggested work:
1. Review session diff between consecutive sessions
2. Dev panel link open attention items to runbook anchors
3. Optional export review session summary Markdown (gitignored)
4. Tie review sessions to scheduled digest regeneration hints

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 41 verification commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test review only' --accepted-limitations"
make mrms-review-sessions
cd frontend && npm run build
```
