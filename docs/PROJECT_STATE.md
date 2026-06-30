# Project State

Current phase: Phase 109 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- **Multi-frame playback** — play/pause steps catalog timestamps; decoded overlay updates per frame
- **Adjacent prefetch** — prev/next frames prefetched via `/api/dev/decoded-overlay/prefetch`
- **In-memory frame cache** — instant replay of recently viewed frames
- **Playback states** — playing, paused, decoding, frame ready, frame missing, decode failed
- **Selected-frame decode** — per-frame cache under `data/dev/mrms_frame_cache/`
- **Default tile serving: placeholder** (production off)
- Not verified real MRMS

## Operator commands (Phase 109)

```bash
make backend
make frontend
make decode-retry
```

API (local dev):

- `GET /api/dev/decoded-overlay?timestamp=<ISO>&refresh=false`
- `GET /api/dev/decoded-overlay/prefetch?timestamps=t1,t2,t3`
- `GET /api/dev/decoded-overlay/preview.png?timestamp=<ISO>`
- `GET /api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png?timestamp=<ISO>`

## Verified MRMS

`verified_mrms` is **false** everywhere.
