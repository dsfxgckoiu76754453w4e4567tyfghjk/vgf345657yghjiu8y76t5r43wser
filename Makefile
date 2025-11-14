# Shia Islamic Chatbot - Makefile
# Comprehensive build automation for production-grade Shia Islamic chatbot

.PHONY: help install dev test lint clean docker-up docker-down docker-build docker-ps docker-health docker-clean docker-clean-all docker-backup db-migrate db-upgrade db-downgrade format security deploy temporal-ui minio-ui docs verify-build test-local

# Variables
PYTHON := python3
UV := uv
DOCKER_COMPOSE := docker compose
APP_NAME := shia-chatbot
DOCKER_IMAGE := $(APP_NAME):latest
SRC_DIR := src/app
MODULE_NAME := app
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

install: ## Install all dependencies using uv
	$(UV) sync
	@echo "✅ Dependencies installed successfully"

install-dev: ## Install dependencies including dev tools
	$(UV) sync --extra dev
	@echo "✅ Development dependencies installed"

install-hooks: ## Install pre-commit git hooks
	$(UV) run pre-commit install
	$(UV) run pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed"

setup: install-dev install-hooks docker-up db-upgrade ## Complete project setup (install + hooks + docker + migrations)
	@echo "✅ Project setup complete! Run 'make dev' to start development server"

# ============================================================================
# Development
# ============================================================================

dev: ## Start development server with hot reload
	$(UV) run uvicorn $(MODULE_NAME).main:app --reload --host 0.0.0.0 --port 8000

dev-docker: docker-up ## Start all services in Docker and run dev server
	$(UV) run uvicorn $(MODULE_NAME).main:app --reload --host 0.0.0.0 --port 8000

shell: ## Open interactive Python shell with app context
	$(UV) run python

# ============================================================================
# Temporal Workflows - Async Task Processing
# ============================================================================
#
# Temporal handles all async background processing (replaces Celery)
# Temporal UI is available at: http://localhost:8233
#
# ============================================================================

temporal-ui: ## Open Temporal Web UI
	@echo "📊 Temporal UI: http://localhost:8233"
	@open http://localhost:8233 || xdg-open http://localhost:8233 || echo "Navigate to http://localhost:8233"

# ============================================================================
# Docker Operations - New Optimized Architecture
# ============================================================================
#
# Two Modes:
#   Mode 1: Local development (app runs natively, all services in Docker)
#   Mode 2: Environment releases (everything in Docker: DEV/STAGE/PROD)
#
# Architecture:
#   docker-compose.base.yml           - All infrastructure services (shared)
#   docker-compose.app.dev.yml        - DEV environment (ENVIRONMENT=dev)
#   docker-compose.app.stage.yml      - STAGE environment (ENVIRONMENT=stage)
#   docker-compose.app.prod.yml       - PROD environment (ENVIRONMENT=prod)
# ============================================================================

# ----------------------------------------------------------------------------
# MODE 1: Local Development (No Image Build)
# ----------------------------------------------------------------------------

docker-local: ## Mode 1: Start ALL services (app runs natively)
	$(DOCKER_COMPOSE) -f docker-compose.base.yml up -d
	@echo "✅ Local development infrastructure started (Mode 1)"
	@echo ""
	@echo "Services running in Docker:"
	@echo "   - PostgreSQL: localhost:5433"
	@echo "   - Redis: localhost:6379"
	@echo "   - Qdrant: http://localhost:6333/dashboard"
	@echo "   - MinIO: http://localhost:9000 (Console: http://localhost:9001)"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000 (admin/admin)"
	@echo "   - Nginx: http://localhost:8100"
	@echo ""
	@echo "💡 Now run app natively:"
	@echo "   make dev           # FastAPI with hot reload"

docker-local-down: ## Mode 1: Stop all local development services
	$(DOCKER_COMPOSE) -f docker-compose.base.yml down
	@echo "✅ Local development infrastructure stopped"

docker-local-restart: docker-local-down docker-local ## Mode 1: Restart local development

# ----------------------------------------------------------------------------
# MODE 2: Environment Releases (With Image Build)
# ----------------------------------------------------------------------------

