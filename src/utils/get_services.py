from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService
from src.services.contacts import ContactsService
from src.entity.models import User, UserRole


def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)):
    return UserService(db)


async def get_current_user(
    auth_service: AuthService = Depends(get_auth_service),
    token: str = Depends(oauth2_scheme),
):
    user = await auth_service.get_current_user(token)
    return user


def get_contacts_service(db: AsyncSession = Depends(get_db)):
    return ContactsService(db)


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission",
        )
