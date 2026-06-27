# RadarArchive

RadarArchive is a cloud-first historical weather replay app focused on radar history.

Primary purpose:
- Archive public NOAA/NWS weather data automatically in the cloud.
- Let users replay historical radar and weather layers from a mobile-friendly app.

Initial scope:
- MRMS radar archive
- Mobile PWA map
- Time slider playback
- Layer toggles
- Subscription-ready structure

Not initial scope:
- Native Android app
- Global weather coverage
- Full Level-II radar viewer
- AI forecasting

## Local development

```bash
make setup
make seed
make test
make backend
```

Simulate one collector run (optional):

```bash
make collect-once
make process-once
```

Discover MRMS object metadata (Phase 8):

```bash
make discover-mrms
make discover-mrms -- --register --limit 5
MRMS_SOURCE_MODE=real make discover-mrms -- --limit 5
```

Download MRMS GRIB2.gz files (Phase 9 — no GRIB2 parse):

```bash
make download-mrms -- --register-discovered --limit 5
make download-mrms -- --limit 5
make download-mrms -- --limit 5 --force
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 3
```

Limitations:
- Default `MRMS_SOURCE_MODE=stub` uses offline sample listings and stub downloads
- Real mode downloads public NOAA AWS GRIB2.gz but does not parse or render radar
- Map tiles remain placeholders until GRIB2 processing is implemented

In another terminal:

```bash
make frontend
```

Open http://127.0.0.1:5173.

Process frames before tiles appear on the map:

```bash
make process-once
```

Then open http://127.0.0.1:5173 — use **Play** for playback and the **Demo Plan** selector to test Free vs Pro history limits.
