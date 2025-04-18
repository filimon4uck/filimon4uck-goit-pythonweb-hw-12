from unittest.mock import AsyncMock
import pytest
from fastapi import status
from conftest import TestingSessionLocal
from src.database.db import get_db


def test_healthchecker_success(client):
    response = client.get("api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI!!!!"}


@pytest.mark.asyncio
def test_healthchecker_db_misconfigured(client):
    async def override_get_db():
        mock_session = AsyncMock()

        mock_result = AsyncMock()
        mock_result.fetchone = AsyncMock(return_value=None)

        mock_session.execute.side_effect = Exception("Db error")

        yield mock_session

    client.app.dependency_overrides[get_db] = override_get_db

    response = client.get("api/v1/health/")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error connecting to the database"}

    client.app.dependency_overrides.pop(get_db, None)
