.PHONY: setup backend frontend test lint dev seed db-reset collect-once process-once discover-mrms download-mrms inspect-grib2 decode-grib2 build-tile-cache build-production-tiles render-status render-queue-status enqueue-render-job render-worker-once render-worker validate-real-mrms validate-real-mrms-batch benchmark-real-mrms benchmark-render-queue scheduled-validation validation-failures real-mrms-smoke-test catalog-status

ARGS ?=

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

build-production-tiles:
	. .venv/bin/activate && PYTHONPATH=. python scripts/build_production_tiles.py $(ARGS)

render-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/render_status.py

enqueue-render-job:
	. .venv/bin/activate && PYTHONPATH=. python scripts/enqueue_render_job.py $(ARGS)

render-worker-once:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_render_worker.py --once $(ARGS)

render-worker:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_render_worker.py $(ARGS)

render-queue-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/render_queue_status.py $(ARGS)

validate-real-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/validate_real_mrms.py $(ARGS)

validate-real-mrms-batch:
	. .venv/bin/activate && PYTHONPATH=. python scripts/batch_validate_mrms.py $(ARGS)

benchmark-real-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/benchmark_real_mrms.py $(ARGS)

benchmark-render-queue:
	. .venv/bin/activate && PYTHONPATH=. python scripts/benchmark_render_queue.py $(ARGS)

scheduled-validation:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py $(ARGS)

validation-failures:
	. .venv/bin/activate && PYTHONPATH=. python scripts/validation_failures.py $(ARGS)

real-mrms-smoke-test:
	. .venv/bin/activate && PYTHONPATH=. python scripts/real_mrms_smoke_test.py $(ARGS)

catalog-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/catalog_status.py $(ARGS)
