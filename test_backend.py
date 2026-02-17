#!/usr/bin/env python3
"""
Backend API Tests - Comprehensive testing of authentication and rate limiting.
Run this while the FastAPI server is running on port 5001.
"""

import requests
import json
import random
import string
from typing import Dict, Any

# Configuration
BASE_URL = "http://127.0.0.1:5001"


def generate_test_email():
    """Generate a unique test email."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"


# Test credentials (will be set during test)
TEST_EMAIL = None
TEST_PASSWORD = "testpass123"
TEST_NAME = "Test User"

# Session for maintaining cookies
session = requests.Session()


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


def test_get_user_not_authenticated():
    """Test GET /api/user when not authenticated."""
    print_section("Test 1: GET /api/user (Not Authenticated)")
    response = session.get(f"{BASE_URL}/api/user")
    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    success = (
        response.status_code == 200 and
        data is not None and
        data.get("authenticated") == False and
        data.get("user") is None
    )

    print_result(
        "Unauthenticated user returns user=None",
        success,
        f"Status: {response.status_code}, Authenticated: {data.get('authenticated') if data else 'N/A'}"
    )
    return success


def test_register_new_user():
    """Test POST /api/register with new user."""
    print_section("Test 2: POST /api/register (New User)")

    global TEST_EMAIL
    TEST_EMAIL = generate_test_email()

    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": TEST_NAME
    }

    response = session.post(
        f"{BASE_URL}/api/register",
        json=payload
    )

    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if response.status_code == 200 and data:
        user_data = data.get("user")
        success = (
            data.get("success") == True and
            user_data is not None and
            isinstance(user_data, dict) and
            user_data.get("email") == TEST_EMAIL.lower()
        )

        print_result(
            "User registration successful",
            success,
            f"User ID: {user_data.get('id', 'N/A') if user_data else 'N/A'}, Email: {TEST_EMAIL}"
        )
        return success
    else:
        print_result(
            "User registration successful",
            False,
            f"Status: {response.status_code}, Response: {data or response.text[:200]}"
        )
        return False


def test_register_duplicate_user():
    """Test POST /api/register with duplicate email."""
    print_section("Test 3: POST /api/register (Duplicate Email)")

    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": "Another Name"
    }

    response = session.post(
        f"{BASE_URL}/api/register",
        json=payload
    )

    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        success = (
            data.get("success") == False and
            "already exists" in data.get("error", "").lower()
        )

        print_result(
            "Duplicate registration properly rejected",
            success,
            f"Error message: {data.get('error')}"
        )
        return success

    print_result("Duplicate registration properly rejected", False, f"Status: {response.status_code}")
    return False


def test_get_user_authenticated():
    """Test GET /api/user when authenticated."""
    print_section("Test 4: GET /api/user (Authenticated)")

    response = session.get(f"{BASE_URL}/api/user")
    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        success = (
            response.status_code == 200 and
            data.get("authenticated") == True and
            data.get("user") is not None
        )

        print_result(
            "Authenticated user returns user data",
            success,
            f"Email: {data.get('user', {}).get('email') if isinstance(data.get('user'), dict) else 'N/A'}"
        )
        return success

    print_result("Authenticated user returns user data", False, f"Status: {response.status_code}")
    return False


def test_login_valid_credentials():
    """Test POST /api/login with valid credentials."""
    print_section("Test 5: POST /api/login (Valid Credentials)")

    # Create new session to test login separately
    login_session = requests.Session()

    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }

    response = login_session.post(
        f"{BASE_URL}/api/login",
        json=payload
    )

    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        user_data = data.get("user")
        success = (
            data.get("success") == True and
            user_data is not None
        )

        print_result(
            "Login with valid credentials successful",
            success,
            f"User: {user_data.get('email') if user_data else 'N/A'}"
        )
        return success

    print_result("Login with valid credentials successful", False, f"Status: {response.status_code}")
    return False


def test_login_invalid_credentials():
    """Test POST /api/login with invalid credentials."""
    print_section("Test 6: POST /api/login (Invalid Credentials)")

    login_session = requests.Session()

    payload = {
        "email": TEST_EMAIL,
        "password": "wrongpassword"
    }

    response = login_session.post(
        f"{BASE_URL}/api/login",
        json=payload
    )

    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        success = (
            data.get("success") == False and
            data.get("error") is not None
        )

        print_result(
            "Login with invalid credentials rejected",
            success,
            f"Error: {data.get('error')}"
        )
        return success

    print_result("Login with invalid credentials rejected", False, f"Status: {response.status_code}")
    return False


def test_query_anonymous_limit():
    """Test POST /api/query anonymous user limit (5 free queries)."""
    print_section("Test 7: POST /api/query (Anonymous User Limit)")

    anon_session = requests.Session()

    # Make 5 queries (should succeed)
    for i in range(1, 6):
        payload = {
            "query": f"Test query {i}",
            "user_id": f"anon_test_{i}",
            "new_session": True
        }

        response = anon_session.post(
            f"{BASE_URL}/api/query",
            json=payload
        )

        remaining = response.headers.get("X-Anonymous-Remaining", "?")

        if response.status_code == 200:
            print_result(
                f"Anonymous query {i}/5 succeeds",
                True,
                f"Remaining: {remaining}"
            )
        else:
            print_result(
                f"Anonymous query {i}/5 succeeds",
                False,
                f"Status: {response.status_code}"
            )
            return False

    # 6th query should fail with 401
    payload = {
        "query": "Test query 6 (should fail)",
        "user_id": "anon_test_6",
        "new_session": True
    }

    response = anon_session.post(
        f"{BASE_URL}/api/query",
        json=payload
    )

    success = response.status_code == 401

    print_result(
        "6th anonymous query rejected with 401",
        success,
        f"Status: {response.status_code}, Expected: 401"
    )

    return success


def test_query_authenticated_user():
    """Test POST /api/query with authenticated user."""
    print_section("Test 8: POST /api/query (Authenticated User)")

    payload = {
        "query": "What is the capital of France?",
        "user_id": "authenticated_test",
        "new_session": True
    }

    response = session.post(
        f"{BASE_URL}/api/query",
        json=payload
    )

    # Check headers
    is_authenticated = response.headers.get("X-Authenticated", "false").lower() == "true"
    anon_remaining = response.headers.get("X-Anonymous-Remaining", "unlimited")
    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if response.status_code == 200 and data:
        success = (
            data.get("success") == True and
            is_authenticated and
            anon_remaining == "unlimited"
        )

        print_result(
            "Authenticated query succeeds with unlimited access",
            success,
            f"X-Authenticated: {is_authenticated}, X-Anonymous-Remaining: {anon_remaining}"
        )
        return success

    print_result(
        "Authenticated query succeeds",
        False,
        f"Status: {response.status_code}"
    )
    return False


def test_logout():
    """Test POST /api/logout."""
    print_section("Test 9: POST /api/logout")

    response = session.post(f"{BASE_URL}/api/logout")
    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        success = data.get("success") == True

        print_result(
            "Logout successful",
            success,
            f"Message: {data.get('message', 'N/A')}"
        )

        # Verify user is logged out
        check_response = session.get(f"{BASE_URL}/api/user")
        check_data = check_response.json() if check_response.headers.get("content-type", "").startswith("application/json") else None

        verified = check_data is not None and not check_data.get("authenticated", False)

        print_result(
            "User session cleared after logout",
            verified,
            f"Authenticated: {check_data.get('authenticated') if check_data else 'N/A'}"
        )

        return success and verified

    print_result("Logout successful", False, f"Status: {response.status_code}")
    return False


def test_samples_endpoint():
    """Test GET /api/samples."""
    print_section("Test 10: GET /api/samples")

    response = session.get(f"{BASE_URL}/api/samples")
    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        success = (
            data.get("success") == True and
            isinstance(data.get("samples"), list) and
            len(data.get("samples", [])) > 0
        )

        print_result(
            "Samples endpoint returns data",
            success,
            f"Sample count: {len(data.get('samples', []))}"
        )
        return success

    print_result("Samples endpoint returns data", False, f"Status: {response.status_code}")
    return False


def test_health_endpoint():
    """Test GET /health."""
    print_section("Test 11: GET /health")

    response = session.get(f"{BASE_URL}/health")
    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        success = (
            data.get("status") == "healthy" and
            data.get("initialized") == True
        )

        print_result(
            "Health check passes",
            success,
            f"Status: {data.get('status')}, Initialized: {data.get('initialized')}"
        )
        return success

    print_result("Health check passes", False, f"Status: {response.status_code}")
    return False


def test_rate_limit_status():
    """Test GET /api/rate-limit-status."""
    print_section("Test 12: GET /api/rate-limit-status")

    response = session.get(f"{BASE_URL}/api/rate-limit-status")
    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None

    if data:
        has_required_keys = all(k in data for k in ["count", "limit", "remaining", "reset_date"])

        print_result(
            "Rate limit status returns data",
            has_required_keys,
            f"Count: {data.get('count')}/{data.get('limit')}, Remaining: {data.get('remaining')}"
        )
        return has_required_keys

    print_result("Rate limit status returns data", False, f"Status: {response.status_code}")
    return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  AI TRIP PLANNER - BACKEND API TESTS")
    print("=" * 60)
    print(f"  Testing: {BASE_URL}")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("GET /api/user (not authenticated)", test_get_user_not_authenticated()))
    results.append(("POST /api/register (new user)", test_register_new_user()))
    results.append(("POST /api/register (duplicate)", test_register_duplicate_user()))
    results.append(("GET /api/user (authenticated)", test_get_user_authenticated()))
    results.append(("POST /api/login (valid)", test_login_valid_credentials()))
    results.append(("POST /api/login (invalid)", test_login_invalid_credentials()))
    results.append(("POST /api/query (anonymous limit)", test_query_anonymous_limit()))
    results.append(("POST /api/query (authenticated)", test_query_authenticated_user()))
    results.append(("POST /api/logout", test_logout()))
    results.append(("GET /api/samples", test_samples_endpoint()))
    results.append(("GET /health", test_health_endpoint()))
    results.append(("GET /api/rate-limit-status", test_rate_limit_status()))

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

    print("\n" + "-" * 60)
    print(f"Total: {passed}/{total} tests passed ({percentage:.0f}%)")
    print("-" * 60)

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
