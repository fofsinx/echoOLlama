.PHONY: migrations migrate rollback

# Set Python path
export PYTHONPATH := $(shell pwd)

migrations:
	source scripts/set_env.sh && alembic revision --autogenerate -m "$(message)"

migrate:
	source scripts/set_env.sh && alembic upgrade head

rollback:
	source scripts/set_env.sh && alembic downgrade -1