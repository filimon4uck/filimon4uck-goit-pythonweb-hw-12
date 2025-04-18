import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone

from src.entity.models import RefreshToken
from src.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.mark.asyncio
async def test_get_by_token_hash_found():
    mock_session = AsyncMock()
    repo = RefreshTokenRepository(mock_session)

    fake_token = RefreshToken(token_hash="abc123")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = fake_token
    mock_session.execute.return_value = mock_result

    result = await repo.get_by_token_hash("abc123")

    assert result == fake_token
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_token_hash_not_found():
    mock_session = AsyncMock()
    repo = RefreshTokenRepository(mock_session)

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repo.get_by_token_hash("notfound")

    assert result is None
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_active_token_success():
    mock_session = AsyncMock()
    repo = RefreshTokenRepository(mock_session)

    current_time = datetime.now(timezone.utc)
    active_token = RefreshToken(
        token_hash="abc123",
        expired_at=current_time + timedelta(hours=1),
        revoked_at=None,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = active_token
    mock_session.execute.return_value = mock_result

    result = await repo.get_active_token("abc123", current_time)

    assert result == active_token
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_active_token_expired():
    mock_session = AsyncMock()
    repo = RefreshTokenRepository(mock_session)

    current_time = datetime.now(timezone.utc)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repo.get_active_token("abc123", current_time)

    assert result is None
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_token():
    mock_session = AsyncMock()
    repo = RefreshTokenRepository(mock_session)

    current_time = datetime.now(timezone.utc)
    expected_token = RefreshToken(
        user_id=1,
        token_hash="hash",
        expired_at=current_time,
        ip_address="127.0.0.1",
        user_agent="TestAgent",
    )

    repo.create = AsyncMock(return_value=expected_token)

    result = await repo.create_token(
        user_id=1,
        token_hash="hash",
        expired_at=current_time,
        ip_address="127.0.0.1",
        user_agent="TestAgent",
    )

    assert result == expected_token
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_token():
    mock_session = AsyncMock()
    repo = RefreshTokenRepository(mock_session)

    token = RefreshToken(token_hash="revokable")
    await repo.revoke_token(token)

    assert token.revoked_at is not None
    mock_session.commit.assert_awaited_once()
