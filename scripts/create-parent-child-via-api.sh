#!/usr/bin/env bash
# Create a parent account (public) then a linked child (JWT as parent).
# Requires backend running, e.g.: docker compose --profile back up
# Requires: python3 (stdlib only)
#
# Usage:
#   chmod +x scripts/create-parent-child-via-api.sh
#   ./scripts/create-parent-child-via-api.sh
#   BASE_URL=https://example.com ./scripts/create-parent-child-via-api.sh
#
# Optional env (defaults shown):
#   PARENT_USER, PARENT_PASS, PARENT_EMAIL, FIRST_NAME, LAST_NAME
#   CHILD_USER, CHILD_PASS, NICKNAME, BIRTH_YEAR, GENDER (male|female)

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
SUFFIX="${SUFFIX:-$(date +%s)}"

PARENT_USER="${PARENT_USER:-parent_${SUFFIX}}"
PARENT_PASS="${PARENT_PASS:-TestParent123!}"
PARENT_EMAIL="${PARENT_EMAIL:-parent_${SUFFIX}@example.com}"
FIRST_NAME="${FIRST_NAME:-Test}"
LAST_NAME="${LAST_NAME:-Parent}"

CHILD_USER="${CHILD_USER:-child_${SUFFIX}}"
CHILD_PASS="${CHILD_PASS:-ChildPass123!}"
NICKNAME="${NICKNAME:-Kid}"
# Age 6–13: birth_year must satisfy validator (current year - birth_year in [6,13])
BIRTH_YEAR="${BIRTH_YEAR:-2016}"
GENDER="${GENDER:-male}"

export BASE_URL PARENT_USER PARENT_PASS PARENT_EMAIL FIRST_NAME LAST_NAME
export CHILD_USER CHILD_PASS NICKNAME BIRTH_YEAR GENDER

PARENT_BODY=$(python3 - <<'PY'
import json, os
print(json.dumps({
    "username": os.environ["PARENT_USER"],
    "password": os.environ["PARENT_PASS"],
    "email": os.environ["PARENT_EMAIL"],
    "first_name": os.environ["FIRST_NAME"],
    "last_name": os.environ["LAST_NAME"],
}))
PY
)

echo "==> 1. Register parent: ${PARENT_USER}"
curl -sS -X POST "${BASE_URL}/api/auth/register/parent/" \
  -H "Content-Type: application/json" \
  -d "$PARENT_BODY"
echo
echo

LOGIN_BODY=$(python3 - <<'PY'
import json, os
print(json.dumps({
    "username": os.environ["PARENT_USER"],
    "password": os.environ["PARENT_PASS"],
}))
PY
)

echo "==> 2. Login as parent"
LOGIN_JSON=$(curl -sS -X POST "${BASE_URL}/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_BODY")
echo "$LOGIN_JSON"
echo
ACCESS=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('access') or '')" "$LOGIN_JSON")
if [[ -z "$ACCESS" ]]; then
  echo "Login failed — check response above." >&2
  exit 1
fi

CHILD_BODY=$(python3 - <<'PY'
import json, os
print(json.dumps({
    "username": os.environ["CHILD_USER"],
    "password": os.environ["CHILD_PASS"],
    "nickname": os.environ["NICKNAME"],
    "birth_year": int(os.environ["BIRTH_YEAR"]),
    "gender": os.environ["GENDER"],
}))
PY
)

echo "==> 3. Create child: ${CHILD_USER}"
curl -sS -X POST "${BASE_URL}/api/auth/children/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS}" \
  -d "$CHILD_BODY"
echo
echo

echo "Done. Parent login: POST ${BASE_URL}/api/auth/login/ with username/password."
echo "Child login: same endpoint with child username (${CHILD_USER}) and password."