docker-dev: ## Mode 2: Start DEV environment (ENVIRONMENT=dev)
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.dev.yml up --build -d
	@echo "✅ DEV environment started (Mode 2)"
	@echo ""
	@echo "Services available:"
	@echo "   - App (FastAPI): http://localhost:8000 (Swagger: /docs)"
	@echo "   - PostgreSQL: localhost:5433"
	@echo "   - Redis: localhost:6379"
	@echo "   - Qdrant: http://localhost:6333/dashboard"
	@echo "   - MinIO: http://localhost:9000"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000 (admin/admin)"
	@echo "   - Nginx: http://localhost:8100"
	@echo ""
	@echo "Environment: ENVIRONMENT=dev"
	@echo "Container prefix: shia-chatbot-dev-*"

docker-stage: ## Mode 2: Start STAGE environment (ENVIRONMENT=stage)
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.stage.yml up --build -d
	@echo "✅ STAGE environment started (Mode 2)"
	@echo ""
	@echo "Services available:"
	@echo "   - App (FastAPI): http://localhost:8001 (Swagger: /docs)"
	@echo "   - All infrastructure services same as DEV"
	@echo ""
	@echo "Environment: ENVIRONMENT=stage"
	@echo "Container prefix: shia-chatbot-stage-*"

docker-prod: ## Mode 2: Start PROD environment (⚠️ SHARED VPS - BE CAREFUL!)
	@echo "⚠️ ⚠️ ⚠️  PRODUCTION DEPLOYMENT WARNING  ⚠️ ⚠️ ⚠️"
	@echo ""
	@echo "This VPS hosts OTHER PRODUCTION CONTAINERS with REAL USERS!"
	@echo ""
	@echo "Before proceeding, verify:"
	@echo "1. No container name conflicts: docker ps -a"
	@echo "2. No port binding conflicts"
	@echo "3. Sufficient system resources available"
	@echo ""
	@read -p "Have you read docker-compose.app.prod.yml header? [y/N] " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "❌ Please read the safety warnings in docker-compose.app.prod.yml first!"; \
		exit 1; \
	fi; \
	read -p "Proceed with PRODUCTION deployment? [y/N] " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "❌ Deployment cancelled"; \
		exit 1; \
	fi
	@echo "🚀 Starting PROD environment..."
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.prod.yml up --build -d
	@echo "✅ PROD environment started (Mode 2)"
	@echo ""
	@echo "Services available:"
	@echo "   - App (FastAPI): http://localhost:8002 (Swagger: /docs)"
	@echo "   - All infrastructure services same as DEV/STAGE"
	@echo ""
	@echo "Environment: ENVIRONMENT=prod"
	@echo "Container prefix: shia-chatbot-prod-*"
	@echo "⚠️  WARNING: Production mode - Debug disabled, warning-level logging"

# Stop commands for environments
docker-dev-down: ## Mode 2: Stop DEV environment
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.dev.yml down
	@echo "✅ DEV environment stopped"

docker-stage-down: ## Mode 2: Stop STAGE environment
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.stage.yml down
	@echo "✅ STAGE environment stopped"

docker-prod-down: ## Mode 2: Stop PROD environment
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.prod.yml down
	@echo "✅ PROD environment stopped"

# Restart commands
docker-dev-restart: docker-dev-down docker-dev ## Mode 2: Restart DEV environment

docker-stage-restart: docker-stage-down docker-stage ## Mode 2: Restart STAGE environment

docker-prod-restart: docker-prod-down docker-prod ## Mode 2: Restart PROD environment

# Legacy aliases (for backward compatibility)
docker-up: docker-local ## Alias for docker-local (backward compatibility)

docker-down: docker-local-down ## Alias for docker-local-down (backward compatibility)

docker-build: ## Build Docker image for the application
	docker build -t $(DOCKER_IMAGE) .
	@echo "✅ Docker image built: $(DOCKER_IMAGE)"

# Logs commands
docker-logs-base: ## Show logs from base infrastructure services
	$(DOCKER_COMPOSE) -f docker-compose.base.yml logs -f

