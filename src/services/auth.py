from datetime import datetime, timedelta, UTC, timezone
import json
import secrets


import redis.asyncio as redis
import bcrypt
import hashlib
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.entity.models import User
from src.schemas.user import UserCreate
from src.conf.config import settings
from src.repositories.user_repository import UserRepository
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.utils.reset_password_token import get_email_from_reset_password_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
redis_client = redis.from_url(settings.REDIS_URL)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.refresh_token_repository = RefreshTokenRepository(self.db)

    def _hash_password(self, password: str) -> str:
        """
        Hashes a plain-text password using bcrypt.

        Args:
            password: The plain-text password to hash.

        Returns:
            A hashed version of the password.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        return hashed_password.decode()

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verifies a plain-text password against a hashed password.

        Args:
            password: The plain-text password to verify.
            hashed_password: The hashed password to compare against.

        Returns:
            True if the password matches the hash, False otherwise.
        """
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def hash_token(self, token: str):
        """
        Hashes a token using SHA3-256 algorithm.

        Args:
            token: The token to hash.

        Returns:
            The hashed token as a hex string.
        """
        return hashlib.sha3_256(token.encode()).hexdigest()

    async def authenticate(self, username: str, password: str) -> User:
        """
        Authenticates a user with a username and password.

        Args:
            username: The user's username.
            password: The user's plain-text password.

        Returns:
            The authenticated User object.

        Raises:
            HTTPException: If authentication fails.
        """
        user = await self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        if not user.confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email is not confirmed",
            )

        if not self._verify_password(password, user.hashed_password):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        return user

    async def register_user(self, user_data: UserCreate) -> User:
        """
        Registers a new user in the system.

        Args:
            user_data: Data required to create a new user (username, email, password).

        Returns:
            The newly created User object.

        Raises:
            HTTPException: If username or email is already taken.
        """
        if await self.user_repository.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User aleready exists"
            )
        if await self.user_repository.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email aleready exists"
            )
        avatar = None
        try:
            g = Gravatar(user_data.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)
        hashed_password = self._hash_password(user_data.password)
        user = await self.user_repository.create_user(
            user_data=user_data, hashed_password=hashed_password, avatar=avatar
        )

        return user

    async def create_acces_token(
        self,
        username: str,
    ) -> str:
        """
        Creates an access token for a user.

        Args:
            username: The username of the user.

        Returns:
            A JWT access token as a string.
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {"sub": username, "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt

    async def create_refresh_token(
        self, user_id: int, ip_address: str | None, user_agent: str | None
    ) -> str:
        """
        Creates and stores a refresh token for a user.

        Args:
            user_id: The ID of the user.
            ip_address: The user's IP address.
            user_agent: The user agent of the client's request.

        Returns:
            A plain refresh token string.
        """
        token = secrets.token_urlsafe(32)

        token_hash = self.hash_token(token)

        expired_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.refresh_token_repository.create_token(
            user_id, token_hash, expired_at, ip_address, user_agent
        )
        return token

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """
        Retrieves the current authenticated user based on access token.

        Args:
            token: JWT access token (automatically provided by FastAPI dependency).

        Returns:
            The corresponding User object.

        Raises:
            HTTPException: If the token is invalid, revoked, or user not found.
        """
        if await redis_client.exists(f"bl:{token}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked"
            )

        cache_key = f"user:{token}"
        cached_user = await redis_client.get(cache_key)
        if cached_user:
            try:
                user_dict = json.loads(cached_user)
                return User(**user_dict)
            except (json.JSONDecodeError, TypeError):
                pass
        payload = self.decode_and_validate_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        user = await self.user_repository.get_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar,
            "confirmed": user.confirmed,
            "role": user.role,
        }
        await redis_client.set(cache_key, json.dumps(user_dict), ex=3600)

        return user


    def decode_and_validate_access_token(self, token: str) -> dict:
        """
        Decodes and validates a JWT access token.

        Args:
            token: The JWT access token.

        Returns:
            The decoded payload.

        Raises:
            HTTPException: If the token is invalid.
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token wrong"
            )

    async def validate_refresh_token(self, token: str) -> User:
        """
        Validates a refresh token and retrieves the associated user.

        Args:
            token: The plain-text refresh token.

        Returns:
            The associated User object.

        Raises:
            HTTPException: If token is invalid or user not found.
        """
        token_hash = self.hash_token(token)
        current_time = datetime.now(timezone.utc)
        refresh_token = await self.refresh_token_repository.get_active_token(
            token_hash=token_hash, current_time=current_time
        )
        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )
        user = await self.user_repository.get_by_id(refresh_token.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        return user

    async def revoke_refresh_token(self, token: str) -> None:
        """
        Revokes a refresh token.

        Args:
            token: The plain-text refresh token.

        Returns:
            None
        """
        token_hash = self.hash_token(token)
        refresh_token = await self.refresh_token_repository.get_by_token_hash(
            token_hash
        )

        if refresh_token and not refresh_token.revoked_at:
            await self.refresh_token_repository.revoke_token(refresh_token)
        return None

    async def revoke_access_token(self, token: str) -> None:
        """
        Revokes an access token by adding it to a blacklist in Redis.

        Args:
            token: The JWT access token.

        Returns:
            None
        """
        payload = self.decode_and_validate_access_token(token)
        exp = payload.get("exp")
        if exp:
            await redis_client.setex(
                f"bl:{token}", int(exp - datetime.now(timezone.utc).timestamp()), "1"
            )
            return None

    async def validate_reset_password_token(self, token: str) -> User:
        """
        Validates a reset password token and retrieves the user.

        Args:
            token: The reset password token.

        Returns:
            The associated User object.

        Raises:
            HTTPException: If token is invalid or user not found.
        """

        email = get_email_from_reset_password_token(token)
        user = await self.user_repository.get_by_email(email)
        if not user or user.reset_password_token is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Token wrong"
            )
        return user

    async def change_password(self, email: str, new_password: str):
        """
        Changes the password of a user.

        Args:
            email: The email of the user whose password is to be changed.
            new_password: The new password in plain-text.

        Returns:
            None

        Raises:
            HTTPException: If the user is not found.
        """
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        hashed_password = self._hash_password(new_password)
        await self.user_repository.change_password(email, hashed_password)
