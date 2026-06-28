.PHONY: setup backend frontend test lint dev seed db-reset collect-once process-once discover-mrms download-mrms inspect-grib2 decode-grib2 build-tile-cache render-status

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip
	. .venv/bin/activate && pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy pytest httpx python-dotenv
	cd frontend && npm install

backend:
	. .venv/bin/activate && uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

test:
	. .venv/bin/activate && pytest backend/tests -v

lint:
	. .venv/bin/activate && python -m compileall backend scripts

seed:
	. .venv/bin/activate && PYTHONPATH=. python scripts/seed_demo_data.py

db-reset:
	. .venv/bin/activate && PYTHONPATH=. python scripts/db_reset.py

collect-once:
	. .venv/bin/activate && PYTHONPATH=. python scripts/collect_once.py

process-once:
	. .venv/bin/activate && PYTHONPATH=. python scripts/process_once.py

discover-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/discover_mrms.py

download-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/download_mrms.py

inspect-grib2:
	. .venv/bin/activate && PYTHONPATH=. python scripts/inspect_grib2.py --latest-mrms --limit 1

decode-grib2:
	. .venv/bin/activate && PYTHONPATH=. python scripts/decode_grib2.py --latest-mrms --limit 1

build-tile-cache:
	. .venv/bin/activate && PYTHONPATH=. python scripts/build_tile_cache.py

render-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/render_status.py
