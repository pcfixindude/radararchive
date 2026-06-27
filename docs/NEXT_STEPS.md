# Next Steps

## Phase 7 - Access Plan Enforcement + History Limits

Goal: Enforce subscription plan history limits on `/api/times` and `/tiles` using the existing `access_plans` table, with clear frontend messaging when frames are outside the user's plan — still without Stripe billing or real NOAA downloads.

Suggested work:
1. Apply `access_control` service to times and tile endpoints (dev plan selector or default `free`)
2. Filter timestamps returned by `/api/times` based on plan history window
3. Return 403/404 on tile requests outside plan window with helpful error detail
4. Add frontend plan indicator and “upgrade” placeholder messaging
5. Add tests for plan-limited times and tiles

Do not start yet:
- Real MRMS S3/AWS downloads
- Real GRIB2 decoding (GDAL/rasterio)
- Stripe billing integration
- Auth / user accounts
- HRRR / WPC / native Android

## Phase 6 verification commands

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

Manual checks at http://127.0.0.1:5173:
1. Map loads with CONUS-fit placeholder overlay (after `make process-once`)
2. Play advances timestamps; Pause stops autoplay
3. Step ◀/▶ and Latest work
4. Speed selector changes autoplay rate
5. Time slider stays synced during autoplay
6. UTC + local time shown in Selected Time panel
7. Opacity slider still adjusts overlay
8. Resize to mobile width — map visible, controls scroll below
9. Network tab shows `/tiles/.../{z}/{x}/{y}.png` URL changes with timestamp

API checks:

```bash
curl http://127.0.0.1:8000/api/layers
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity&processed_only=true"
```
