# Next Steps

## Phase 9 - MRMS Download Stub (no GRIB2 parse)

Goal: Download discovered MRMS GRIB2.gz files from NOAA AWS to local raw storage and update catalog rows with real file paths — still no GDAL/rasterio or real tile rendering.

Suggested work:
1. Add download service that fetches GRIB2.gz from `source_url` for `mrms_discovered` rows
2. Stream to `data/raw/mrms/reflectivity/{timestamp}.grib2.gz` with checksum
3. Wire collector or new `make download-mrms` script with safe limits and timeouts
4. Keep processor/tile pipeline on placeholders until GRIB2 decode phase
5. Add tests with mocked HTTP responses (no live network)

Do not start yet:
- Full GRIB2 decoding (GDAL/rasterio)
- Real radar tile rendering
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 8 verification commands

```bash
make setup
make seed
make process-once
make test
make discover-mrms
make backend
```

In another terminal:

```bash
make frontend
```

MRMS discovery checks:

```bash
# Offline stub mode (default)
make discover-mrms -- --limit 5

# Register discovered metadata in catalog
make discover-mrms -- --register --limit 5

# Live NOAA AWS listing (requires network)
MRMS_SOURCE_MODE=real make discover-mrms -- --limit 5

curl "http://127.0.0.1:8000/api/sources/mrms/latest?product=MRMS_ReflectivityAtLowestAltitude&limit=3"
```

Plan API checks (unchanged):

```bash
curl http://127.0.0.1:8000/api/access/plans
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity&plan=free"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:20:00Z/0/0/0.png?plan=free"
```

In the UI:
1. Confirm demo banner mentions MRMS discovery available, rendering still placeholder
2. Demo playback and plan limits still work on processed demo timestamps
