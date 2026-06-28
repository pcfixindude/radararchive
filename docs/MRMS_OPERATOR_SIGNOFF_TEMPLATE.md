# MRMS Operator Sign-Off Template (Draft)

Use this template when reviewing a **draft proof report** from `make mrms-proof-report`.

**Important:** Completing this sign-off does **NOT** set `verified_mrms=true` anywhere in code, APIs, or reports. It records human review of prototype evidence only.

## Report reference

| Field | Value |
|-------|-------|
| Proof report generated at | _(from `data/dev/mrms_proof_latest.json` → `generated_at`)_ |
| Overall proof status | _(e.g. `insufficient_evidence`, `ready_for_operator_review`)_ |
| Source mode | _(stub / real)_ |
| Frames evaluated | _(count)_ |
| Proof report path | `data/dev/mrms_proof_latest.json` |
| Criteria doc | [VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md) |

## Operator attestation

- [ ] I reviewed the latest proof report JSON and per-frame evidence.
- [ ] I understand output is **prototype** tooling, not verified production MRMS.
- [ ] I confirm `verified_mrms` must remain **false** until a future explicit launch review phase.
- [ ] Failures/warnings in the proof report are acknowledged or tracked.
- [ ] Visual sanity checks (if any) were performed manually where required.
- [ ] Production rendering flag state was intentional for this review window.

## Reviewer

| Field | Value |
|-------|-------|
| Reviewer name | |
| Review date (UTC) | |
| Git commit or report ID | |
| Notes | |

## Explicit statement

> This sign-off documents operator review of draft MRMS proof evidence. It does **not** certify verified MRMS production output and does **not** enable `verified_mrms=true`.

## Recording sign-off (Phase 27)

```bash
make mrms-signoff ARGS="--operator-name 'Jane Operator' --notes 'Reviewed proof JSON' --accepted-limitations 'Prototype only'"
make mrms-signoff ARGS="--initials JO --accepted-limitations 'Not verified MRMS'"
```

Persisted locally at `data/dev/mrms_signoffs.json`. Read via `GET /api/validation/signoffs` or Dev Validation **Show proof review**.

### Dev API sign-off (Phase 29)

Dev/local only — same validation as CLI:

```bash
curl -X POST http://127.0.0.1:8000/api/validation/signoffs \
  -H 'Content-Type: application/json' \
  -d '{"operator_initials":"JO","operator_notes":"Reviewed proof JSON locally"}'
```

Response always includes `verified_mrms: false`, `local_signoff_only: true`, `does_not_enable_production: true`. Does **not** enable production rendering or clear proof regression automatically.

Dev Validation panel: **Show proof review** → dev sign-off form.

## Related commands

```bash
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make validation-alerts
```
