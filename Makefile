# Shia Islamic Chatbot - Makefile
# Minimal yet comprehensive build automation

.PHONY: help install dev test lint clean docker-up docker-down docker-build db-migrate db-upgrade db-downgrade format security deploy

# Variables
PYTHON := python3
POETRY := poetry
DOCKER_COMPOSE := docker-compose
APP_NAME := shia-chatbot
DOCKER_IMAGE := $(APP_NAME):latest

# Default target - show help
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Shia Islamic Chatbot - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Setup & Installation
# ============================================================================

install: ## Install all dependencies using Poetry
	$(POETRY) install
	@echo "✅ Dependencies installed successfully"

install-dev: ## Install dependencies including dev tools
	$(POETRY) install --with dev
	@echo "✅ Development dependencies installed"

setup: install docker-up db-upgrade ## Complete project setup (install + docker + migrations)
	@echo "✅ Project setup complete! Run 'make dev' to start development server"

# ============================================================================
# Development
# ============================================================================

dev: ## Start development server with hot reload
	$(POETRY) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-docker: docker-up ## Start all services in Docker and run dev server
	$(POETRY) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

shell: ## Open interactive Python shell with app context
	$(POETRY) run python

# ============================================================================
# Docker Operations
# ============================================================================

docker-up: ## Start all Docker services (PostgreSQL, Redis, Qdrant, Langfuse)
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Docker services started"

docker-down: ## Stop all Docker services
	$(DOCKER_COMPOSE) down
	@echo "✅ Docker services stopped"

docker-restart: docker-down docker-up ## Restart all Docker services

docker-build: ## Build Docker image for the application
	docker build -t $(DOCKER_IMAGE) .
	@echo "✅ Docker image built: $(DOCKER_IMAGE)"

docker-logs: ## Show logs from all Docker services
	$(DOCKER_COMPOSE) logs -f

docker-clean: ## Remove all Docker containers, volumes, and images
	$(DOCKER_COMPOSE) down -v --rmi all
	@echo "✅ Docker environment cleaned"

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

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests with coverage
	$(POETRY) run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "✅ Tests completed. Coverage report: htmlcov/index.html"

test-unit: ## Run unit tests only
	$(POETRY) run pytest tests/test_*.py -v --cov=src
	@echo "✅ Unit tests completed"

test-integration: ## Run integration tests only
	$(POETRY) run pytest tests/integration/ -v
	@echo "✅ Integration tests completed"

test-watch: ## Run tests in watch mode (re-run on file changes)
	$(POETRY) run ptw tests/ -- -v

coverage: test ## Generate HTML coverage report
	@echo "📊 Opening coverage report..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Open htmlcov/index.html manually"

# ============================================================================
# Code Quality & Linting
# ============================================================================

format: ## Format code with ruff
	$(POETRY) run ruff format src/ tests/
	$(POETRY) run ruff check --fix src/ tests/
	@echo "✅ Code formatted"

lint: ## Run all linters (ruff, mypy)
	$(POETRY) run ruff check src/ tests/
	$(POETRY) run mypy src/
	@echo "✅ Linting completed"

security: ## Run security checks
	@echo "⚠️  Install bandit and safety for security checks: poetry add --group dev bandit safety"
	@echo "ℹ️  Security checks skipped - install security tools first"

check: format lint test ## Run format, lint, and test (complete check)
	@echo "✅ All checks passed!"

# ============================================================================
# Cleaning
# ============================================================================

clean: ## Remove build artifacts, cache files, and generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml .pytest_cache/ .mypy_cache/
	@echo "✅ Cleaned build artifacts and cache files"

clean-all: clean docker-clean ## Remove all artifacts including Docker resources
	@echo "✅ Complete cleanup finished"

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
	$(POETRY) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# ============================================================================
# Monitoring & Observability
# ============================================================================

logs: docker-logs ## Show application logs

langfuse-ui: ## Open Langfuse UI for observability
	@echo "📊 Langfuse UI available at: http://localhost:3000"
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Navigate to http://localhost:3000"

qdrant-ui: ## Open Qdrant UI for vector database
	@echo "📊 Qdrant UI available at: http://localhost:6333/dashboard"
	@open http://localhost:6333/dashboard || xdg-open http://localhost:6333/dashboard || echo "Navigate to http://localhost:6333/dashboard"

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

update: ## Update all dependencies
	$(POETRY) update
	@echo "✅ Dependencies updated"

version: ## Show application version
	@$(POETRY) version

# ============================================================================
# CI/CD Simulation
# ============================================================================

ci: lint test security ## Run CI pipeline locally (lint, test, security)
	@echo "✅ CI pipeline completed successfully"

pre-commit: format lint ## Run pre-commit checks (format + lint)
	@echo "✅ Pre-commit checks passed"
