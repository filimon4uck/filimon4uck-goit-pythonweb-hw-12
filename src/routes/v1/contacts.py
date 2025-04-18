import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.schemas.contact import BaseContact, UpdateContact,ContactResponse
from src.utils.get_services import get_contacts_service, get_current_user
from src.services.contacts import ContactsService
from src.entity.models import User

router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger("uvicorn.error")


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    contacts_service: ContactsService = Depends(get_contacts_service),
    user: User = Depends(get_current_user),
):

    return await contacts_service.get_contacts(limit, offset, user)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    contacts_service: ContactsService = Depends(get_contacts_service),
    user: User = Depends(get_current_user),
):
    contact = await contacts_service.ge_contact_by_id(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: BaseContact,
    contacts_service: ContactsService = Depends(get_contacts_service),
    user: User = Depends(get_current_user),
):
    return await contacts_service.create_contact(body, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: UpdateContact,
    contacts_service: ContactsService = Depends(get_contacts_service),
    user: User = Depends(get_current_user),
):
    contact = await contacts_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    contacts_service: ContactsService = Depends(get_contacts_service),
    user: User = Depends(get_current_user),
):
    await contacts_service.remove_contact(contact_id, user)
    return None


@router.get("/search/", response_model=list[ContactResponse])
async def search_contacts(
    query: str,
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    contacts_service: ContactsService = Depends(get_contacts_service),
    user: User = Depends(get_current_user),
):
    return await contacts_service.search_contacts(query, limit, offset, user)


@router.get("/birthdays/", response_model=list[ContactResponse])
async def get_upcoming_birthdays(
    days: int = Query(7, ge=1, le=30),
    contacts_service: ContactsService = Depends(get_contacts_service),
    user: User = Depends(get_current_user),
):
    return await contacts_service.get_upcoming_birthdays(days, user)
