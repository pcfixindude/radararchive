# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 110
- Latest phase: Phase 110 — Bulk local MRMS catalog ingestion
- Latest commit: `a7678d8`
- Latest tag: `phase-110-bulk-local-mrms-catalog-ingestion`
- Push status: pushed to `origin/main` with tag
- Final git status: source clean after commit; only local `data/dev/` runtime artifacts modified

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **110**
- Purpose: Bulk download/register multiple real MRMS frames locally for multi-frame playback.
- Bulk local MRMS ingest command exists? **Yes** — `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
- Multiple raw frames downloaded/found? **Yes** (when `--real` + network); default window limit **8** (max 20); discovers, selects latest window, registers catalog rows, downloads to `data/raw/mrms/reflectivity/`
- Catalog/timeline registration works? **Yes** — reuses `register_discovered_files`; registered timestamps appear in catalog `list_times`
- Playback steps through multiple real local frames? **Yes** — `App.tsx` merges full catalog + processed times for playback sequence; Phase 108/109 decode/prefetch apply per timestamp
- Command(s):
  - `make mrms-bulk-local-ingest ARGS='--real --limit 8'`
  - Optional: `--start`, `--end`, `--force`, `--product`
- Report paths:
  - `data/dev/mrms_bulk_ingest_latest.json`
  - `data/dev/mrms_bulk_ingest_latest.md`
- Raw path: `data/raw/mrms/reflectivity/{token}_{filename}.grib2.gz`
- Catalog: `mrms_discovered` rows, product `mrms_reflectivity`
- Next commands in report: `make decode-retry`, `make backend && make frontend`
- Backend: `mrms_bulk_ingest.py` — `plan_ingest_window()`, `run_bulk_local_ingest()`
- Tests: backend 1195 passed; frontend 15 passed; `npm run build` ok

## Current focus

Bulk ingest provides a bounded real-MRMS window for playback. Next: frame cache warming, playback polish, or ingestion robustness.

## Next recommended phase

- Phase number: **111**
- Phase title: Frame cache warming for playback
- Goal: After bulk ingest, prefetch/decode the ingested window into per-frame cache so playback starts without per-step decode delay.
- Why this is next: Bulk ingest fills raw/catalog; warming cache makes Phase 109 playback smoother across multiple frames.
- Safety boundaries:
  - local dev / prototype only
  - keep production tile serving off
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 111 only.
Warm per-frame decode cache for bulk-ingested MRMS timestamps to smooth playback.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
