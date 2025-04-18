from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from src.conf.config import settings


def create_reset_password_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_reset_password_token(token: str) -> str:
    current_time = datetime.now(timezone.utc)
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        if current_time > exp_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Token is expired"
            )
        return payload["sub"]

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token wrong"
        ) from e
