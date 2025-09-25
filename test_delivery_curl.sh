#!/bin/bash

# Simple curl tests for delivery API endpoints
# Replace YOUR_PO_ID and YOUR_TOKEN with actual values

PO_ID="YOUR_PO_ID"
TOKEN="YOUR_TOKEN"
API_URL="http://localhost:8000"

echo "🚚 Testing Delivery API with curl"
echo "=================================="

echo ""
echo "1. Get delivery information:"
echo "curl -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     $API_URL/api/v1/purchase-orders/\$PO_ID/delivery"
echo ""

echo "2. Update delivery status to 'in_transit':"
echo "curl -X PATCH \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"status\": \"in_transit\", \"notes\": \"Package picked up\"}' \\"
echo "     $API_URL/api/v1/purchase-orders/\$PO_ID/delivery"
echo ""

echo "3. Mark as delivered:"
echo "curl -X PATCH \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"status\": \"delivered\", \"notes\": \"Successfully delivered\"}' \\"
echo "     $API_URL/api/v1/purchase-orders/\$PO_ID/delivery"
echo ""

echo "4. Get delivery history:"
echo "curl -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     $API_URL/api/v1/purchase-orders/\$PO_ID/delivery/history"
echo ""

echo "=================================="
echo "🎯 To run actual tests:"
echo "1. Replace YOUR_PO_ID with actual purchase order ID"
echo "2. Replace YOUR_TOKEN with valid auth token"
echo "3. Make sure API server is running"
echo "4. Run: bash test_delivery_curl.sh"
