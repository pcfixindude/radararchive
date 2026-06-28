# Next Steps

## Phase 43 - Review Session Export + Digest Tie-In (Draft)

Goal: Optional Markdown export of review session + comparison summary and tighter links to digest regeneration hints — still local-only.

Suggested work:
1. Gitignored Markdown export for latest review session + comparison
2. Surface digest regeneration hints alongside open attention guidance
3. Optional comparison trigger on scheduled digest export

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 42 verification commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test review only' --accepted-limitations"
make mrms-review-sessions
make mrms-review-session-compare
cd frontend && npm run build
```
