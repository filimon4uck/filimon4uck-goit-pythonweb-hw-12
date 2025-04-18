from datetime import date
from typing import Optional


from pydantic import BaseModel, ConfigDict


class BaseContact(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    birthday: date
    optional_data: Optional[str] = None


class CreateContact(BaseContact):
    pass


class UpdateContact(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birthday: Optional[str] = None
    optional_data: Optional[str] = None


class ContactResponse(BaseContact):
    id: int
    model_config = ConfigDict(from_attributes=True)
