from sqlalchemy.ext.asyncio import AsyncSession
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.entity.models import User
from src.schemas.user import UserCreate
from src.repositories.user_repository import UserRepository


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.fixture
def test_user():
    return User(id=1, username="testuser", email="test@example.com")


@pytest.mark.asyncio
async def test_get_by_username(user_repository, mock_session, test_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value=test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_by_username("testuser")

    assert result == test_user
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_by_email(user_repository, mock_session, test_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value=test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_by_email("test@example.com")

    assert result == test_user
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session):
    user_data = UserCreate(
        username="newuser",
        email="new@example.com",
        password="secret123"
    )
    hashed_password = "hashed_pwd"
    avatar = "http://example.com/avatar.png"

    mock_user = User(
        username="newuser",
        email="new@example.com",
        hashed_password=hashed_password,
        avatar=avatar
    )

    user_repository.create = AsyncMock(return_value=mock_user)

    result = await user_repository.create_user(user_data, hashed_password, avatar)

    assert result == mock_user
    user_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_confirmed_email(user_repository, mock_session, test_user):
    user_repository.get_by_email = AsyncMock(return_value=test_user)

    await user_repository.confirmed_email(test_user.email)

    assert test_user.confirmed is True
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_change_password(user_repository, mock_session, test_user):
    user_repository.get_by_email = AsyncMock(return_value=test_user)

    await user_repository.change_password(test_user.email, "new_hashed_pwd")

    assert test_user.hashed_password == "new_hashed_pwd"
    assert test_user.reset_password_token is None
    mock_session.commit.assert_called_once()
