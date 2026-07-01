# ChatGPT Review Handoff

Concise continuation state for ChatGPT. After each phase, Cursor updates this file so you can ask: **“Read docs/CHATGPT_REVIEW.md and give me the next phase.”**

Do not treat this file as verified MRMS proof or production authorization.

## Current state

- Project: RadarArchive
- Repo: pcfixindude/radararchive
- Local path: ~/Projects/radararchive
- Completed through phase: 121
- Latest phase: Phase 121 — One-shot local replay setup
- Latest commit: `547216f`
- Latest tag: `phase-121-one-shot-local-replay-setup`
- Push status: pushed to `origin/main` with tag
- Final git status: source committed; local `data/dev/` runtime artifacts not committed

## Safety state

- `verified_mrms`: **false**
- `ENABLE_PRODUCTION_RADAR_TILES`: **false** by default
- Placeholder tiles default: **true**
- Production rendering: gated/off by default
- Color preview + local tiles: prototype/local dev only — not verified MRMS

## Latest phase summary

- Phase: **121**
- Purpose: Guided one-shot post-ingest setup chaining bounded warm/decode readiness checks.
- CLI? **Yes** — `make local-replay-ready` dry-run default; `RUN=1` executes local warm/decode only (never real ingest)
- API? **Yes** — `GET /api/dev/local-replay-ready` returns checklist/status/next command
- UI? **Yes** — Replay session panel shows **Local replay setup** checklist with refresh
- Checks: local frames, frame cache, decoded artifacts, open UI step
- Tests: backend 1248 passed; frontend 67 passed; `npm run build` ok

## Current focus

Post-ingest setup is one command away from replay-ready status. Next: frame catalog browser or playback export clip.

## Next recommended phase

- Phase number: **122**
- Phase title: Frame catalog browser
- Goal: Browse available local MRMS frames with cache/decode status and jump-to-frame for faster local replay navigation.
- Why this is next: Setup workflow is streamlined; browsing frames in the UI reduces hunting on the time slider alone.
- Safety boundaries:
  - local dev / prototype only
  - no silent real MRMS download
  - no verified MRMS claim

## Suggested next Cursor prompt

```text
Follow docs/CURSOR_RULES.md and docs/PHASE_WORKFLOW_RULES.md.
Read docs/CHATGPT_REVIEW.md first and implement Phase 122 only.
Add a frame catalog browser for local replay navigation.
```

## Key docs (read order for new work)

1. `docs/CHATGPT_REVIEW.md` (this file)
2. `docs/PROJECT_STATE.md`
3. `docs/NEXT_STEPS.md`
4. `docs/PHASE_LOG.md`
