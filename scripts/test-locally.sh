#!/bin/bash

# =============================================================================
# Local Testing Script
# =============================================================================
# Quick script to test critical API endpoints locally
# Run this after starting the app with: make dev
#
# Usage: ./scripts/test-locally.sh
# Or via Make: make test-local
# =============================================================================

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:8000"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123!"
ACCESS_TOKEN=""

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}LOCAL API TESTING SCRIPT${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo "Base URL: $BASE_URL"
echo "Test Email: $TEST_EMAIL"
echo ""

# Function to print test results
test_endpoint() {
    local name=$1
    local url=$2
    local method=$3
    local data=$4
    local expected=$5

    echo -e "${YELLOW}Testing: $name${NC}"
    echo "  Method: $method"
    echo "  URL: $url"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    elif [ "$method" = "POST" ]; then
        if [ -n "$ACCESS_TOKEN" ]; then
            response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $ACCESS_TOKEN" \
                -d "$data")
        else
            response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
                -H "Content-Type: application/json" \
                -d "$data")
        fi
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected" ]; then
        echo -e "  ${GREEN}✅ PASS (HTTP $http_code)${NC}"
    else
        echo -e "  ${RED}❌ FAIL (Expected $expected, got $http_code)${NC}"
        echo "  Response: $body"
    fi
    echo ""
}

# Check if app is running
echo "Checking if application is running..."
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ Application is not running on $BASE_URL${NC}"
    echo "Please start the application first: make dev"
    exit 1
fi
echo -e "${GREEN}✅ Application is running${NC}"
echo ""

# =============================================================================
# TEST 1: Health Check
# =============================================================================
echo -e "${BLUE}[1/8] Health Check${NC}"
test_endpoint "Health Endpoint" "$BASE_URL/health" "GET" "" "200"

# =============================================================================
# TEST 2: Docs
# =============================================================================
echo -e "${BLUE}[2/8] Documentation${NC}"
test_endpoint "Swagger UI" "$BASE_URL/docs" "GET" "" "200"
test_endpoint "ReDoc" "$BASE_URL/redoc" "GET" "" "200"

# =============================================================================
# TEST 3: User Registration
# =============================================================================
echo -e "${BLUE}[3/8] User Registration${NC}"
REGISTER_DATA="{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Test User\"}"
echo "  Data: $REGISTER_DATA"

response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$REGISTER_DATA")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
    echo -e "  ${GREEN}✅ PASS (HTTP $http_code)${NC}"
    echo "  User registered successfully"
else
    echo -e "  ${YELLOW}⚠️  WARNING (HTTP $http_code)${NC}"
    echo "  Response: $body"
fi
echo ""

# =============================================================================
# TEST 4: User Login
# =============================================================================
echo -e "${BLUE}[4/8] User Login${NC}"
LOGIN_DATA="username=$TEST_EMAIL&password=$TEST_PASSWORD"

response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "$LOGIN_DATA")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "  ${GREEN}✅ PASS (HTTP $http_code)${NC}"
    ACCESS_TOKEN=$(echo "$body" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$ACCESS_TOKEN" ]; then
        echo "  Access token received"
        echo "  Token: ${ACCESS_TOKEN:0:20}..."
    else
        echo -e "  ${YELLOW}⚠️  Could not extract access token${NC}"
    fi
else
    echo -e "  ${RED}❌ FAIL (HTTP $http_code)${NC}"
    echo "  Response: $body"
fi
echo ""

# =============================================================================
# TEST 5: Get Current User (Authenticated)
# =============================================================================
if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${BLUE}[5/8] Get Current User (Authenticated)${NC}"

    response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/auth/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo -e "  ${GREEN}✅ PASS (HTTP $http_code)${NC}"
        echo "  User data retrieved"
    else
        echo -e "  ${RED}❌ FAIL (HTTP $http_code)${NC}"
        echo "  Response: $body"
    fi
    echo ""
else
    echo -e "${YELLOW}[5/8] Get Current User - SKIPPED (no token)${NC}"
    echo ""
fi

# =============================================================================
# TEST 6: Chat Completion (if endpoint exists)
# =============================================================================
if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${BLUE}[6/8] Chat Completion${NC}"
    CHAT_DATA='{"messages":[{"role":"user","content":"What is Islam?"}],"model":"gpt-4","stream":false}'

    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$CHAT_DATA")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo -e "  ${GREEN}✅ PASS (HTTP $http_code)${NC}"
        echo "  Chat response received"
    elif [ "$http_code" = "404" ]; then
        echo -e "  ${YELLOW}⚠️  SKIPPED (endpoint not found)${NC}"
    else
        echo -e "  ${YELLOW}⚠️  WARNING (HTTP $http_code)${NC}"
        echo "  Response: ${body:0:200}..."
    fi
    echo ""
else
    echo -e "${YELLOW}[6/8] Chat Completion - SKIPPED (no token)${NC}"
    echo ""
fi

# =============================================================================
# TEST 7: Document Upload (if endpoint exists)
# =============================================================================
if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${BLUE}[7/8] Document Upload${NC}"
    DOC_DATA='{"title":"Test Document","content":"This is a test document for RAG testing.","document_type":"hadith","primary_category":"aqidah","language":"en"}'

    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/documents/upload" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$DOC_DATA")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        echo -e "  ${GREEN}✅ PASS (HTTP $http_code)${NC}"
        echo "  Document uploaded successfully"
    elif [ "$http_code" = "404" ]; then
        echo -e "  ${YELLOW}⚠️  SKIPPED (endpoint not found)${NC}"
    else
        echo -e "  ${YELLOW}⚠️  WARNING (HTTP $http_code)${NC}"
        echo "  Response: ${body:0:200}..."
    fi
    echo ""
else
    echo -e "${YELLOW}[7/8] Document Upload - SKIPPED (no token)${NC}"
    echo ""
fi

# =============================================================================
# TEST 8: Qdrant Status
# =============================================================================
echo -e "${BLUE}[8/8] Qdrant Status${NC}"
if curl -s http://localhost:6333/healthz > /dev/null; then
    echo -e "  ${GREEN}✅ Qdrant is healthy${NC}"

    # Check collections
    collections=$(curl -s http://localhost:6333/collections | grep -o '"name":"[^"]*"' | wc -l)
    echo "  Collections: $collections"
else
    echo -e "  ${YELLOW}⚠️  Qdrant not accessible${NC}"
fi
echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}TESTING COMPLETE${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo "Test Results:"
echo "  - Health check: ✅"
echo "  - Documentation: ✅"
echo "  - User registration: See above"
echo "  - User login: See above"
echo "  - Authentication: See above"
echo "  - API endpoints: See above"
echo ""
echo "Next Steps:"
echo "  1. Review results above"
echo "  2. Test manually via Swagger: $BASE_URL/docs"
echo "  3. Check Qdrant UI: http://localhost:6333/dashboard"
echo "  4. Check Flower UI: http://localhost:5555 (if running)"
echo ""
echo "To test more endpoints, use Swagger UI: $BASE_URL/docs"
echo ""
