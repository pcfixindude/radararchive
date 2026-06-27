# Next Steps

## Phase 8 - Real MRMS Collection Stub (S3 listing only)

Goal: Add a collector path that lists or discovers real MRMS object keys from public AWS/NCEP sources without full GRIB2 parsing — register discovered frames in the catalog while keeping processing/tiles as placeholders.

Suggested work:
1. Research public MRMS S3 bucket layout and document in `docs/DATA_SOURCES.md`
2. Add collector module that lists recent object keys (no download or parse yet)
3. Register discovered keys as catalog rows with real raw paths
4. Keep processor/tile pipeline on placeholders until GRIB2 phase
5. Add tests with mocked S3 listing responses

Do not start yet:
- Full GRIB2 decoding (GDAL/rasterio)
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 7 verification commands

```bash
make setup
make seed
make process-once
make test
make backend
```

In another terminal:

```bash
make frontend
```

Manual plan checks:

```bash
curl http://127.0.0.1:8000/api/access/plans
curl "http://127.0.0.1:8000/api/access/current?plan=free"
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity&plan=free"
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity&plan=pro"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png?plan=free"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:20:00Z/0/0/0.png?plan=free"
```

In the UI:
1. Select **Free** — time slider shows one timestamp; older frames hidden
2. Select **Pro** — all demo timestamps available
3. Confirm upgrade messaging in plan panel
4. Confirm map status when plan blocks a timestamp
