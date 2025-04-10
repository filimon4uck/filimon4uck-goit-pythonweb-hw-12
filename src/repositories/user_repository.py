import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas.user import UserCreate
from src.repositories.base import BaseRepository

logger = logging.getLogger("uvicorn.error")


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(self.model).where(self.model.username == username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(self.model).where(self.model.email == email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self, user_data: UserCreate, hashed_password: str, avatar: str
    ) -> User | None:
        user = User(
            **user_data.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=hashed_password,
            avatar=avatar
        )
        return await self.create(user)

    async def confirmed_email(self, email: str) -> None:
        user = await self.get_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        user = await self.get_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user
