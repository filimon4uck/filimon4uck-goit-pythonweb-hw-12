import logging

from fastapi import APIRouter, Depends, Request, status, BackgroundTasks, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from src.utils.get_services import get_auth_service
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService
from src.utils.get_services import get_user_service
from src.schemas.token import TokenResponse, RefreshTokenRequest
from src.schemas.password import ResetPasswordRequest
from src.schemas.email import RequestEmail
from src.utils.reset_password_token import create_reset_password_token
from src.schemas.user import UserResponse, UserCreate
from src.services.email import send_email, send_reset_password_email


router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("uvicorn.error")


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user.

    Args:
        user_data: UserCreate object containing user registration details.
        request: FastAPI Request object to access request metadata.
        background_tasks: BackgroundTasks instance to handle sending email in background.
        auth_service: Dependency-injected AuthService instance.

    Returns:
        UserResponse: Registered user data.
    """
    user = await auth_service.register_user(user_data)
    background_tasks.add_task(
        send_email, user.email, user.username, str(request.base_url)
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Authenticate user and return access and refresh tokens.

    Args:
        form_data: OAuth2PasswordRequestForm containing username and password.
        request: FastAPI Request object for getting client IP and user-agent.
        auth_service: Dependency-injected AuthService instance.

    Returns:
        TokenResponse: Contains access token, refresh token and token type.
    """
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
    """
    Refresh authentication tokens.

    Args:
        refresh_token: RefreshTokenRequest containing the refresh token.
        request: FastAPI Request object for getting IP and user-agent info.
        auth_service: Dependency-injected AuthService instance.

    Returns:
        TokenResponse: New access and refresh tokens.
    """
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


@router.post("/request_reset_password")
async def request_reset_password(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """
    Request password reset email.

    Args:
        body: RequestEmail containing the email address of the user.
        background_tasks: BackgroundTasks instance to handle sending email asynchronously.
        request: FastAPI Request object for building the reset URL.
        user_service: Dependency-injected UserService instance.

    Returns:
        dict: Message indicating whether the reset email was sent.
    """
    user = await user_service.get_by_email(body.email)

    if not user:
        return {"message": "Incorrect email"}

    if user:
        token = create_reset_password_token({"sub": body.email})
        background_tasks.add_task(
            send_reset_password_email,
            user.email,
            user.username,
            str(request.base_url),
            token,
        )
        await user_service.add_reset_password_token(body.email, token)
    return {"message": "Check your email address"}


@router.post("/reset_password/", response_model=dict)
async def reset_password(
    token: str,
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Reset user password using the reset token.

    Args:
        token: Reset password token provided in email.
        body: ResetPasswordRequest containing the new password.
        auth_service: Dependency-injected AuthService instance.

    Returns:
        dict: Confirmation message after password is successfully changed.
    """

    user = await auth_service.validate_reset_password_token(token)

    await auth_service.change_password(user.email, body.new_password)
    return {"Message": "Password was changes"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: RefreshTokenRequest,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout user by revoking access and refresh tokens.

    Args:
        refresh_token: RefreshTokenRequest containing the refresh token.
        token: Bearer access token from request headers.
        auth_service: Dependency-injected AuthService instance.

    Returns:
        None
    """
    await auth_service.revoke_access_token(token)
    await auth_service.revoke_refresh_token(refresh_token.refresh_token)
    return None
