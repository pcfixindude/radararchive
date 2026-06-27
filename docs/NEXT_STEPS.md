# Next Steps

## Phase 2 - Catalog + Storage Foundation

Goal: Replace hard-coded demo timestamps with a database-backed catalog and local/raw storage layout, still without full NOAA download automation.

Suggested work:
1. Wire SQLAlchemy models in `backend/app/models/` to a local SQLite/Postgres database
2. Implement `backend/app/services/catalog.py` to read layers/timestamps from the DB
3. Seed demo catalog rows via `scripts/seed_demo_data.py` instead of in-memory lists
4. Keep API response shapes stable (`/api/layers`, `/api/times`, `/api/latest`)
5. Add catalog service tests; keep collection out of API request paths

Do not start yet:
- Real MRMS S3 downloads
- Tile rendering pipeline
- Stripe billing
- Auth
- HRRR / WPC / native Android

## Phase 1 verification commands

```bash
make setup
make test
make backend
```

In another terminal:

```bash
make frontend
```

Manual API checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/layers
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity"
curl "http://127.0.0.1:8000/api/latest?layer=mrms_reflectivity"
```
