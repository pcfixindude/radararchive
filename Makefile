.PHONY: setup backend frontend test lint dev seed

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip
	. .venv/bin/activate && pip install fastapi uvicorn pydantic pydantic-settings pytest httpx python-dotenv
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