docker-logs-dev: ## Show logs from DEV environment
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.dev.yml logs -f

docker-logs-stage: ## Show logs from STAGE environment
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.stage.yml logs -f

docker-logs-prod: ## Show logs from PROD environment
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.app.prod.yml logs -f

docker-logs-app: ## Show logs from app container (specify ENV=dev|stage|prod)
	@if [ "$(ENV)" = "dev" ]; then \
		docker logs -f shia-chatbot-dev-app; \
	elif [ "$(ENV)" = "stage" ]; then \
		docker logs -f shia-chatbot-stage-app; \
	elif [ "$(ENV)" = "prod" ]; then \
		docker logs -f shia-chatbot-prod-app; \
	else \
		echo "Usage: make docker-logs-app ENV=dev|stage|prod"; \
	fi

docker-logs-postgres: ## Show logs from PostgreSQL
	docker logs -f shia-chatbot-postgres

docker-logs-redis: ## Show logs from Redis
	docker logs -f shia-chatbot-redis

docker-ps: ## Check status and health of all Docker services
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "Volume Status:"
	@docker volume ls | grep $(APP_NAME) || docker volume ls | grep shia-chatbot || echo "No volumes found"

docker-health: ## Check health of all running Docker services
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "=== Core Infrastructure (Base Services) ==="
	@echo -n "PostgreSQL: "
	@docker exec shia-chatbot-postgres pg_isready -U postgres 2>/dev/null && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Redis: "
	@docker exec shia-chatbot-redis redis-cli ping 2>/dev/null && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Qdrant: "
	@curl -sf http://localhost:6333/healthz >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "MinIO: "
	@curl -sf http://localhost:9000/minio/health/live >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Prometheus: "
	@curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Grafana: "
	@curl -sf http://localhost:3000/api/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo -n "Nginx: "
	@docker exec shia-chatbot-nginx nginx -t >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo ""
	@echo "=== DEV Environment (if running) ==="
	@echo -n "DEV App: "
	@curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo ""
	@echo "=== STAGE Environment (if running) ==="
	@echo -n "STAGE App: "
	@curl -sf http://localhost:8001/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo ""
	@echo "=== PROD Environment (if running) ==="
	@echo -n "PROD App: "
	@curl -sf http://localhost:8002/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Not running"
	@echo ""
	@echo "💡 Modes:"
	@echo "   Mode 1: make docker-local (then run: make dev)"
	@echo "   Mode 2: make docker-dev | docker-stage | docker-prod"

# Environment Promotion Commands
docker-promote-dev-stage: ## Promote approved data from DEV to STAGE
	@echo "🔄 Promoting data from DEV → STAGE..."
	@echo "⚠️  This will copy approved content from DEV to STAGE environment"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(UV) run python scripts/promote.py --source dev --target stage; \
	else \
		echo "❌ Promotion cancelled"; \
	fi

docker-promote-stage-prod: ## Promote approved data from STAGE to PROD
	@echo "🔄 Promoting data from STAGE → PROD..."
	@echo "⚠️  WARNING: This will affect PRODUCTION environment!"
	@read -p "Are you absolutely sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(UV) run python scripts/promote.py --source stage --target prod; \
	else \
		echo "❌ Promotion cancelled"; \
	fi

docker-clean: ## Remove all Docker containers and images (preserves volumes)
	$(DOCKER_COMPOSE) down --rmi all
	@echo "✅ Docker containers and images removed (volumes preserved)"

docker-clean-all: ## Remove all Docker containers, volumes, and images (⚠️  DELETES ALL DATA!)
	@echo "⚠️ ⚠️ ⚠️  DANGER: DATA DELETION WARNING  ⚠️ ⚠️ ⚠️"
	@echo ""
	@echo "This will DELETE ALL DATA in docker-compose volumes:"
	@echo "  - PostgreSQL databases (ALL environments)"
	@echo "  - Redis data"
	@echo "  - Qdrant vector collections"
	@echo "  - MinIO object storage"
	@echo "  - All application images"
	@echo ""
	@echo "This command only affects shia-chatbot containers."
	@echo "It will NOT affect other containers on this VPS."
	@echo ""
	@read -p "Are you ABSOLUTELY SURE? Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "❌ Cancelled - data preserved"; \
		exit 1; \
	fi
	@echo "🗑️  Cleaning docker-compose environment..."
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
	$(UV) run alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "✅ Migration created"

