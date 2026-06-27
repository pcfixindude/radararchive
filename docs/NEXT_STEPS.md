# Next Steps

## Phase 6 - Georeferenced Tiles + Playback Polish

Goal: Align placeholder tiles to a real CONUS (or regional) bounding box, add smooth time-slider playback (auto-play/pause), and improve mobile map UX — still without real GRIB2 or NOAA downloads.

Suggested work:
1. Define MRMS reflectivity tile bounds and zoom range in backend tile metadata
2. Constrain MapLibre raster source bounds so overlays align with the basemap
3. Wire play/pause to advance timestamps on an interval
4. Add keyboard/touch-friendly playback controls for mobile PWA
5. Keep tiles as obvious placeholders until real processing lands

Do not start yet:
- Real MRMS S3/AWS downloads
- Real GRIB2 decoding (GDAL/rasterio)
- Stripe billing
- Auth
- HRRR / WPC / native Android

## Phase 5 verification commands

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

Open http://127.0.0.1:5173 and verify:
1. MapLibre basemap loads
2. Selected timestamp shows in map status bar
3. Browser network tab requests `/tiles/mrms_reflectivity/.../{z}/{x}/{y}.png`
4. Moving the time slider changes tile URLs
5. Opacity slider adjusts radar overlay

Manual API checks:

```bash
curl http://127.0.0.1:8000/api/health
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```
