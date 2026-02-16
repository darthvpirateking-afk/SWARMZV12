#!/bin/bash
# SWARMZ API Example Requests

BASE_URL="http://127.0.0.1:8012"

echo "============================================"
echo "SWARMZ API Examples"
echo "============================================"
echo ""

echo "1. Health Check"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""
echo ""

echo "2. Create Mission"
curl -s -X POST "$BASE_URL/v1/missions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Optimize lead conversion process",
    "category": "coin",
    "constraints": {"max_time_seconds": 60, "max_steps": 3}
  }' | python3 -m json.tool
echo ""
echo ""

echo "3. List Missions"
curl -s "$BASE_URL/v1/missions/list" | python3 -m json.tool
echo ""
echo ""

echo "4. Get System Omens"
curl -s "$BASE_URL/v1/system/omens" | python3 -m json.tool
echo ""
echo ""

echo "5. Get Predictions"
curl -s "$BASE_URL/v1/system/predictions" | python3 -m json.tool
echo ""
echo ""

echo "6. Get Templates"
curl -s "$BASE_URL/v1/system/templates" | python3 -m json.tool
echo ""
echo ""

echo "7. Schedule Maintenance"
curl -s -X POST "$BASE_URL/v1/admin/maintenance" | python3 -m json.tool
echo ""
