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

In another terminal:

```bash
make frontend
```

Open http://localhost:5173.
