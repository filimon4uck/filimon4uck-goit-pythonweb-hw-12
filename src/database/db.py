import contextlib
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


class DatabaseSessionManager:
    def __init__(self, url: str):
        self.engine: AsyncEngine | None = create_async_engine(url=url)
        self.session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self.engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        if self.session_maker is None:
            raise Exception("Database session in not initialized")
        session = self.session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database error {e}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    async with sessionmanager.session() as session:
        yield session
