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
- `raw_path`: S3 object key until downloaded; local path after download
- `download_status`: `pending` | `downloaded` | `failed`
- `processed_status`: `pending` (not real radar processing yet)

### Download (Phase 9)
Downloads GRIB2.gz from `source_url` into local raw storage — **no GRIB2 parse**.

Local layout:
```
data/raw/mrms/reflectivity/{timestamp_token}_{original_filename}.stub   # stub mode
data/raw/mrms/reflectivity/{timestamp_token}_{original_filename}        # real mode
```

Example stub file:
```
data/raw/mrms/reflectivity/20260626T200000Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz.stub
```

Stub files are gzip-compressed text placeholders labeled as demo/stub — not real NOAA data.

Real mode streams the public HTTPS object with short timeout; SHA256 and size stored on the catalog row.

Commands:
```bash
make download-mrms -- --register-discovered --limit 5
MRMS_SOURCE_MODE=real make download-mrms -- --limit 5
```

Limitations:
- No GRIB2 decoding, GDAL/rasterio, or real radar tiles
- Processor stub may create placeholder PNGs from downloaded raw files
- Duplicate downloads skipped when checksum/size matches (use `--force` to re-download)

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
