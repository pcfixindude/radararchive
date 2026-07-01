# Next Steps

## Phase 118 - Playback range and loop (Draft)

Goal: Select a start/end frame range and loop playback within that window for local storm replay.

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

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
- Collapsible keyboard shortcuts help in the session panel
- Session summary uses existing decoded overlay, cache status, and frame quality APIs

## Phase 116 verification commands

```bash
make test
cd frontend && npm test && npm run build
make backend
make frontend
```

Local result after Phase 116:

- Map & overlay panel toggles decoded overlay and bounds outline
- Fit map to overlay bounds is explicit (no auto-jump during playback)
- Selected frame summary and next-command hint in decoded overlay panel
- Georef debug and frame quality details are optional toggles

## Phase 115 verification commands

```bash
make test
make decode-retry
```

## Phase 114 verification commands

```bash
make test
cd frontend && npm test && npm run build
```
