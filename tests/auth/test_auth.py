import pytest
import requests
import json
from datetime import datetime
import firebase_admin
from firebase_admin import auth

def test_register_and_login(base_url, test_user):
    """Test the complete authentication flow: register, login, and get user info."""
    
    # 1. Register new user
    print("\n1. Registering new user...")
    register_response = requests.post(
        f"{base_url}/auth/register",
        json=test_user
    )
    
    assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
    register_data = register_response.json()
    print("Registration successful:", json.dumps(register_data, indent=2))
    
    # Get the custom token from registration
    custom_token = register_data["access_token"]
    assert custom_token is not None, "No access token received from registration"
    
    # 2. Create a new custom token for login
    try:
        # Create a new custom token for the user and decode it from bytes to string
        id_token = auth.create_custom_token(test_user["email"]).decode('utf-8')
        print("Created new ID token for login")
    except Exception as e:
        print(f"Error creating ID token: {str(e)}")
        raise
    
    # 3. Login with the ID token
    print("\n3. Logging in with ID token...")
    login_response = requests.post(
        f"{base_url}/auth/login",
        json={
            "id_token": id_token
        }
    )
    
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    login_data = login_response.json()
    print("Login successful:", json.dumps(login_data, indent=2))
    
    # Get the access token
    access_token = login_data["access_token"]
    assert access_token is not None, "No access token received from login"
    
    # 4. Get user info
    print("\n4. Getting user info...")
    user_info_response = requests.get(
        f"{base_url}/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    assert user_info_response.status_code == 200, f"Failed to get user info: {user_info_response.text}"
    user_info = user_info_response.json()
    print("User info:", json.dumps(user_info, indent=2))
    
    # Verify user info
    assert user_info["email"] == test_user["email"], "User email mismatch"
    assert user_info["full_name"] == test_user["full_name"], "User name mismatch"
    assert user_info["is_active"] is True, "User is not active"
    assert "id" in user_info, "User ID is missing"
    assert "created_at" in user_info, "Created at timestamp is missing"
    
    print("\nTest completed successfully!")

def test_invalid_login(base_url):
    """Test login with invalid token."""
    response = requests.post(
        f"{base_url}/auth/login",
        json={
            "id_token": "invalid_token"
        }
    )
    
    assert response.status_code == 401, "Expected 401 for invalid token"
    assert response.json()["detail"] == "Invalid credentials", "Expected invalid credentials message"

def test_unauthorized_access(base_url):
    """Test accessing protected endpoint without token."""
    response = requests.get(
        f"{base_url}/auth/me"
    )
    
    assert response.status_code == 401, "Expected 401 for unauthorized access" 