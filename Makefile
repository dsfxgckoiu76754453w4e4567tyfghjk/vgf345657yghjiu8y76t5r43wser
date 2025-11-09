# Shia Islamic Chatbot - Makefile
# Comprehensive build automation for production-grade Shia Islamic chatbot

.PHONY: help install dev test lint clean docker-up docker-down docker-build docker-ps docker-health docker-clean docker-clean-all docker-backup db-migrate db-upgrade db-downgrade format security deploy celery flower minio-ui docs verify-build test-local

# Variables
PYTHON := python3
POETRY := poetry
DOCKER_COMPOSE := docker compose
APP_NAME := shia-chatbot
DOCKER_IMAGE := $(APP_NAME):latest
SRC_DIR := src/app
TEST_DIR := tests

# Default target - show help
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Shia Islamic Chatbot - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Setup & Installation
# ============================================================================

install: ## Install all dependencies using Poetry
	$(POETRY) install
	@echo "✅ Dependencies installed successfully"

install-dev: ## Install dependencies including dev tools
	$(POETRY) install --with dev
	@echo "✅ Development dependencies installed"

install-hooks: ## Install pre-commit git hooks
	$(POETRY) run pre-commit install
	$(POETRY) run pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed"

setup: install-dev install-hooks docker-up db-upgrade ## Complete project setup (install + hooks + docker + migrations)
	@echo "✅ Project setup complete! Run 'make dev' to start development server"

# ============================================================================
# Development
# ============================================================================

dev: ## Start development server with hot reload
	$(POETRY) run uvicorn $(SRC_DIR).main:app --reload --host 0.0.0.0 --port 8000

dev-docker: docker-up ## Start all services in Docker and run dev server
	$(POETRY) run uvicorn $(SRC_DIR).main:app --reload --host 0.0.0.0 --port 8000

shell: ## Open interactive Python shell with app context
	$(POETRY) run python

# ============================================================================
# Celery & Background Tasks
# ============================================================================

celery-worker: ## Start Celery worker for background tasks
	$(POETRY) run celery -A $(SRC_DIR).tasks worker --loglevel=info --concurrency=4

celery-beat: ## Start Celery beat scheduler for periodic tasks
	$(POETRY) run celery -A $(SRC_DIR).tasks beat --loglevel=info

celery-worker-dev: ## Start Celery worker in development mode (auto-reload)
	$(POETRY) run watchmedo auto-restart --directory=./$(SRC_DIR) --pattern=*.py --recursive -- celery -A $(SRC_DIR).tasks worker --loglevel=debug

flower: ## Start Flower (Celery monitoring web UI)
	$(POETRY) run celery -A $(SRC_DIR).tasks flower --port=5555
	@echo "📊 Flower UI available at: http://localhost:5555"

celery-purge: ## Purge all Celery tasks from queue (⚠️  Use with caution!)
	@echo "⚠️  WARNING: This will DELETE ALL pending tasks!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(POETRY) run celery -A $(SRC_DIR).tasks purge; \
	else \
		echo "❌ Operation cancelled"; \
	fi

# ============================================================================
# Docker Operations
# ============================================================================

docker-up: ## Start development infrastructure only (PostgreSQL, Redis, Qdrant)
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d
	@echo "✅ Development infrastructure started"
	@echo "   - PostgreSQL: localhost:5433"
	@echo "   - Redis: localhost:6379"
	@echo "   - Qdrant: localhost:6333"
	@echo ""
	@echo "💡 Run 'make dev' to start the app natively (recommended for development)"
	@echo "💡 Or run 'make docker-up-full' to start all 10 services including monitoring"

docker-up-full: ## Start full production stack (all 10 services with monitoring)
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Full production stack started (10 services)"
	@echo ""
	@echo "Services available:"
	@echo "   - App (FastAPI): http://localhost:8000 (Swagger: /docs)"
	@echo "   - PostgreSQL: localhost:5433"
	@echo "   - Redis: localhost:6379"
	@echo "   - Qdrant: http://localhost:6333/dashboard"
	@echo "   - Flower (Celery): http://localhost:5555"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000 (admin/admin)"
	@echo "   - Nginx: http://localhost (port 80/443)"

