# Next Steps

## Phase 117 - Playback keyboard shortcuts (Draft)

Goal: Keyboard shortcuts for play/pause, step frames, and common overlay toggles.

```bash
cd frontend && npm test && npm run build
make backend
make frontend
```

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
