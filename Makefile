.PHONY: up down build logs uplint format install-hooks db-revision db-upgrade db-seed

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

uplint:
	docker-compose exec api ruff check .
	docker-compose exec workers ruff check .
	docker-compose exec web npm run lint

format:
	docker-compose exec api ruff format .
	docker-compose exec workers ruff format .
	docker-compose exec web npm run format

install-hooks:
	pip install pre-commit
	pre-commit install
