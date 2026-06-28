# Next Steps

## Phase 26 - Verified MRMS Proof Automation (Draft)

Goal: Automate checks from [VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md) where possible — checksum recording, multi-frame validation reports, geo sanity assertions — still without setting `verified_mrms=true` or enabling production rendering by default.

Suggested work:
1. Automated checksum + source metadata capture on real download
2. Multi-frame validation report with pass/fail per criterion
3. Geo bounds/CRS assertion helpers (optional decoder)
4. Operator sign-off record template (local JSON)
5. Alert marker integration when criteria regress

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment, email/Slack/PagerDuty
- Setting `verified_mrms=true` without documented operator review phase

## Phase 25 verification commands

```bash
make test
make validation-alerts
make validation-failures
make scheduled-validation
make catalog-status
make render-queue-status
cd frontend && npm run build
```
