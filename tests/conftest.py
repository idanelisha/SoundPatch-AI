import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def load_env():
    """Load environment variables from .env file."""
    load_dotenv()

@pytest.fixture
def base_url():
    """Base URL for API requests."""
    return "http://localhost:8000/api/v1"

@pytest.fixture
def test_user():
    """Test user credentials."""
    return {
        "email": f"test_{os.getpid()}@example.com",  # Unique email using process ID
        "password": "password123",
        "full_name": "Test User"
    } 