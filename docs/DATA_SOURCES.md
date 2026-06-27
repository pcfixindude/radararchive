# Data Sources

## MRMS
Primary source for observed radar mosaic and precipitation products.

### Discovery source (Phase 8)
Public NOAA open-data S3 bucket: **`noaa-mrms-pds`** (anonymous HTTPS ListObjectsV2 — no AWS credentials).

Initial discovered product:
- **MRMS_ReflectivityAtLowestAltitude**

S3 layout (CONUS):
```
CONUS/ReflectivityAtLowestAltitude_00.50/{YYYYMMDD}/MRMS_ReflectivityAtLowestAltitude_00.50_{YYYYMMDD}-{HHMMSS}.grib2.gz
```

Example object key:
```
CONUS/ReflectivityAtLowestAltitude_00.50/20260627/MRMS_ReflectivityAtLowestAltitude_00.50_20260627-200000.grib2.gz
```

Public URL pattern:
```
https://noaa-mrms-pds.s3.amazonaws.com/{object_key}
```

Catalog registration fields:
- `source`: `mrms_discovered`
- `source_provider`: `noaa_aws`
- `source_url`: full HTTPS URL
- `raw_path`: S3 object key (not downloaded yet in Phase 8)
- `processed_status`: `pending` (not processed)

Config:
- `MRMS_SOURCE_MODE=stub` — offline sample listings (default for local dev)
- `MRMS_SOURCE_MODE=real` — live S3 listing with short timeout and friendly errors

Future products (not yet discovered):
- MRMS_MergedReflectivityQCComposite
- MRMS_CompositeReflectivity
- MRMS_RadarOnly_QPE_01H
- MRMS_RadarOnly_QPE_24H

## NWS Alerts
Used for watches, warnings, advisories, and alert polygons.

## HRRR
Later source for 10m wind, gusts, simulated reflectivity, precipitation, CAPE/CIN/helicity.

## WPC Surface Analysis
Later source for fronts, troughs/drylines, highs/lows, and isobars.

## Data Attribution
Footer text: "Powered by public NOAA/NWS data. Not affiliated with or endorsed by NOAA or the National Weather Service."