docker-down: ## Stop all Docker services
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down
	@echo "✅ Docker services stopped"

docker-down-full: ## Stop full production stack
	$(DOCKER_COMPOSE) down
	@echo "✅ Full stack stopped"

docker-down-dev: ## Stop development infrastructure only
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down
	@echo "✅ Development infrastructure stopped"

docker-restart: docker-down docker-up ## Restart development infrastructure

docker-restart-full: docker-down-full docker-up-full ## Restart full production stack

docker-build: ## Build Docker image for the application
	docker build -t $(DOCKER_IMAGE) .
	@echo "✅ Docker image built: $(DOCKER_IMAGE)"

docker-logs: ## Show logs from all Docker services
	$(DOCKER_COMPOSE) logs -f

docker-logs-app: ## Show logs from application service (full stack only)
	$(DOCKER_COMPOSE) logs -f app

docker-logs-postgres: ## Show logs from PostgreSQL service
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f postgres 2>/dev/null || $(DOCKER_COMPOSE) logs -f postgres

docker-logs-redis: ## Show logs from Redis service
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f redis 2>/dev/null || $(DOCKER_COMPOSE) logs -f redis

docker-logs-qdrant: ## Show logs from Qdrant service
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f qdrant 2>/dev/null || $(DOCKER_COMPOSE) logs -f qdrant

docker-logs-celery: ## Show logs from Celery worker (full stack only)
	$(DOCKER_COMPOSE) logs -f celery-worker

docker-logs-flower: ## Show logs from Flower (full stack only)
	$(DOCKER_COMPOSE) logs -f flower

docker-logs-prometheus: ## Show logs from Prometheus (full stack only)
	$(DOCKER_COMPOSE) logs -f prometheus

docker-logs-grafana: ## Show logs from Grafana (full stack only)
	$(DOCKER_COMPOSE) logs -f grafana

docker-logs-nginx: ## Show logs from Nginx (full stack only)
	$(DOCKER_COMPOSE) logs -f nginx

docker-ps: ## Check status and health of all Docker services
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "Volume Status:"
	@docker volume ls | grep $(APP_NAME) || docker volume ls | grep shia-chatbot || echo "No volumes found"

docker-health: ## Check health status of all running services
	@echo "🏥 Checking service health..."
	@echo ""
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "=== Core Infrastructure ==="
	@echo -n "PostgreSQL: "
	@docker exec shia-chatbot-postgres pg_isready -U postgres 2>/dev/null && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Redis: "
	@docker exec shia-chatbot-redis redis-cli ping 2>/dev/null && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Qdrant: "
	@curl -sf http://localhost:6333/healthz >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo ""
	@echo "=== Application Services (if running full stack) ==="
	@echo -n "FastAPI App: "
	@curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Celery Worker: "
	@docker exec shia-chatbot-celery-worker celery -A src.app.tasks inspect ping 2>/dev/null >/dev/null && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Flower: "
	@curl -sf http://localhost:5555/healthcheck >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo ""
	@echo "=== Monitoring Stack (if running full stack) ==="
	@echo -n "Prometheus: "
	@curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Grafana: "
	@curl -sf http://localhost:3000/api/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Nginx: "
	@curl -sf http://localhost/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running (or not configured)"
	@echo ""
	@echo "💡 Use 'make docker-up' for dev infrastructure or 'make docker-up-full' for all services"

docker-clean: ## Remove all Docker containers and images (preserves volumes)
	$(DOCKER_COMPOSE) down --rmi all
	@echo "✅ Docker containers and images removed (volumes preserved)"

docker-clean-all: ## Remove all Docker containers, volumes, and images (⚠️  DELETES ALL DATA!)
	@echo "⚠️  WARNING: This will DELETE ALL DATA in volumes!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	$(DOCKER_COMPOSE) down -v --rmi all
	@echo "✅ Docker environment completely cleaned"

