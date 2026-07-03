.PHONY: lint fix format type test coverage dev migrate dump restore

lint:
	uv run ruff check .

fix:
	uv run ruff check . --fix

format:
	uv run ruff format .

type:
	uv run ty check

test:
	uv run pytest -x -q

coverage:
	uv run pytest -x -q --cov=src --cov-report=term-missing

dev:
	uv run fastapi dev src/main.py --reload

migrate:
	@read -p "Migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

dump:
	@mkdir -p ../backups
	docker compose -f ../compose.yml exec -T db \
		pg_dump -U ecommerce -Fc ecommerce \
		| gzip > ../backups/dump_$$(date +%Y%m%d_%H%M%S).tar.gz

restore:
	@test -n "$(file)" || (echo "Usage: make restore file=backups/dump_xxx.tar.gz" && exit 1)
	gunzip -c $(file) | docker compose -f ../compose.yml exec -T db \
		pg_restore -U ecommerce -d ecommerce --clean --if-exists

all: lint type test
