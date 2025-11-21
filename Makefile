.PHONY: help install install-dev lint lint-fix test test-cov clean format type-check check all

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	uv pip install -e .

install-dev: ## Install the package with dev dependencies
	uv pip install -e ".[dev]"

lint: ## Run linters (ruff, black check, mypy)
	uv run ruff check src/ tests/
	uv run black --check src/ tests/
	uv run mypy src/

lint-fix: ## Fix linting issues automatically
	uv run ruff check --fix src/ tests/
	uv run black src/ tests/

format: ## Format code with black
	uv run black src/ tests/

type-check: ## Run type checking with mypy
	uv run mypy src/

test: ## Run tests (starts TimescaleDB Docker container automatically)
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Install Docker or use 'make test-local' with your own database."; exit 1; }
	@echo "🐳 Starting TimescaleDB container..."
	@docker-compose -f docker-compose.test.yml down 2>/dev/null || true
	@docker-compose -f docker-compose.test.yml up -d || exit 1
	@echo "⏳ Waiting for database to be ready..."
	@timeout=30; \
	while [ $$timeout -gt 0 ]; do \
		if docker exec timescaledb-test pg_isready -U postgres > /dev/null 2>&1; then \
			sleep 8; \
			docker exec timescaledb-test psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';" > /dev/null 2>&1; \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Waiting... ($$timeout seconds remaining)"; \
		sleep 1; \
		timeout=$$((timeout-1)); \
	done; \
	if [ $$timeout -eq 0 ]; then \
		echo "❌ Database failed to start or become ready"; \
		docker-compose -f docker-compose.test.yml down; \
		exit 1; \
	fi
	@echo "🧪 Running tests..."
	@EXIT_CODE=0; \
	TIMESCALEDB_HOST=localhost \
	 TIMESCALEDB_PORT=5432 \
	 TIMESCALEDB_DATABASE=postgres \
	 TIMESCALEDB_USER=postgres \
	 TIMESCALEDB_PASSWORD=postgres \
	 uv run pytest tests/ -v || EXIT_CODE=$$?; \
	 echo "🧹 Cleaning up Docker container..."; \
	 docker-compose -f docker-compose.test.yml down; \
	 exit $$EXIT_CODE

test-cov: ## Run tests with coverage (starts TimescaleDB Docker container automatically)
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Install Docker or use 'make test-local' with your own database."; exit 1; }
	@echo "🐳 Starting TimescaleDB container..."
	@docker-compose -f docker-compose.test.yml down 2>/dev/null || true
	@docker-compose -f docker-compose.test.yml up -d || exit 1
	@echo "⏳ Waiting for database to be ready..."
	@timeout=30; \
	while [ $$timeout -gt 0 ]; do \
		if docker exec timescaledb-test pg_isready -U postgres > /dev/null 2>&1; then \
			sleep 8; \
			docker exec timescaledb-test psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';" > /dev/null 2>&1; \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Waiting... ($$timeout seconds remaining)"; \
		sleep 1; \
		timeout=$$((timeout-1)); \
	done; \
	if [ $$timeout -eq 0 ]; then \
		echo "❌ Database failed to start or become ready"; \
		docker-compose -f docker-compose.test.yml down; \
		exit 1; \
	fi
	@echo "🧪 Running tests with coverage..."
	@EXIT_CODE=0; \
	TIMESCALEDB_HOST=localhost \
	 TIMESCALEDB_PORT=5432 \
	 TIMESCALEDB_DATABASE=postgres \
	 TIMESCALEDB_USER=postgres \
	 TIMESCALEDB_PASSWORD=postgres \
	 uv run pytest tests/ -v --cov=timescaledb_mcp --cov-report=html --cov-report=term || EXIT_CODE=$$?; \
	echo "🧹 Cleaning up Docker container..."; \
	docker-compose -f docker-compose.test.yml down; \
	exit $$EXIT_CODE

test-local: ## Run tests against local database (no Docker, uses existing connection)
	uv run pytest tests/ -v

check: lint type-check test ## Run all checks (lint, type-check, test)

all: lint type-check test ## Run all checks and tests

clean: ## Clean build artifacts and test containers
	rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true

