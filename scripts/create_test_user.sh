#!/bin/bash
# Create a test user in Keycloak for development/testing

set -e

# Configuration
KEYCLOAK_URL=${KEYCLOAK_URL:-"http://localhost:8080"}
REALM=${KEYCLOAK_REALM:-"colink"}
ADMIN_USER=${KEYCLOAK_ADMIN:-"admin"}
ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:-"admin"}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Keycloak Test User Creator${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo

# Prompt for user details
read -p "Username: " USERNAME
read -p "Email: " EMAIL
read -p "First Name: " FIRST_NAME
read -p "Last Name: " LAST_NAME
read -s -p "Password: " PASSWORD
echo
read -p "Is Admin? (y/n): " IS_ADMIN

echo
echo -e "${BLUE}Creating user...${NC}"

# Get admin access token
echo -e "${BLUE}1. Authenticating as admin...${NC}"
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}✗ Failed to get admin token${NC}"
    echo -e "${YELLOW}  Make sure Keycloak is running and admin credentials are correct${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Admin authenticated${NC}"

# Create user
echo -e "${BLUE}2. Creating user '$USERNAME'...${NC}"

USER_DATA=$(cat <<EOF
{
  "username": "$USERNAME",
  "email": "$EMAIL",
  "firstName": "$FIRST_NAME",
  "lastName": "$LAST_NAME",
  "enabled": true,
  "emailVerified": true,
  "credentials": [
    {
      "type": "password",
      "value": "$PASSWORD",
      "temporary": false
    }
  ]
}
EOF
)

CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$USER_DATA")

HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "201" ]; then
    echo -e "${GREEN}✓ User created successfully${NC}"
else
    echo -e "${RED}✗ Failed to create user (HTTP $HTTP_CODE)${NC}"
    echo "$CREATE_RESPONSE" | head -n -1
    exit 1
fi

# Get user ID
echo -e "${BLUE}3. Getting user ID...${NC}"
USER_ID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM/users?username=$USERNAME&exact=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq -r '.[0].id')

if [ "$USER_ID" == "null" ] || [ -z "$USER_ID" ]; then
    echo -e "${RED}✗ Failed to get user ID${NC}"
    exit 1
fi

echo -e "${GREEN}✓ User ID: $USER_ID${NC}"

# Assign 'user' role
echo -e "${BLUE}4. Assigning 'user' role...${NC}"
USER_ROLE_ID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM/roles/user" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq -r '.id')

ROLE_DATA="[{\"id\":\"$USER_ROLE_ID\",\"name\":\"user\"}]"

curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users/$USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$ROLE_DATA" > /dev/null

echo -e "${GREEN}✓ 'user' role assigned${NC}"

# Assign 'admin' role if requested
if [ "$IS_ADMIN" == "y" ] || [ "$IS_ADMIN" == "Y" ]; then
    echo -e "${BLUE}5. Assigning 'admin' role...${NC}"
    ADMIN_ROLE_ID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM/roles/admin" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      | jq -r '.id')

    ADMIN_ROLE_DATA="[{\"id\":\"$ADMIN_ROLE_ID\",\"name\":\"admin\"}]"

    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users/$USER_ID/role-mappings/realm" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$ADMIN_ROLE_DATA" > /dev/null

    echo -e "${GREEN}✓ 'admin' role assigned${NC}"
fi

echo
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ User created successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo
echo -e "  Username: ${BLUE}$USERNAME${NC}"
echo -e "  Email: ${BLUE}$EMAIL${NC}"
echo -e "  User ID: ${BLUE}$USER_ID${NC}"
echo -e "  Roles: ${BLUE}user$([ "$IS_ADMIN" == "y" ] || [ "$IS_ADMIN" == "Y" ] && echo ", admin")${NC}"
echo
echo -e "${YELLOW}Note: 2FA (TOTP) is required by default.${NC}"
echo -e "${YELLOW}User will be prompted to set up 2FA on first login.${NC}"
echo
echo "Test the user with:"
echo "  python3 scripts/test_auth.py"
echo
