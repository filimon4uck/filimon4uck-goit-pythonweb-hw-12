from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    status,
    BackgroundTasks,
    UploadFile,
    File,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.schemas.user import UserResponse
from src.entity.models import User
from src.utils.get_services import get_auth_service, get_user_service, get_current_user
from src.utils.email_token import get_email_from_token
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService
from src.schemas.email import RequestEmail
from src.services.email import send_email
from src.conf.config import settings
from src.services.upload_file import UploadFileService


router = APIRouter(prefix="/users", tags=["users"])
Limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=UserResponse)
@Limiter.limit(
    "10/hour",
)
async def me(
    request: Request,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(token)


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str, user_service: UserService = Depends(get_user_service)
):
    email = get_email_from_token(token)
    user = await user_service.get_by_email(email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Veryfication error"
        )
    if user.confirmed:
        return {"message": "Your email has already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Your email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.get_by_email(body.email)

    if user.confirmed:
        return {"message": "Your email has already confirmed"}

    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email address"}


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)
    user = await user_service.update_avatar_url(user.email, avatar_url)
    return user
