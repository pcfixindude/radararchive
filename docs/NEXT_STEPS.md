# Next Steps

## Phase 17 - Background Worker + Render Queue

Goal: Move production tile batch builds off the CLI into a worker process with a simple job queue, progress tracking, and safer catalog promotion workflow.

Suggested work:
1. Worker script/process for `build-production-tiles` batches (not in API routes)
2. Simple SQLite or file-based job queue for render tasks
3. Separate `production_prototype` vs future `production_verified` catalog status
4. Progress reporting API (dev-only) for build status
5. Validate one real MRMS frame against known bounds
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 16 verification commands

```bash
make test
make build-production-tiles
PYTHONPATH=. python scripts/build_production_tiles.py --dry-run --json-report
cd frontend && npm run build
```

Production build benchmark:

```bash
make decode-grib2
PYTHONPATH=. python scripts/build_production_tiles.py --min-zoom 0 --max-zoom 2 --json-report
PYTHONPATH=. python scripts/build_production_tiles.py --dry-run
PYTHONPATH=. python scripts/build_production_tiles.py --force
```

Production serving (unchanged gates):

```bash
PYTHONPATH=. python scripts/build_production_tiles.py --mark-catalog   # fixture/test ONLY
ENABLE_PRODUCTION_RADAR_TILES=true make backend
```

Placeholder default (unchanged):

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
# X-RadarArchive-Tile: placeholder
# X-RadarArchive-Production-Rendering: false
```
