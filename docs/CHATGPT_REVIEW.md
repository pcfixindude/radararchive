# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 113
- Latest phase: Phase 113 — Ingestion robustness
- Latest commit: (pending)
- Latest tag: `phase-113-ingestion-robustness`
- Push status: pending
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **113**
- Purpose: Harden bulk MRMS ingest retries, failure reporting, and partial-window recovery.
- Retry logic exists? **Yes** — bounded `download_row_with_retry()` with transient vs permanent error detection (`ingest_retry.py`)
- Partial-window recovery works? **Yes** — `partial_success` status preserves successful frames; `--retry-failed` and `--missing-only` recovery modes
- Bad/already-present files handled? **Yes** — `ingest_file_health.py` validates non-empty usable files; `--repair` re-downloads empty/checksum-mismatched files; `--force` re-downloads all
- Command changes:
  - `make mrms-bulk-local-ingest ARGS='--real --limit 8'` (unchanged default)
  - Optional: `--retry-failed`, `--repair`, `--max-retries`, `--retry-delay`, `--missing-only`
  - Warm cache still works: `make mrms-bulk-local-ingest ARGS='--real --limit 8 --warm-cache'`
- Report paths:
  - `data/dev/mrms_bulk_ingest_latest.json`
  - `data/dev/mrms_bulk_ingest_latest.md`
- Final ingest statuses: `success`, `partial_success`, `no_frames_available`, `failed` (+ `discovery_failed`, `invalid_mode`)
- Report fields: discovered/selected/downloaded/already-present/registered/repaired/skipped/failed counts, `retry_attempts`, per-failure `attempts` + exact `error`, `next_commands` including retry hints
- Backend modules: `ingest_retry.py`, `ingest_file_health.py`, `ingest_report.py`, updated `mrms_bulk_ingest.py`
- Tests: backend 1212 passed; frontend unchanged

## Current focus

Bulk ingest failures are clearer and recoverable without re-downloading the full window. Next: georef improvement, frame quality checks, or cache hardening.

## Next recommended phase

- Phase number: **114**
- Phase title: Georef improvement
- Goal: Improve decoded overlay geographic placement accuracy for local prototype playback.
- Why this is next: Ingest + cache + playback polish are in place; overlay alignment is the next playback quality lever.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 114 only.
Improve georef placement for local decoded overlay playback.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
