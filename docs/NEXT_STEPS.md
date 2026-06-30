# Next Steps

## Phase 109 - Multi-frame playback animation (Draft)

Goal: Prefetch/decode adjacent catalog frames and animate decoded overlay during time-slider playback.

```bash
make backend
make frontend
```

## Phase 108 verification commands

```bash
make test
cd frontend && npm test
cd frontend && npm run build
make backend
make frontend
```

Local result after Phase 108:

- Select timestamp with local real `.grib2.gz` → decode + preview/tiles cached and shown
- Demo stub timestamps → `stub_input` / actionable download hint
- Unknown timestamp → `no_local_candidate` with nearest local timestamps
- Frame cache under `data/dev/mrms_frame_cache/`

## Phase 107 verification commands

```bash
make test
cd frontend && npm test
cd frontend && npm run build
make decode-retry
```

## Phase 106 verification commands

```bash
make test
make decode-retry
```
