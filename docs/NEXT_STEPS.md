# Next Steps

## Phase 34 - Proof Bundle Diff Alert History (Draft)

Goal: Persist compact proof bundle diff status history over scheduled runs and surface trend in Dev Validation — still without `verified_mrms=true`.

Suggested work:
1. Append diff status snapshots to bounded local history JSON on each scheduled diff step
2. Summary API: `proof_bundle_diff_history` compact (last N statuses, attention flags)
3. Dev panel timeline for worsened → improved transitions (local review only)
4. Optional alert auto-clear documentation when diff improves (explicit operator ack, not silent)

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Setting `verified_mrms=true` or production promotion

## Phase 33 verification commands

```bash
make test
make scheduled-validation
make scheduled-proof-bundle
make scheduled-proof-bundle-handoff
make mrms-proof-bundle
make mrms-proof-bundle-diff
make mrms-operator-handoff
make validation-alerts
cd frontend && npm run build
```
