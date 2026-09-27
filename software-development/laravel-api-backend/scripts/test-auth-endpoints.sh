#!/usr/bin/env bash
# Automated API Endpoint Tester for Laravel Sanctum REST APIs

BASE_URL="${1:-http://localhost/api}"
ADMIN_EMAIL="${2:-admin@pangudiluhur.sch.id}"
ADMIN_PASS="${3:-admin123}"

echo "=========================================="
echo "    Laravel API Endpoint Health Test"
echo "=========================================="
echo "Target URL: $BASE_URL"
echo "Timestamp:  $(date)"
echo "=========================================="
echo

# 1. Test Public Endpoint
echo "[1/4] Testing GET /categories (Public)..."
HTTP_CODE=$(curl -s -o /tmp/api_cat.json -w "%{http_code}" "$BASE_URL/categories")
if [ "$HTTP_CODE" -eq 200 ]; then
  echo "  ✅ PASS (HTTP 200)"
  cat /tmp/api_cat.json | jq -c '.categories[] | {id, name}' 2>/dev/null | head -3
else
  echo "  ❌ FAIL (HTTP $HTTP_CODE)"
  cat /tmp/api_cat.json
fi
echo

# 2. Test Login & Get Sanctum Token
echo "[2/4] Testing POST /login..."
TOKEN_RESP=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}")

TOKEN=$(echo "$TOKEN_RESP" | jq -r '.token // empty')

if [ -n "$TOKEN" ]; then
  echo "  ✅ PASS (Token received: ${TOKEN:0:15}...)"
else
  echo "  ❌ FAIL (No token in response)"
  echo "$TOKEN_RESP"
  exit 1
fi
echo

# 3. Test Protected Endpoint (/me)
echo "[3/4] Testing GET /me (Protected)..."
ME_RESP=$(curl -s "$BASE_URL/me" -H "Authorization: Bearer $TOKEN")
USER_EMAIL=$(echo "$ME_RESP" | jq -r '.user.email // empty')

if [ "$USER_EMAIL" = "$ADMIN_EMAIL" ]; then
  echo "  ✅ PASS (Authenticated as: $USER_EMAIL)"
else
  echo "  ❌ FAIL (Could not verify user)"
  echo "$ME_RESP"
fi
echo

# 4. Test Bookings Endpoint
echo "[4/4] Testing GET /bookings (Protected)..."
BOOKINGS_COUNT=$(curl -s "$BASE_URL/bookings" \
  -H "Authorization: Bearer $TOKEN" | jq '.bookings | length' 2>/dev/null)

if [ -n "$BOOKINGS_COUNT" ]; then
  echo "  ✅ PASS (Found $BOOKINGS_COUNT existing bookings)"
else
  echo "  ❌ FAIL (Could not fetch bookings)"
fi

echo
echo "=========================================="
echo "         Test Execution Complete"
echo "=========================================="
