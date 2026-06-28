# Next Steps

## Phase 45 - Export Diff + Auto-Export Options (Draft)

Goal: Optional diff between consecutive review session exports and optional auto-export after review session create — still local-only.

Suggested work:
1. Gitignored diff metadata between consecutive review session exports
2. Optional `--review-export` on review session create CLI (off by default)
3. Tie export regeneration hints to scheduled validation history

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/webhooks
- Setting `verified_mrms=true` or production promotion

## Phase 44 verification commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test review only' --accepted-limitations"
make scheduled-proof-bundle-review-export
make mrms-review-session-export
cd frontend && npm run build
```
