#!/bin/bash

# =============================================================================
# Pre-Build Verification Script
# =============================================================================
# This script runs all necessary checks before building the Docker image.
# Use this to ensure everything is ready for production deployment.
#
# Usage: ./scripts/verify-before-build.sh
# Or via Make: make verify-build
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_step() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo ""
    echo -e "${YELLOW}[$TOTAL_CHECKS] $1${NC}"
}

print_success() {
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# =============================================================================
# START VERIFICATION
# =============================================================================

clear
print_header "PRE-BUILD VERIFICATION SCRIPT"
echo "This script will verify that your application is ready for Docker build."
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# =============================================================================
# PHASE 1: ENVIRONMENT CHECKS
# =============================================================================

print_header "PHASE 1: ENVIRONMENT CHECKS"

# Check if .env file exists
print_step "Checking .env file exists"
if [ -f .env ]; then
    print_success ".env file found"
else
    print_error ".env file not found"
    print_info "Run: cp .env.example .env"
    exit 1
fi

# Check if Poetry is installed
print_step "Checking Poetry installation"
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version)
    print_success "Poetry installed: $POETRY_VERSION"
else
    print_error "Poetry not installed"
    print_info "Install: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if Docker is running
print_step "Checking Docker is running"
if docker info &> /dev/null; then
    print_success "Docker is running"
else
    print_error "Docker is not running"
    print_info "Start Docker Desktop or Docker daemon"
    exit 1
fi

# Check if Docker Compose is available
print_step "Checking Docker Compose"
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    print_success "Docker Compose available: $COMPOSE_VERSION"
else
    print_error "Docker Compose not available"
    exit 1
fi

# =============================================================================
# PHASE 2: DOCKER SERVICES CHECK
# =============================================================================

print_header "PHASE 2: DOCKER SERVICES CHECK"

# Check PostgreSQL
print_step "Checking PostgreSQL service"
if docker exec shia-chatbot-postgres pg_isready -U postgres &> /dev/null; then
    print_success "PostgreSQL is healthy"
else
    print_error "PostgreSQL is not running"
    print_info "Run: make docker-up"
    exit 1
fi

# Check Redis
print_step "Checking Redis service"
if docker exec shia-chatbot-redis redis-cli ping &> /dev/null; then
    print_success "Redis is healthy"
else
    print_error "Redis is not running"
    print_info "Run: make docker-up"
    exit 1
fi

# Check Qdrant
print_step "Checking Qdrant service"
if curl -s http://localhost:6333/healthz &> /dev/null; then
    print_success "Qdrant is healthy"
else
    print_warning "Qdrant is not running (optional)"
fi

# =============================================================================
# PHASE 3: CODE QUALITY CHECKS
# =============================================================================

print_header "PHASE 3: CODE QUALITY CHECKS"

# Check code formatting
print_step "Checking code formatting (Black)"
if uv run black --check src/ tests/ &> /dev/null; then
    print_success "Code is properly formatted"
else
    print_error "Code formatting issues found"
    print_info "Run: make format"
    exit 1
fi

# Check import sorting
print_step "Checking import sorting (isort)"
if uv run isort --check-only src/ tests/ &> /dev/null; then
    print_success "Imports are properly sorted"
else
    print_error "Import sorting issues found"
    print_info "Run: make format"
    exit 1
fi

# Check flake8
print_step "Checking linting (flake8)"
if uv run flake8 src/ tests/ --max-line-length=100 --statistics &> /dev/null; then
    print_success "Flake8 checks passed"
else
    print_error "Flake8 found issues"
    print_info "Run: make lint-flake8"
    exit 1
fi

# Check mypy
print_step "Checking type hints (mypy)"
if uv run mypy src/ --ignore-missing-imports --show-error-codes &> /dev/null; then
    print_success "Type checking passed"
else
    print_warning "Type checking found issues (non-critical)"
    print_info "Review: make lint-mypy"
fi

# =============================================================================
# PHASE 4: SECURITY CHECKS
# =============================================================================

print_header "PHASE 4: SECURITY CHECKS"

# Check for secrets
print_step "Scanning for hardcoded secrets"
if uv run detect-secrets scan --baseline .secrets.baseline &> /dev/null; then
    print_success "No new secrets detected"
else
    print_error "Potential secrets found in code"
    print_info "Run: make security-secrets"
    exit 1
fi

# Check Bandit
print_step "Running security scan (Bandit)"
if uv run bandit -r src/ -c pyproject.toml -ll &> /dev/null; then
    print_success "No high-severity security issues"
else
    print_warning "Security issues found (review recommended)"
    print_info "Run: make security-bandit"
fi

# Check dependency vulnerabilities
print_step "Checking dependency vulnerabilities (Safety)"
if uv run safety check --json &> /dev/null; then
    print_success "No known vulnerabilities in dependencies"
else
    print_warning "Vulnerable dependencies found (review recommended)"
    print_info "Run: make security-safety"
fi

# =============================================================================
# PHASE 5: DATABASE CHECKS
# =============================================================================

print_header "PHASE 5: DATABASE CHECKS"

# Check migrations
print_step "Checking database migrations status"
CURRENT_MIGRATION=$(uv run alembic current 2>/dev/null | grep -v "INFO" || echo "none")
if [ "$CURRENT_MIGRATION" != "none" ]; then
    print_success "Database is migrated: $CURRENT_MIGRATION"
