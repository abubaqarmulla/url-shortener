
#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="smoke-$(date +%s)-$$@example.com"
PASSWORD="SmokeTest-Password-123!"

RESPONSE_BODY=""
HTTP_STATUS=""


request() {
    local method="$1"
    local path="$2"
    local data="${3:-}"
    local token="${4:-}"
    local content_type="${5:-application/json}"

    local args=(-sS -X "$method")

    if [[ -n "$data" ]]; then
        args+=(-H "Content-Type: $content_type")
        args+=(--data "$data")
    fi

    if [[ -n "$token" ]]; then
        args+=(-H "Authorization: Bearer $token")
    fi

    local response
    response=$(curl "${args[@]}" -w $'\n%{http_code}' "$BASE_URL$path")

    HTTP_STATUS="${response##*$'\n'}"
    RESPONSE_BODY="${response%$'\n'*}"
}

require_status() {
    local expected="$1"
    local step="$2"

    if [[ "$HTTP_STATUS" != "$expected" ]]; then
        echo "FAIL: $step (HTTP $HTTP_STATUS)"
        echo "Response: $RESPONSE_BODY"
        exit 1
    fi

    echo "PASS: $step (HTTP $HTTP_STATUS)"
}

json_value() {
    local key="$1"
    local body="$2"

    python3 -c \
        'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' \
        "$key" <<< "$body"
}

echo "Testing URL Shortener at $BASE_URL"
echo

echo "1. Health check"
request GET "/health"
require_status 200 "Health check"

echo
echo "2. Register user"
request POST "/auth/register" \
    "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
require_status 201 "User registration"

echo

echo
echo "3. Login"
LOGIN_DATA=$(python3 -c \
    'import urllib.parse,sys; print(urllib.parse.urlencode({"username":sys.argv[1],"password":sys.argv[2]}))' \
    "$EMAIL" "$PASSWORD")

request POST "/auth/login" "$LOGIN_DATA" "" "application/x-www-form-urlencoded"
require_status 200 "User login"

TOKEN=$(json_value access_token "$RESPONSE_BODY")

if [[ -z "$TOKEN" ]]; then
    echo "FAIL: Login did not return an access token"
    exit 1
fi

echo "PASS: Access token received"


echo
echo "4. Create shortened URL"
request POST "/urls/" \
    '{"original_url":"https://example.com/smoke-test"}' \
    "$TOKEN"
require_status 201 "Create shortened URL"

URL_ID=$(json_value id "$RESPONSE_BODY")
SHORT_CODE=$(json_value short_code "$RESPONSE_BODY")

echo "Created URL ID: $URL_ID"
echo "Short code: $SHORT_CODE"

echo
echo "5. List user's URLs"
request GET "/urls/" "" "$TOKEN"
require_status 200 "List user's URLs"

echo
echo "6. Test short URL redirect"
request GET "/$SHORT_CODE"
require_status 307 "Short URL redirect"

echo
echo "7. Retrieve click analytics"
request GET "/urls/$URL_ID/analytics" "" "$TOKEN"
require_status 200 "Retrieve click analytics"

echo "Analytics response:"
printf '%s\n' "$RESPONSE_BODY"

echo
echo "ALL SMOKE TESTS PASSED"
