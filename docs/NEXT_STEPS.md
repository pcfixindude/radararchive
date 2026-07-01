# Next Steps

## Phase 119 - Ingest date window UX (Draft)

Goal: Pick a date/time window for bounded local MRMS ingest with guided presets instead of manual ARGS only.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

## Phase 118 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

Local result after Phase 118:

- **Range & loop** panel: Set start, Set end, Loop range, Clear range
- Loop wraps inside range; playback pauses at range end when loop is off
- Time slider highlights frames inside the selected range
- Playback panel shows position in range and loop/playback status
- Keyboard: `[` start, `]` end, `L` loop, `Esc` clear range

## Phase 117 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

Local result after Phase 117:

- **Replay session** panel with readiness badge, checklist, and next-command hint
- Keyboard shortcuts for play/pause, step, overlay/bounds toggles, and fit-to-bounds

## Phase 116 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```
