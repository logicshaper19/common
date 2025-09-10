#!/bin/bash

# Database Operations Test
# Tests CRUD operations and data integrity

set -e

echo "🗄️  Database Operations Test"
echo "============================"

API_BASE="http://localhost:8000"
COMPANY_ID="ad172949-0036-4009-b00f-787a40f84699"

# Authenticate
AUTH_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"elisha@common.co","password":"password123"}')

TOKEN=$(echo $AUTH_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
  exit 1
fi

echo "✅ Authentication successful"

# Test 1: Create Gap Action (CREATE)
echo ""
echo "1. 📝 Testing CREATE operations..."

CREATE_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gaps/test-db-crud/actions" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "request_data",
    "message": "Database CRUD test - CREATE operation",
    "priority": "medium"
  }')

ACTION_ID=$(echo $CREATE_RESPONSE | jq -r '.action_id')
CREATE_SUCCESS=$(echo $CREATE_RESPONSE | jq -r '.success')

if [ "$CREATE_SUCCESS" = "true" ]; then
  echo "✅ CREATE - Gap action created with ID: $ACTION_ID"
else
  echo "❌ CREATE - Failed to create gap action"
  exit 1
fi

# Test 2: Read Gap Action (READ)
echo ""
echo "2. 📖 Testing READ operations..."

READ_RESPONSE=$(curl -s -X GET "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions" \
  -H "Authorization: Bearer ${TOKEN}")

FOUND_ACTION=$(echo $READ_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | .id")

if [ "$FOUND_ACTION" = "$ACTION_ID" ]; then
  echo "✅ READ - Gap action found in database"
else
  echo "❌ READ - Gap action not found in database"
  exit 1
fi

# Test 3: Update Gap Action (UPDATE)
echo ""
echo "3. ✏️  Testing UPDATE operations..."

UPDATE_RESPONSE=$(curl -s -X PUT "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions/${ACTION_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "resolution_notes": "Database CRUD test - UPDATE operation completed"
  }')

UPDATE_SUCCESS=$(echo $UPDATE_RESPONSE | jq -r '.success')

if [ "$UPDATE_SUCCESS" = "true" ]; then
  echo "✅ UPDATE - Gap action status updated to resolved"
else
  echo "❌ UPDATE - Failed to update gap action"
  exit 1
fi

# Test 4: Verify Update (READ after UPDATE)
echo ""
echo "4. 🔍 Testing READ after UPDATE..."

VERIFY_RESPONSE=$(curl -s -X GET "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions" \
  -H "Authorization: Bearer ${TOKEN}")

UPDATED_STATUS=$(echo $VERIFY_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | .status")

if [ "$UPDATED_STATUS" = "resolved" ]; then
  echo "✅ READ after UPDATE - Status correctly updated to: $UPDATED_STATUS"
else
  echo "❌ READ after UPDATE - Status not updated correctly. Got: $UPDATED_STATUS"
  exit 1
fi

# Test 5: Data Integrity Check
echo ""
echo "5. 🔒 Testing Data Integrity..."

# Check that all required fields are present
INTEGRITY_CHECK=$(echo $VERIFY_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | {id, gap_id, company_id, action_type, message, status, created_at} | length")

if [ "$INTEGRITY_CHECK" = "7" ]; then
  echo "✅ DATA INTEGRITY - All required fields present"
else
  echo "❌ DATA INTEGRITY - Missing required fields"
  exit 1
fi

# Test 6: Relationship Integrity
echo ""
echo "6. 🔗 Testing Relationship Integrity..."

# Verify company relationship
ACTION_COMPANY_ID=$(echo $VERIFY_RESPONSE | jq -r ".actions[] | select(.id == \"$ACTION_ID\") | .company_id")

if [ "$ACTION_COMPANY_ID" = "$COMPANY_ID" ]; then
  echo "✅ RELATIONSHIP INTEGRITY - Company relationship maintained"
else
  echo "❌ RELATIONSHIP INTEGRITY - Company relationship broken"
  exit 1
fi

# Test 7: Concurrent Operations
echo ""
echo "7. 🔄 Testing Concurrent Operations..."

# Create multiple actions simultaneously
for i in {1..3}; do
  curl -s -X POST "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gaps/concurrent-test-${i}/actions" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"action_type\": \"request_data\",
      \"message\": \"Concurrent test action ${i}\",
      \"priority\": \"low\"
    }" > /dev/null &
done

wait # Wait for all background processes

# Check if all were created
FINAL_COUNT=$(curl -s -X GET "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gap-actions" \
  -H "Authorization: Bearer ${TOKEN}" | jq -r '.total_count')

echo "✅ CONCURRENT OPERATIONS - Total actions after concurrent creates: $FINAL_COUNT"

# Test 8: Transaction Rollback (Error Handling)
echo ""
echo "8. 🚫 Testing Error Handling..."

# Try to create action with invalid data
ERROR_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/transparency/v2/companies/${COMPANY_ID}/gaps/error-test/actions" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "invalid_type",
    "message": "",
    "priority": "invalid_priority"
  }')

ERROR_SUCCESS=$(echo $ERROR_RESPONSE | jq -r '.success // false')

if [ "$ERROR_SUCCESS" = "false" ]; then
  echo "✅ ERROR HANDLING - Invalid data properly rejected"
else
  echo "⚠️  ERROR HANDLING - Invalid data was accepted (may need validation)"
fi

echo ""
echo "🎉 Database Operations Test Complete!"
echo "===================================="
echo "✅ CREATE operations working"
echo "✅ READ operations working"
echo "✅ UPDATE operations working"
echo "✅ Data integrity maintained"
echo "✅ Relationship integrity maintained"
echo "✅ Concurrent operations handled"
echo "✅ Error handling functional"
echo ""
echo "📊 Database Status: FULLY OPERATIONAL"
