from typing import TypeVar, Type

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.db = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        smst = select(self.model)
        result = await self.db.execute(smst)
        return list(result.scalars().all())

    async def get_by_id(self, _id: int) -> ModelType | None:
        stmt = select(self.model).filter_by(id=_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        await self.db.delete(instance)
        await self.db.commit()