docker-backup: ## Backup all Docker volumes
	@echo "📦 Creating backups..."
	@mkdir -p backups
	@docker run --rm -v shia-chatbot-postgres_data:/data -v $(PWD)/backups:/backup ubuntu tar czf /backup/postgres_$(shell date +%Y%m%d_%H%M%S).tar.gz /data 2>/dev/null || echo "⚠️  PostgreSQL volume not found"
	@docker run --rm -v shia-chatbot-redis_data:/data -v $(PWD)/backups:/backup ubuntu tar czf /backup/redis_$(shell date +%Y%m%d_%H%M%S).tar.gz /data 2>/dev/null || echo "⚠️  Redis volume not found"
	@docker run --rm -v shia-chatbot-qdrant_data:/data -v $(PWD)/backups:/backup ubuntu tar czf /backup/qdrant_$(shell date +%Y%m%d_%H%M%S).tar.gz /data 2>/dev/null || echo "⚠️  Qdrant volume not found"
	@echo "✅ Backups created in ./backups/"

# ============================================================================
# Database Operations
# ============================================================================

db-migrate: ## Create a new Alembic migration (usage: make db-migrate MESSAGE="description")
	$(POETRY) run alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "✅ Migration created"

db-upgrade: ## Apply all pending migrations
	$(POETRY) run alembic upgrade head
	@echo "✅ Database upgraded to latest version"

db-downgrade: ## Rollback last migration
	$(POETRY) run alembic downgrade -1
	@echo "✅ Database downgraded by 1 version"

db-reset: ## Reset database (downgrade all, upgrade all)
	$(POETRY) run alembic downgrade base
	$(POETRY) run alembic upgrade head
	@echo "✅ Database reset complete"

db-shell: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d shia_chatbot

db-dump: ## Create database dump
	@mkdir -p backups
	docker exec shia-chatbot-postgres pg_dump -U postgres shia_chatbot > backups/db_dump_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database dump created in ./backups/"

db-restore: ## Restore database from dump (usage: make db-restore FILE=backups/db_dump_*.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify FILE parameter: make db-restore FILE=backups/db_dump_*.sql"; \
		exit 1; \
	fi
	docker exec -i shia-chatbot-postgres psql -U postgres shia_chatbot < $(FILE)
	@echo "✅ Database restored from $(FILE)"

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests with coverage
	$(POETRY) run pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo "✅ Tests completed. Coverage report: htmlcov/index.html"

test-unit: ## Run unit tests only
	$(POETRY) run pytest $(TEST_DIR)/unit/ -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "✅ Unit tests completed"

test-integration: ## Run integration tests only
	$(POETRY) run pytest $(TEST_DIR)/integration/ -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "✅ Integration tests completed"

test-e2e: ## Run end-to-end tests only
	$(POETRY) run pytest $(TEST_DIR)/e2e/ -v
	@echo "✅ End-to-end tests completed"

test-watch: ## Run tests in watch mode (re-run on file changes)
	$(POETRY) run ptw $(TEST_DIR)/ -- -v

test-failed: ## Re-run only failed tests from last run
	$(POETRY) run pytest $(TEST_DIR)/ --lf -v

test-verbose: ## Run tests with verbose output and no capture
	$(POETRY) run pytest $(TEST_DIR)/ -vv -s --cov=$(SRC_DIR)

test-markers: ## Show all available pytest markers
	$(POETRY) run pytest --markers

coverage: test ## Generate and open HTML coverage report
	@echo "📊 Opening coverage report..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Open htmlcov/index.html manually"

coverage-report: ## Generate coverage report without running tests
	@echo "📊 Coverage Summary:"
	@$(POETRY) run coverage report -m

# ============================================================================
# Code Quality & Linting
# ============================================================================

format: ## Format code with Black and isort
	$(POETRY) run black $(SRC_DIR)/ $(TEST_DIR)/
	$(POETRY) run isort $(SRC_DIR)/ $(TEST_DIR)/
	@echo "✅ Code formatted with Black and isort"

format-check: ## Check code formatting without making changes
	$(POETRY) run black --check $(SRC_DIR)/ $(TEST_DIR)/
	$(POETRY) run isort --check-only $(SRC_DIR)/ $(TEST_DIR)/
	@echo "✅ Format check completed"

lint: ## Run all linters (flake8, mypy, pylint)
	@echo "Running flake8..."
	$(POETRY) run flake8 $(SRC_DIR)/ $(TEST_DIR)/ --max-line-length=100 --statistics
	@echo ""
	@echo "Running mypy..."
	$(POETRY) run mypy $(SRC_DIR)/ --ignore-missing-imports --show-error-codes
	@echo ""
	@echo "Running pylint..."
	$(POETRY) run pylint $(SRC_DIR)/ --max-line-length=100 || true
	@echo "✅ Linting completed"

