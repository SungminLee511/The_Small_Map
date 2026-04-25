.PHONY: up down migrate seed test lint

up:
	docker-compose up --build -d

down:
	docker-compose down

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m scripts.seed_dev_data

test:
	cd backend && pytest -v

lint:
	cd backend && ruff check . && black --check .

format:
	cd backend && ruff check --fix . && black .
