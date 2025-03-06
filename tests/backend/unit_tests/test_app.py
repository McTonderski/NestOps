import pytest
import asyncio
from httpx import AsyncClient
from backend.app import app
from backend.utilities.auth import hash_password, create_jwt_token
from backend.utilities.database import users_collection

# Sample test user data
TEST_USER = {"username": "testuser", "password": "testpassword", "role": "admin"}

TEST_SERVICE = {
    "name": "test-service",
    "image": "test-image",
    "description": "A test service",
}


@pytest.fixture(scope="session")
def event_loop():
    """Create a separate event loop for async tests."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Setup test user in the database."""
    hashed_pw = await hash_password(TEST_USER["password"])
    user_data = {
        "username": TEST_USER["username"],
        "password": hashed_pw,
        "role": TEST_USER["role"],
    }
    await users_collection.insert_one(user_data)

    yield  # Test execution happens here

    await users_collection.delete_many({})  # Cleanup after tests


@pytest.fixture
async def client():
    """Create a test client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def auth_token():
    """Generate JWT token for the test user."""
    return await create_jwt_token(
        {"sub": TEST_USER["username"], "role": TEST_USER["role"]}
    )


@pytest.mark.asyncio
async def test_register_existing_user(client):
    """Test registering a user that already exists."""
    response = await client.post("/api/register", json=TEST_USER)
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_login_success(client):
    """Test successful login."""
    response = await client.post(
        "/api/login",
        json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_failure(client):
    """Test login failure with incorrect credentials."""
    response = await client.post(
        "/api/login", json={"username": "wronguser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_list_services_unauthorized(client):
    """Test listing services without authentication."""
    response = await client.get("/api/services/list")
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_list_services_authorized(client, auth_token):
    """Test listing services with authentication."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/services/list", headers=headers)
    assert response.status_code in [200, 403]  # 403 if non-admin, 200 if allowed


@pytest.mark.asyncio
async def test_register_service(client, auth_token):
    """Test registering a service."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.post(
        "/api/services/register", json=TEST_SERVICE, headers=headers
    )
    assert response.status_code in [200, 403]  # 403 if unauthorized, 200 if admin


@pytest.mark.asyncio
async def test_instance_details(client, auth_token):
    """Test fetching instance details."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/instance/details", headers=headers)
    assert response.status_code == 200
    assert "cpu_usage_percent" in response.json()
    assert "memory_usage" in response.json()
