from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.contacts_repository import ContactsRepository

from src.schemas.contact import BaseContact, UpdateContact
from src.entity.models import User


class ContactsService:
    def __init__(self, db: AsyncSession):
        self.contacts_repository = ContactsRepository(db)

    async def create_contact(self, body: BaseContact, user: User):
        return await self.contacts_repository.create_contact(body, user)

    async def get_contacts(self, limit: int, offset: int, user: User):
        return await self.contacts_repository.get_contacts(limit, offset, user)

    async def ge_contact_by_id(self, contact_id: int, user: User):
        return await self.contacts_repository.get_contact_by_id(contact_id, user)

    async def update_contact(self, contact_id: int, body: UpdateContact, user: User):
        return await self.contacts_repository.update_contact(contact_id, body, user)

    async def remove_contact(self, contact_id: int, user: User):
        return await self.contacts_repository.remove_contact(contact_id, user)

    async def search_contacts(self, query: str, limit: int, offset: int, user: User):
        return await self.contacts_repository.search_contacts(
            query=query, limit=limit, offset=offset, user=user
        )

    async def get_upcoming_birthdays(self, days: int, user: User):
        return await self.contacts_repository.get_upcoming_birthdays(days, user)