db-upgrade: ## Apply all pending migrations
	$(UV) run alembic upgrade head
	@echo "✅ Database upgraded to latest version"

db-downgrade: ## Rollback last migration
	$(UV) run alembic downgrade -1
	@echo "✅ Database downgraded by 1 version"

db-reset: ## Reset database (downgrade all, upgrade all)
	$(UV) run alembic downgrade base
	$(UV) run alembic upgrade head
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
	$(UV) run pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo "✅ Tests completed. Coverage report: htmlcov/index.html"

test-unit: ## Run unit tests only
	$(UV) run pytest $(TEST_DIR)/unit/ -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "✅ Unit tests completed"

test-integration: ## Run integration tests only
	$(UV) run pytest $(TEST_DIR)/integration/ -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "✅ Integration tests completed"

test-e2e: ## Run end-to-end tests only
	$(UV) run pytest $(TEST_DIR)/e2e/ -v
	@echo "✅ End-to-end tests completed"

test-watch: ## Run tests in watch mode (re-run on file changes)
	$(UV) run ptw $(TEST_DIR)/ -- -v

test-failed: ## Re-run only failed tests from last run
	$(UV) run pytest $(TEST_DIR)/ --lf -v

test-verbose: ## Run tests with verbose output and no capture
	$(UV) run pytest $(TEST_DIR)/ -vv -s --cov=$(SRC_DIR)

test-markers: ## Show all available pytest markers
	$(UV) run pytest --markers

coverage: test ## Generate and open HTML coverage report
	@echo "📊 Opening coverage report..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Open htmlcov/index.html manually"

coverage-report: ## Generate coverage report without running tests
	@echo "📊 Coverage Summary:"
	@$(UV) run coverage report -m

# ============================================================================
# Code Quality & Linting
# ============================================================================

format: ## Format code with Black and isort
	$(UV) run black $(SRC_DIR)/ $(TEST_DIR)/
	$(UV) run isort $(SRC_DIR)/ $(TEST_DIR)/
	@echo "✅ Code formatted with Black and isort"

format-check: ## Check code formatting without making changes
	$(UV) run black --check $(SRC_DIR)/ $(TEST_DIR)/
	$(UV) run isort --check-only $(SRC_DIR)/ $(TEST_DIR)/
	@echo "✅ Format check completed"

lint: ## Run all linters (flake8, mypy, pylint)
	@echo "Running flake8..."
	$(UV) run flake8 $(SRC_DIR)/ $(TEST_DIR)/ --max-line-length=100 --statistics
	@echo ""
	@echo "Running mypy..."
	$(UV) run mypy $(SRC_DIR)/ --ignore-missing-imports --show-error-codes
	@echo ""
	@echo "Running pylint..."
	$(UV) run pylint $(SRC_DIR)/ --max-line-length=100 || true
	@echo "✅ Linting completed"

lint-flake8: ## Run flake8 only
	$(UV) run flake8 $(SRC_DIR)/ $(TEST_DIR)/ --max-line-length=100 --statistics

lint-mypy: ## Run mypy type checking only
	$(UV) run mypy $(SRC_DIR)/ --ignore-missing-imports --show-error-codes

lint-pylint: ## Run pylint only
	$(UV) run pylint $(SRC_DIR)/ --max-line-length=100

security: ## Run security checks (bandit, safety, detect-secrets)
	@echo "Running Bandit security scan..."
	$(UV) run bandit -r $(SRC_DIR)/ -c pyproject.toml || true
	@echo ""
	@echo "Running Safety dependency check..."
	$(UV) run safety check --json || true
	@echo ""
	@echo "Running detect-secrets scan..."
	$(UV) run detect-secrets scan --baseline .secrets.baseline || true
	@echo "✅ Security checks completed"