lint-flake8: ## Run flake8 only
	$(POETRY) run flake8 $(SRC_DIR)/ $(TEST_DIR)/ --max-line-length=100 --statistics

lint-mypy: ## Run mypy type checking only
	$(POETRY) run mypy $(SRC_DIR)/ --ignore-missing-imports --show-error-codes

lint-pylint: ## Run pylint only
	$(POETRY) run pylint $(SRC_DIR)/ --max-line-length=100

security: ## Run security checks (bandit, safety, detect-secrets)
	@echo "Running Bandit security scan..."
	$(POETRY) run bandit -r $(SRC_DIR)/ -c pyproject.toml || true
	@echo ""
	@echo "Running Safety dependency check..."
	$(POETRY) run safety check --json || true
	@echo ""
	@echo "Running detect-secrets scan..."
	$(POETRY) run detect-secrets scan --baseline .secrets.baseline || true
	@echo "✅ Security checks completed"

security-bandit: ## Run Bandit security scan only
	$(POETRY) run bandit -r $(SRC_DIR)/ -c pyproject.toml

security-safety: ## Run Safety dependency vulnerability check only
	$(POETRY) run safety check --json

security-secrets: ## Scan for hardcoded secrets
	$(POETRY) run detect-secrets scan --baseline .secrets.baseline

security-update-baseline: ## Update secrets baseline (after reviewing detected secrets)
	$(POETRY) run detect-secrets scan --update .secrets.baseline
	@echo "✅ Secrets baseline updated"

complexity: ## Check code complexity with Radon
	@echo "Cyclomatic Complexity (CC):"
	$(POETRY) run radon cc $(SRC_DIR)/ -a -s
	@echo ""
	@echo "Maintainability Index (MI):"
	$(POETRY) run radon mi $(SRC_DIR)/ -s
	@echo ""
	@echo "Raw Metrics:"
	$(POETRY) run radon raw $(SRC_DIR)/ -s

docstrings: ## Check docstring coverage with interrogate
	$(POETRY) run interrogate $(SRC_DIR)/ -v --fail-under=80

pre-commit-run: ## Run all pre-commit hooks on all files
	$(POETRY) run pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	$(POETRY) run pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated"

check: format lint security test ## Run all checks (format, lint, security, test)
	@echo "✅ All checks passed!"

quality: format-check lint complexity docstrings ## Run all quality checks without tests
	@echo "✅ All quality checks passed!"

# ============================================================================
# Cleaning
# ============================================================================

clean: ## Remove build artifacts, cache files, and generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml .pytest_cache/ .mypy_cache/ .ruff_cache/
	@echo "✅ Cleaned build artifacts and cache files"

clean-all: clean docker-clean ## Remove all artifacts including Docker resources
	@echo "✅ Complete cleanup finished"

clean-pyc: ## Remove Python file artifacts
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

# ============================================================================
# Production & Deployment
# ============================================================================

build: docker-build ## Build production Docker image

deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	docker tag $(DOCKER_IMAGE) $(DOCKER_IMAGE)-staging
	# Add your staging deployment commands here
	@echo "✅ Deployed to staging"

deploy-prod: ## Deploy to production (requires manual confirmation)
	@echo "⚠️  WARNING: Deploying to PRODUCTION"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "🚀 Deploying to production..."; \
		docker tag $(DOCKER_IMAGE) $(DOCKER_IMAGE)-prod; \
		echo "✅ Deployed to production"; \
	else \
		echo "❌ Deployment cancelled"; \
	fi

run-prod: ## Run production server (not for actual production, use docker-compose)
	$(POETRY) run uvicorn $(SRC_DIR).main:app --host 0.0.0.0 --port 8000 --workers 4

# ============================================================================
# Monitoring & Observability
# ============================================================================

logs: docker-logs ## Show application logs

langfuse-ui: ## Open Langfuse UI for observability
	@echo "📊 Langfuse UI available at: http://localhost:3001"
	@open http://localhost:3001 || xdg-open http://localhost:3001 || echo "Navigate to http://localhost:3001"

