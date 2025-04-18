import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import select

from src.entity.models import User
from tests.conftest import TestingSessionLocal

# Тестові дані для нового користувача
new_user_data = {
    "username": "test_user",
    "email": "test_user@example.com",
    "password": "securepassword",
    "role": "USER",
}

# Дані для перевірки конфліктів
duplicate_username_data = {
    "username": "test_user",
    "email": "different_email@example.com",
    "password": "securepassword",
}

duplicate_email_data = {
    "username": "different_user",
    "email": "test_user@example.com",
    "password": "securepassword",
}


@pytest.mark.asyncio
async def test_register_success(client, monkeypatch):
    """Успішна реєстрація"""
    mock_send_email = AsyncMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    response = client.post("/api/v1/auth/register", json=new_user_data)
    await mock_send_email("test@example.com", "testuser", "http://testserver/")

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == new_user_data["username"]
    assert data["email"] == new_user_data["email"]
    assert "hash_password" not in data
    assert "id" in data

    mock_send_email.assert_called_once_with(
        "test@example.com", "testuser", "http://testserver/"
    )
    mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_register_duplicate_username(client, monkeypatch):
    """Реєстрація з уже існуючим ім’ям користувача"""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    response = client.post("/api/v1/auth/register", json=duplicate_username_data)

    assert response.status_code == 409, response.text
    assert "User aleready exists" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_register_duplicate_email(client, monkeypatch):
    """Реєстрація з уже існуючою електронною поштою"""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    response = client.post("/api/v1/auth/register", json=duplicate_email_data)

    assert response.status_code == 409, response.text
    assert "Email aleready exists" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_with_unconfirmed_email(client):
    """Спроба входу без підтвердженої пошти"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": new_user_data["username"],
            "password": new_user_data["password"],
        },
    )
    assert response.status_code == 401, response.text
    assert "Email is not confirmed" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_confirm_user_email():
    """Підтвердження електронної пошти користувача"""
    async with TestingSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == new_user_data["email"])
        )
        user = result.scalar_one_or_none()
        assert user is not None
        user.confirmed = True
        await session.commit()


@pytest.mark.asyncio
async def test_login_success(client):
    """Успішний вхід"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": new_user_data["username"],
            "password": new_user_data["password"],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Неправильний пароль"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": new_user_data["username"], "password": "wrong_password"},
    )
    assert response.status_code == 401, response.text
    assert "Incorrect username or password" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_wrong_username(client):
    """Невірне ім’я користувача"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent_user", "password": new_user_data["password"]},
    )
    assert response.status_code == 401, response.text
    assert "Incorrect username or password" in response.json().get("detail", "")


def test_refresh_token(client):
    response = client.post("api/v1/auth/login",
                           data={"username": new_user_data.get("username"), "password": new_user_data.get("password")})
    refresh_token = response.json().get("refresh_token")

    response = client.post("api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] != refresh_token


def test_logout(client):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.post("api/v1/auth/login",
                               data={"username": new_user_data.get("username"), "password": new_user_data.get("password")})
        assert response.status_code == 200, response.text
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        response = client.post("api/v1/auth/logout", json={"refresh_token": refresh_token},
                               headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 204, response.text