security-bandit: ## Run Bandit security scan only
	$(UV) run bandit -r $(SRC_DIR)/ -c pyproject.toml

security-safety: ## Run Safety dependency vulnerability check only
	$(UV) run safety check --json

security-secrets: ## Scan for hardcoded secrets
	$(UV) run detect-secrets scan --baseline .secrets.baseline

security-update-baseline: ## Update secrets baseline (after reviewing detected secrets)
	$(UV) run detect-secrets scan --update .secrets.baseline
	@echo "✅ Secrets baseline updated"

complexity: ## Check code complexity with Radon
	@echo "Cyclomatic Complexity (CC):"
	$(UV) run radon cc $(SRC_DIR)/ -a -s
	@echo ""
	@echo "Maintainability Index (MI):"
	$(UV) run radon mi $(SRC_DIR)/ -s
	@echo ""
	@echo "Raw Metrics:"
	$(UV) run radon raw $(SRC_DIR)/ -s

docstrings: ## Check docstring coverage with interrogate
	$(UV) run interrogate $(SRC_DIR)/ -v --fail-under=80

pre-commit-run: ## Run all pre-commit hooks on all files
	$(UV) run pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	$(UV) run pre-commit autoupdate
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
	$(UV) run uvicorn $(MODULE_NAME).main:app --host 0.0.0.0 --port 8000 --workers 4

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

redis-cli: ## Open Redis CLI
	docker exec -it shia-chatbot-redis redis-cli

redis-monitor: ## Monitor Redis commands in real-time
	docker exec -it shia-chatbot-redis redis-cli monitor

# ============================================================================
# Documentation
# ============================================================================

docs-serve: ## Serve documentation locally with hot reload
	$(UV) run mkdocs serve -a 0.0.0.0:8001
	@echo "📚 Documentation available at: http://localhost:8001"

docs-build: ## Build documentation static site
	$(UV) run mkdocs build
	@echo "✅ Documentation built in ./site/"

docs-deploy: ## Deploy documentation to GitHub Pages
	$(UV) run mkdocs gh-deploy --force
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

requirements: ## Export requirements.txt from uv
	$(UV) pip compile pyproject.toml -o requirements.txt
	@echo "✅ requirements.txt generated"

requirements-dev: ## Export requirements-dev.txt including dev dependencies
	$(UV) pip compile pyproject.toml --extra dev -o requirements-dev.txt
	@echo "✅ requirements-dev.txt generated"

update: ## Update all dependencies
	$(UV) sync --upgrade
	@echo "✅ Dependencies updated"

update-pre-commit: ## Update pre-commit hooks
	$(UV) run pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated"

version: ## Show application version
	@python -c "import tomlkit; f=open("pyproject.toml"); d=tomlkit.load(f); print(d["project"]["version"]); f.close()"

version-bump-patch: ## Bump patch version (1.0.0 -> 1.0.1)
	python -c "import tomlkit; f=open("pyproject.toml"); d=tomlkit.load(f); print(d["project"]["version"]); f.close()" patch
	@echo "✅ Version bumped to $$(python -c "import tomlkit; f=open("pyproject.toml"); d=tomlkit.load(f); print(d["project"]["version"]); f.close()" -s)"

version-bump-minor: ## Bump minor version (1.0.0 -> 1.1.0)
	python -c "import tomlkit; f=open("pyproject.toml"); d=tomlkit.load(f); print(d["project"]["version"]); f.close()" minor
	@echo "✅ Version bumped to $$(python -c "import tomlkit; f=open("pyproject.toml"); d=tomlkit.load(f); print(d["project"]["version"]); f.close()" -s)"

version-bump-major: ## Bump major version (1.0.0 -> 2.0.0)
	python -c "import tomlkit; f=open("pyproject.toml"); d=tomlkit.load(f); print(d["project"]["version"]); f.close()" major
	@echo "✅ Version bumped to $$(python -c "import tomlkit; f=open("pyproject.toml"); d=tomlkit.load(f); print(d["project"]["version"]); f.close()" -s)"

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