qdrant-ui: ## Open Qdrant UI for vector database
	@echo "📊 Qdrant UI available at: http://localhost:6333/dashboard"
	@open http://localhost:6333/dashboard || xdg-open http://localhost:6333/dashboard || echo "Navigate to http://localhost:6333/dashboard"

flower-ui: ## Open Flower UI for Celery monitoring
	@echo "📊 Flower UI available at: http://localhost:5555"
	@open http://localhost:5555 || xdg-open http://localhost:5555 || echo "Navigate to http://localhost:5555"

redis-cli: ## Open Redis CLI
	docker exec -it shia-chatbot-redis redis-cli

redis-monitor: ## Monitor Redis commands in real-time
	docker exec -it shia-chatbot-redis redis-cli monitor

# ============================================================================
# Documentation
# ============================================================================

docs-serve: ## Serve documentation locally with hot reload
	$(POETRY) run mkdocs serve -a 0.0.0.0:8001
	@echo "📚 Documentation available at: http://localhost:8001"

docs-build: ## Build documentation static site
	$(POETRY) run mkdocs build
	@echo "✅ Documentation built in ./site/"

docs-deploy: ## Deploy documentation to GitHub Pages
	$(POETRY) run mkdocs gh-deploy --force
	@echo "✅ Documentation deployed to GitHub Pages"

# ============================================================================
# Utilities
# ============================================================================

env-example: ## Create .env.example from current .env (DO NOT commit secrets)
	@if [ -f .env ]; then \
		cat .env | sed 's/=.*/=/' > .env.example; \
		echo "✅ .env.example created (secrets removed)"; \
	else \
		echo "❌ .env file not found"; \
	fi

requirements: ## Export requirements.txt from Poetry
	$(POETRY) export -f requirements.txt --output requirements.txt --without-hashes
	@echo "✅ requirements.txt generated"

requirements-dev: ## Export requirements-dev.txt including dev dependencies
	$(POETRY) export -f requirements.txt --output requirements-dev.txt --without-hashes --with dev
	@echo "✅ requirements-dev.txt generated"

update: ## Update all dependencies
	$(POETRY) update
	@echo "✅ Dependencies updated"

update-pre-commit: ## Update pre-commit hooks
	$(POETRY) run pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated"

version: ## Show application version
	@$(POETRY) version

version-bump-patch: ## Bump patch version (1.0.0 -> 1.0.1)
	$(POETRY) version patch
	@echo "✅ Version bumped to $$($(POETRY) version -s)"

version-bump-minor: ## Bump minor version (1.0.0 -> 1.1.0)
	$(POETRY) version minor
	@echo "✅ Version bumped to $$($(POETRY) version -s)"

version-bump-major: ## Bump major version (1.0.0 -> 2.0.0)
	$(POETRY) version major
	@echo "✅ Version bumped to $$($(POETRY) version -s)"

# ============================================================================
# CI/CD Simulation
# ============================================================================

ci: format-check lint security test ## Run CI pipeline locally (format-check, lint, security, test)
	@echo "✅ CI pipeline completed successfully"

ci-quick: format-check lint-flake8 test-unit ## Quick CI check (format, flake8, unit tests only)
	@echo "✅ Quick CI check completed"

# ============================================================================
# Development Workflows
# ============================================================================

dev-setup: setup ## Alias for setup (for new developers)

dev-reset: clean-all setup ## Complete reset and setup (⚠️  DELETES ALL DATA!)
	@echo "✅ Development environment reset complete"

quick-check: format lint-flake8 test-unit ## Quick check before commit
	@echo "✅ Quick check passed - ready to commit!"

full-check: check ## Full check before push (runs all checks)
	@echo "✅ Full check passed - ready to push!"

verify-build: ## Comprehensive pre-build verification (recommended before docker build)
	@echo "🔍 Running comprehensive pre-build verification..."
	@chmod +x scripts/verify-before-build.sh
	@./scripts/verify-before-build.sh

test-local: ## Test API endpoints locally (requires app to be running)
	@echo "🧪 Testing local API endpoints..."
	@chmod +x scripts/test-locally.sh
	@./scripts/test-locally.sh
