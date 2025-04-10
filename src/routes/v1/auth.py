import logging

from fastapi import APIRouter, Depends, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from src.utils.get_services import get_auth_service
from src.services.auth import AuthService, oauth2_scheme
from src.schemas.token import TokenResponse, RefreshTokenRequest
from src.schemas.user import UserResponse, UserCreate
from src.services.email import send_email


router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("uvicorn.error")


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):

    user = await auth_service.register_user(user_data)
    background_tasks.add_task(send_email, user.email, user.username, request.base_url)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    user = await auth_service.authenticate(form_data.username, form_data.password)
    access_token = await auth_service.create_acces_token(form_data.username)
    refresh_token = await auth_service.create_refresh_token(
        user_id=user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    return TokenResponse(
        access_token=access_token, token_type="bearer", refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    user = await auth_service.validate_refresh_token(refresh_token.refresh_token)
    access_token = await auth_service.create_acces_token(user.username)
    refresh_token = await auth_service.create_refresh_token(
        user_id=user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    await auth_service.revoke_refresh_token(refresh_token)
    return TokenResponse(
        access_token=access_token, token_type="bearer", refresh_token=refresh_token
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: RefreshTokenRequest,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.revoke_access_token(token)
    await auth_service.revoke_refresh_token(refresh_token.refresh_token)
    return None
