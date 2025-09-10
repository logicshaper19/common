#!/bin/bash

# API Endpoints Comprehensive Test
# Tests all major API endpoints for functionality and response format

set -e

echo "🔌 API Endpoints Comprehensive Test"
echo "==================================="

API_BASE="http://localhost:8000"
COMPANY_ID="ad172949-0036-4009-b00f-787a40f84699"

# Authenticate first
AUTH_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"elisha@common.co","password":"password123"}')

TOKEN=$(echo $AUTH_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
  exit 1
fi

echo "✅ Authentication successful"

# Test all major endpoints
echo ""
echo "📋 Testing Core API Endpoints..."

# 1. Purchase Orders
echo "1. Purchase Orders API:"
curl -s -X GET "${API_BASE}/api/v1/purchase-orders/" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if type == "array" then "✅ GET /purchase-orders - \(length) orders" else "❌ GET /purchase-orders - Invalid response" end'

# 2. Companies
echo "2. Companies API:"
curl -s -X GET "${API_BASE}/api/v1/companies/${COMPANY_ID}" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if .id then "✅ GET /companies/{id} - Company found" else "❌ GET /companies/{id} - No company data" end'

# 3. Products
echo "3. Products API:"
curl -s -X GET "${API_BASE}/api/v1/products/" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if type == "array" then "✅ GET /products - \(length) products" else "❌ GET /products - Invalid response" end'

# 4. Documents
echo "4. Documents API:"
curl -s -X GET "${API_BASE}/api/v1/documents/company/${COMPANY_ID}" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if type == "array" then "✅ GET /documents/company/{id} - \(length) documents" else "❌ GET /documents/company/{id} - Invalid response" end'

# 5. Transparency Dashboard
echo "5. Transparency Dashboard API:"
TRANSPARENCY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "${API_BASE}/api/v2/companies/${COMPANY_ID}/transparency-dashboard" \
  -H "Authorization: Bearer ${TOKEN}")

if [ "$TRANSPARENCY_STATUS" = "200" ]; then
  echo "✅ GET /api/v2/companies/{id}/transparency-dashboard - Working"
else
  echo "❌ GET /api/v2/companies/{id}/transparency-dashboard - Status: $TRANSPARENCY_STATUS"
fi

# 6. Gap Actions
echo "6. Gap Actions API:"
curl -s -X GET "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if .total_count then "✅ GET /gap-actions - \(.total_count) actions" else "❌ GET /gap-actions - Invalid response" end'

# 7. Recent Improvements
echo "7. Recent Improvements API:"
IMPROVEMENTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "${API_BASE}/api/v2/companies/${COMPANY_ID}/recent-improvements" \
  -H "Authorization: Bearer ${TOKEN}")

if [ "$IMPROVEMENTS_STATUS" = "200" ]; then
  echo "✅ GET /api/v2/companies/{id}/recent-improvements - Working"
elif [ "$IMPROVEMENTS_STATUS" = "404" ]; then
  echo "⚠️  GET /api/v2/companies/{id}/recent-improvements - Not implemented"
else
  echo "❌ GET /api/v2/companies/{id}/recent-improvements - Status: $IMPROVEMENTS_STATUS"
fi

# 8. Business Relationships
echo "8. Business Relationships API:"
curl -s -X GET "${API_BASE}/api/v1/business-relationships/" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if type == "array" then "✅ GET /business-relationships - \(length) relationships" else "❌ GET /business-relationships - Invalid response" end'

# 9. Batches
echo "9. Batches API:"
curl -s -X GET "${API_BASE}/api/v1/batches/" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if type == "array" then "✅ GET /batches - \(length) batches" else "❌ GET /batches - Invalid response" end'

# 10. Users
echo "10. Users API:"
curl -s -X GET "${API_BASE}/api/v1/users/me" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r 'if .id then "✅ GET /users/me - User profile loaded" else "❌ GET /users/me - No user data" end'

echo ""
echo "🎯 API Endpoints Test Complete!"
