# Project State

Current phase: Phase 83 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Candidate trend-hint acknowledgment status history** — bounded local history of acknowledgment status rollups
- **Candidate trend-hint acknowledgment status rollup** — local rollup linking trend hints to acknowledgments
- **Candidate trend-hint review acknowledgments** — local acknowledgment of reviewed candidate trend hints
- **Candidate trend hints** (Phase 80 chain) — local advisory trends from status history
- **Default tile serving: placeholder**
- Not verified real MRMS

## Operator commands (Phase 83)

```bash
make mrms-render-candidate-trend-hint-ack-status --refresh
make mrms-render-candidate-trend-hint-ack-status-history --refresh
```

## Dev API

`mrms_render_candidate_trend_hint_ack_status_history` compact on validation summary; `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status/history` for local trend-hint acknowledgment status history (does not clear alerts).

## Verified MRMS

`verified_mrms` is **false** everywhere.