else
    print_warning "No migrations applied"
    print_info "Run: make db-upgrade"
fi

# Check if there are pending migrations
print_step "Checking for pending migrations"
PENDING=$(uv run alembic check 2>&1 || true)
if echo "$PENDING" | grep -q "No new upgrade operations detected"; then
    print_success "No pending migrations"
elif echo "$PENDING" | grep -q "Target database is not up to date"; then
    print_error "Pending migrations detected"
    print_info "Run: make db-upgrade"
    exit 1
else
    print_success "Migrations are up to date"
fi

# =============================================================================
# PHASE 6: TESTING
# =============================================================================

print_header "PHASE 6: TESTING"

# Run unit tests
print_step "Running unit tests"
if uv run pytest tests/unit/ -v --tb=short &> /tmp/unit-tests.log; then
    UNIT_COUNT=$(grep -o "passed" /tmp/unit-tests.log | wc -l)
    print_success "Unit tests passed ($UNIT_COUNT tests)"
else
    print_error "Unit tests failed"
    print_info "Run: make test-unit"
    echo "Last 20 lines of output:"
    tail -20 /tmp/unit-tests.log
    exit 1
fi

# Run integration tests
print_step "Running integration tests"
if uv run pytest tests/integration/ -v --tb=short &> /tmp/integration-tests.log; then
    INTEGRATION_COUNT=$(grep -o "passed" /tmp/integration-tests.log | wc -l)
    print_success "Integration tests passed ($INTEGRATION_COUNT tests)"
else
    print_warning "Integration tests failed (review recommended)"
    print_info "Run: make test-integration"
    echo "Last 20 lines of output:"
    tail -20 /tmp/integration-tests.log
fi

# Check test coverage
print_step "Checking test coverage"
COVERAGE_REPORT=$(uv run pytest tests/ --cov=src/app --cov-report=term-missing 2>&1 | grep "TOTAL" || echo "TOTAL 0%")
COVERAGE_PERCENT=$(echo "$COVERAGE_REPORT" | grep -oP '\d+%' | tail -1 | tr -d '%')

if [ "$COVERAGE_PERCENT" -ge 75 ]; then
    print_success "Test coverage: ${COVERAGE_PERCENT}% (>= 75% required)"
elif [ "$COVERAGE_PERCENT" -ge 60 ]; then
    print_warning "Test coverage: ${COVERAGE_PERCENT}% (< 75% recommended)"
else
    print_warning "Test coverage: ${COVERAGE_PERCENT}% (low coverage)"
fi

# =============================================================================
# PHASE 7: APPLICATION HEALTH CHECK
# =============================================================================

print_header "PHASE 7: APPLICATION HEALTH CHECK"

# Start app in background for health check
print_step "Starting application for health check"
print_info "Starting FastAPI server..."

# Kill any existing processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start app in background
uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 &> /tmp/app-startup.log &
APP_PID=$!

# Wait for app to start (max 30 seconds)
print_info "Waiting for application to start (max 30 seconds)..."
COUNTER=0
while [ $COUNTER -lt 30 ]; do
    if curl -s http://localhost:8000/health &> /dev/null; then
        print_success "Application started successfully"
        break
    fi
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq 30 ]; then
    print_error "Application failed to start within 30 seconds"
    echo "Startup log:"
    cat /tmp/app-startup.log
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

# Check health endpoint
print_step "Checking health endpoint"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_success "Health endpoint responding: healthy"
else
    print_error "Health endpoint not responding properly"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

# Check Swagger docs
print_step "Checking Swagger documentation"
if curl -s http://localhost:8000/docs | grep -q "Swagger UI"; then
    print_success "Swagger UI is accessible"
else
    print_warning "Swagger UI may not be accessible"
fi

# Cleanup: Stop the app
print_info "Stopping test application..."
kill $APP_PID 2>/dev/null || true
sleep 2

# =============================================================================
# PHASE 8: GIT CHECKS
# =============================================================================

print_header "PHASE 8: GIT CHECKS"

# Check if working tree is clean
print_step "Checking git working tree"
if git diff-index --quiet HEAD --; then
    print_success "Working tree is clean"
else
    print_warning "Uncommitted changes detected"
    print_info "Consider committing changes before building"
fi

# Check current branch
print_step "Checking git branch"
CURRENT_BRANCH=$(git branch --show-current)
print_info "Current branch: $CURRENT_BRANCH"

# =============================================================================
# SUMMARY
# =============================================================================

print_header "VERIFICATION SUMMARY"

echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║  ✅ ALL CHECKS PASSED - READY TO BUILD DOCKER IMAGE! ✅   ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Build Docker image:    make build"
    echo "  2. Deploy to staging:     make deploy-staging"
    echo "  3. Deploy to production:  make deploy-prod"
    echo ""

    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Note: $WARNINGS warning(s) found. Review recommended but not blocking.${NC}"
        echo ""
    fi

    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                            ║${NC}"
    echo -e "${RED}║  ❌ VERIFICATION FAILED - DO NOT BUILD YET! ❌            ║${NC}"
    echo -e "${RED}║                                                            ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please fix the issues above before building the Docker image."
    echo ""
    echo "Common fixes:"
    echo "  • Format code:        make format"
    echo "  • Fix linting:        make lint"
    echo "  • Run migrations:     make db-upgrade"
    echo "  • Fix tests:          make test"
    echo "  • Start services:     make docker-up"
    echo ""
    exit 1
fi
