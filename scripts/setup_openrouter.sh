#!/bin/bash

# OpenRouter Integration Setup Script
# This script sets up the complete OpenRouter integration

set -e

echo "🚀 Setting up OpenRouter Integration..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Step 1: Check environment file
echo "${YELLOW}📝 Step 1: Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo "   Creating .env from .env.example..."
    cp .env.example .env
    echo "   ⚠️  Please edit .env and add your OPENROUTER_API_KEY"
    echo "   Get your API key from: https://openrouter.ai/keys"
    echo ""
    read -p "   Press Enter after you've added your API key..."
fi
echo "${GREEN}   ✅ Environment file exists${NC}"
echo ""

# Step 2: Install dependencies
echo "${YELLOW}📦 Step 2: Installing dependencies...${NC}"
if command -v poetry &> /dev/null; then
    poetry install
    echo "${GREEN}   ✅ Dependencies installed${NC}"
else
    echo "   ⚠️  Poetry not found, skipping dependency installation"
    echo "   Install poetry: curl -sSL https://install.python-poetry.org | python3 -"
fi
echo ""

# Step 3: Database migrations
echo "${YELLOW}🗄️  Step 3: Running database migrations...${NC}"
if command -v alembic &> /dev/null; then
    alembic upgrade head
    echo "${GREEN}   ✅ Migrations applied${NC}"
else
    echo "   ⚠️  Alembic not found, please run manually:"
    echo "   alembic upgrade head"
fi
echo ""

# Step 4: Seed plan limits
echo "${YELLOW}🌱 Step 4: Seeding subscription plans...${NC}"
if [ -f "scripts/seed_plan_limits.py" ]; then
    python scripts/seed_plan_limits.py
    echo "${GREEN}   ✅ Subscription plans seeded${NC}"
else
    echo "   ⚠️  Seed script not found"
fi
echo ""

# Step 5: Run tests
echo "${YELLOW}🧪 Step 5: Running tests (optional)...${NC}"
read -p "   Run tests? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pytest tests/unit/test_openrouter_service.py -v
    pytest tests/unit/test_subscription_service.py -v
    pytest tests/unit/test_presets_service.py -v
    echo "${GREEN}   ✅ Tests passed${NC}"
fi
echo ""

# Summary
echo "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "📚 Next Steps:"
echo "   1. Start the server:"
echo "      uvicorn app.main:app --reload"
echo ""
echo "   2. Access API documentation:"
echo "      http://localhost:8000/docs"
echo ""
echo "   3. Test health check:"
echo "      curl http://localhost:8000/api/v1/health"
echo ""
echo "   4. Create your first conversation:"
echo "      curl -X POST http://localhost:8000/api/v1/conversations \\"
echo "        -H \"Authorization: Bearer \$TOKEN\" \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"mode\": \"standard\"}'"
echo ""
echo "📖 Documentation:"
echo "   - Integration Guide: docs/OPENROUTER_INTEGRATION.md"
echo "   - README: README_OPENROUTER.md"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "🎉 Happy coding!"
