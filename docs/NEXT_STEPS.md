# Next Steps

## Phase 24 - Operator Runbooks + Validation Notifications

Goal: Add local-only operator runbooks for real-MRMS validation, optional log-file notification hooks, and clearer failure triage in the dev panel — still without cloud deployment or verified MRMS claims.

Suggested work:
1. Operator runbook doc for real mode (decoder install, network, expected warnings)
2. Optional local log append on scheduled validation failure (no external services)
3. Dev panel step-level drill-down from scheduled validation report
4. Align batch and queue per-frame metrics when multiple jobs share one worker pass
5. Keep placeholder default for offline dev

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack notifications
- Mandatory GDAL/rasterio/wgrib2

## Phase 23 verification commands

```bash
make test
make scheduled-validation
make benchmark-render-queue
make validate-real-mrms-batch
make catalog-status
make render-queue-status
cd frontend && npm run build
```
