#!/usr/bin/env python3
"""
Test script for CoLink authentication flow

Tests:
1. Keycloak connectivity
2. Token acquisition (password grant)
3. Token verification
4. Protected endpoint access
5. Role-based access control
"""

import asyncio
import httpx
import json
import sys
from typing import Optional


# Configuration
KEYCLOAK_URL = "http://localhost:8080"
REALM = "colink"
CLIENT_ID = "colink-api"
CLIENT_SECRET = "colink-api-secret-dev-only"
GATEWAY_URL = "http://localhost:8000"


class Colors:
    """Terminal colors for output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


async def test_keycloak_connectivity():
    """Test 1: Verify Keycloak is accessible"""
    print_info("Test 1: Checking Keycloak connectivity...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/realms/{REALM}",
                timeout=5.0,
            )
            response.raise_for_status()
            realm_info = response.json()
            print_success(f"Keycloak realm '{REALM}' is accessible")
            print(f"  Realm: {realm_info.get('realm')}")
            print(f"  Issuer: {realm_info.get('issuer')}")
            return True
    except httpx.ConnectError:
        print_error("Cannot connect to Keycloak")
        print_warning("Make sure Keycloak is running: docker-compose up keycloak")
        return False
    except httpx.HTTPStatusError as e:
        print_error(f"Keycloak returned error: {e.response.status_code}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


async def get_token(username: str, password: str) -> Optional[dict]:
    """Test 2: Get access token via password grant"""
    print_info(f"Test 2: Acquiring token for user '{username}'...")

    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"

    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password,
        "scope": "openid profile email",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )
            response.raise_for_status()
            tokens = response.json()
            print_success("Token acquired successfully")
            print(f"  Access Token: {tokens['access_token'][:50]}...")
            print(f"  Token Type: {tokens.get('token_type')}")
            print(f"  Expires In: {tokens.get('expires_in')} seconds")
            print(f"  Refresh Token: {tokens.get('refresh_token')[:50] if tokens.get('refresh_token') else 'None'}...")
            return tokens
    except httpx.HTTPStatusError as e:
        print_error(f"Failed to get token: {e.response.status_code}")
        if e.response.status_code == 401:
            print_warning("Invalid credentials or user doesn't exist")
            print_info("Create a user in Keycloak Admin Console first")
        print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None


async def test_gateway_health():
    """Test 3: Check API Gateway is running"""
    print_info("Test 3: Checking API Gateway connectivity...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GATEWAY_URL}/health", timeout=5.0)
            response.raise_for_status()
            health = response.json()
            print_success("API Gateway is healthy")
            print(f"  Status: {health.get('status')}")
            print(f"  Service: {health.get('service')}")
            return True
    except httpx.ConnectError:
        print_error("Cannot connect to API Gateway")
        print_warning("Make sure Gateway is running on port 8000")
        print_info("Run: cd services/gateway && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


async def test_protected_endpoint(token: str):
    """Test 4: Access protected endpoint with token"""
    print_info("Test 4: Accessing protected endpoint /auth/me...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            response.raise_for_status()
            user_info = response.json()
            print_success("Protected endpoint accessed successfully")
            print(f"  User ID: {user_info.get('user_id')}")
            print(f"  Username: {user_info.get('username')}")
            print(f"  Email: {user_info.get('email')}")
            print(f"  Roles: {user_info.get('roles')}")
            print(f"  Is Admin: {user_info.get('is_admin')}")
            return user_info
    except httpx.HTTPStatusError as e:
        print_error(f"Failed to access protected endpoint: {e.response.status_code}")
        if e.response.status_code == 401:
            print_warning("Token is invalid or expired")
        print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None


async def test_admin_endpoint(token: str):
    """Test 5: Access admin-only endpoint"""
    print_info("Test 5: Accessing admin endpoint /admin/stats...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/admin/stats",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            response.raise_for_status()
            stats = response.json()
            print_success("Admin endpoint accessed successfully")
            print(f"  Message: {stats.get('message')}")
            print(f"  Admin User: {stats.get('admin_user')}")
            return True
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            print_warning("Access denied: User does not have 'admin' role")
            print_info("This is expected if the user is not an admin")
            return False
        print_error(f"Failed to access admin endpoint: {e.response.status_code}")
        print(f"  Response: {e.response.text}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


async def test_invalid_token():
    """Test 6: Verify invalid token is rejected"""
    print_info("Test 6: Testing with invalid token...")

    invalid_token = "invalid.jwt.token"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/auth/me",
                headers={"Authorization": f"Bearer {invalid_token}"},
                timeout=5.0,
            )

            # Should get 401
            if response.status_code == 401:
                print_success("Invalid token correctly rejected (401)")
                return True
            else:
                print_error(f"Expected 401, got {response.status_code}")
                return False

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print_success("Invalid token correctly rejected (401)")
            return True
        print_error(f"Unexpected status code: {e.response.status_code}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


async def main():
    """Run all authentication tests"""
    print("\n" + "=" * 70)
    print("CoLink Authentication Test Suite")
    print("=" * 70 + "\n")

    # Test 1: Keycloak connectivity
    if not await test_keycloak_connectivity():
        print_error("\n❌ Keycloak is not accessible. Aborting tests.")
        sys.exit(1)

    print()

    # Test 3: Gateway health (before authentication tests)
    if not await test_gateway_health():
        print_error("\n❌ API Gateway is not accessible. Aborting tests.")
        sys.exit(1)

    print()

    # Prompt for user credentials
    print_info("Enter test user credentials:")
    print_warning("Note: Create a test user in Keycloak Admin Console first")
    print_info("Keycloak Admin: http://localhost:8080 (admin/admin)")
    print()

    username = input("  Username: ").strip()
    if not username:
        print_error("Username is required")
        sys.exit(1)

    import getpass

    password = getpass.getpass("  Password: ").strip()
    if not password:
        print_error("Password is required")
        sys.exit(1)

    print()

    # Test 2: Get token
    tokens = await get_token(username, password)
    if not tokens:
        print_error("\n❌ Failed to acquire token. Cannot continue.")
        sys.exit(1)

    access_token = tokens["access_token"]
    print()

    # Test 4: Protected endpoint
    user_info = await test_protected_endpoint(access_token)
    if not user_info:
        print_error("\n❌ Failed to access protected endpoint.")
        sys.exit(1)

    print()

    # Test 5: Admin endpoint (may fail if user is not admin)
    await test_admin_endpoint(access_token)

    print()

    # Test 6: Invalid token
    await test_invalid_token()

    print("\n" + "=" * 70)
    print_success("All tests completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        sys.exit(1)
