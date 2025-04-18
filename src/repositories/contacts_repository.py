import logging

from datetime import date, timedelta

from typing import Sequence, Optional

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact
from src.schemas.contact import BaseContact, UpdateContact
from src.entity.models import User

logger = logging.getLogger("uvicorn.error")


class ContactsRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(
        self, limit: int, offset: int, user: User
    ) -> Sequence[Contact]:
        stmt = select(Contact).filter_by(user_id=user.id).offset(offset).limit(limit)
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        stmt = select(Contact).filter_by(user_id=user.id, id=contact_id)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: BaseContact, user: User) -> Contact:
        contact = Contact(**body.model_dump(), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, contact_id: int, body: UpdateContact, user: User
    ) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            update_data = body.model_dump(exclude_unset=True)
            for key, val in update_data.items():
                setattr(contact, key, val)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def search_contacts(
        self, query: str, limit: int = 10, offset: int = 0, user: User = None
    ) -> Sequence[Contact]:
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .where(
                or_(
                    Contact.first_name.ilike(f"%{query}%"),
                    Contact.last_name.ilike(f"%{query}%"),
                    Contact.email.ilike(f"%{query}%"),
                )
            )
            .offset(offset)
            .limit(limit)
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_upcoming_birthdays(
        self, days: int = 7, user: User = None
    ) -> Sequence[Contact]:
        today = date.today()
        end_date = today + timedelta(days=days)
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .where(and_(Contact.birthday >= today, Contact.birthday <= end_date))
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()
