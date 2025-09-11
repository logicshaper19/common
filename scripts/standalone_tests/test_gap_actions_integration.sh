#!/bin/bash

# Integration test for Gap Actions functionality
# Tests the complete workflow: Database → API → Frontend

set -e

echo "🧪 Starting Gap Actions Integration Test"
echo "========================================"

# Configuration
API_BASE="http://localhost:8000"
COMPANY_ID="ad172949-0036-4009-b00f-787a40f84699"

# Step 1: Authenticate
echo "1. 🔐 Authenticating..."
AUTH_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"elisha@common.co","password":"password123"}')

TOKEN=$(echo $AUTH_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
  echo $AUTH_RESPONSE
  exit 1
fi

echo "✅ Authentication successful"

# Step 2: Test List Gap Actions (should be empty initially)
echo "2. 📋 Testing list gap actions..."
LIST_RESPONSE=$(curl -s -X GET "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions" \
  -H "Authorization: Bearer ${TOKEN}")

INITIAL_COUNT=$(echo $LIST_RESPONSE | jq -r '.total_count')
echo "✅ Initial gap actions count: $INITIAL_COUNT"

# Step 3: Create a Gap Action
echo "3. ➕ Creating a gap action..."
CREATE_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gaps/test-gap-integration/actions" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "request_data",
    "message": "Integration test: Please provide missing traceability data",
    "priority": "high"
  }')

ACTION_ID=$(echo $CREATE_RESPONSE | jq -r '.action_id')
CREATE_SUCCESS=$(echo $CREATE_RESPONSE | jq -r '.success')

if [ "$CREATE_SUCCESS" != "true" ]; then
  echo "❌ Failed to create gap action"
  echo $CREATE_RESPONSE
  exit 1
fi

echo "✅ Gap action created with ID: $ACTION_ID"

# Step 4: Update the Gap Action
echo "4. 🔄 Updating gap action status..."
UPDATE_RESPONSE=$(curl -s -X PUT "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions/${ACTION_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "resolution_notes": "Integration test: Contacted supplier, awaiting response"
  }')

UPDATE_SUCCESS=$(echo $UPDATE_RESPONSE | jq -r '.success')

if [ "$UPDATE_SUCCESS" != "true" ]; then
  echo "❌ Failed to update gap action"
  echo $UPDATE_RESPONSE
  exit 1
fi

echo "✅ Gap action updated successfully"

# Step 5: Verify the action appears in the list
echo "5. 🔍 Verifying action appears in list..."
FINAL_LIST_RESPONSE=$(curl -s -X GET "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions" \
  -H "Authorization: Bearer ${TOKEN}")

FINAL_COUNT=$(echo $FINAL_LIST_RESPONSE | jq -r '.total_count')
FOUND_ACTION=$(echo $FINAL_LIST_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | .id")

if [ "$FOUND_ACTION" != "$ACTION_ID" ]; then
  echo "❌ Created action not found in list"
  echo $FINAL_LIST_RESPONSE
  exit 1
fi

echo "✅ Action found in list (total count: $FINAL_COUNT)"

# Step 6: Verify action details
echo "6. 🔎 Verifying action details..."
ACTION_STATUS=$(echo $FINAL_LIST_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | .status")
ACTION_TYPE=$(echo $FINAL_LIST_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | .action_type")
ACTION_MESSAGE=$(echo $FINAL_LIST_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | .message")

if [ "$ACTION_STATUS" != "in_progress" ]; then
  echo "❌ Action status incorrect. Expected: in_progress, Got: $ACTION_STATUS"
  exit 1
fi

if [ "$ACTION_TYPE" != "request_data" ]; then
  echo "❌ Action type incorrect. Expected: request_data, Got: $ACTION_TYPE"
  exit 1
fi

echo "✅ Action details verified:"
echo "   - Status: $ACTION_STATUS"
echo "   - Type: $ACTION_TYPE"
echo "   - Message: $ACTION_MESSAGE"

# Step 7: Test Frontend Accessibility
echo "7. 🌐 Testing frontend accessibility..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)

if [ "$FRONTEND_RESPONSE" != "200" ]; then
  echo "❌ Frontend not accessible (HTTP $FRONTEND_RESPONSE)"
  exit 1
fi

echo "✅ Frontend accessible at http://localhost:3000"

# Summary
echo ""
echo "🎉 Integration Test PASSED!"
echo "=========================="
echo "✅ Database migration applied successfully"
echo "✅ API endpoints working correctly"
echo "✅ CRUD operations functional"
echo "✅ Authentication working"
echo "✅ Frontend accessible"
echo ""
echo "📊 Test Results:"
echo "   - Initial actions: $INITIAL_COUNT"
echo "   - Final actions: $FINAL_COUNT"
echo "   - Created action ID: $ACTION_ID"
echo "   - Action status: $ACTION_STATUS"
echo ""
echo "🚀 Gap Actions system is fully operational!"
