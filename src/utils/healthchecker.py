from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db

router = APIRouter(prefix="/health", tags=["HealthCheck"])


@router.get("/")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Perform a health check for the API.

    - Verifies if the API is up and running.
    - Tests the database connection with a `SELECT 1` query.
    - Returns a success message or an error if the database connection fails.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to FastAPI!!!!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        ) from e
