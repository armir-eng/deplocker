import logging
from datetime import datetime, timedelta
from typing import Any, cast

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import redis
from app.core.conf import settings
from app.models.auth import UserModel
from app.schemas.auth import SessionData

password_hash = PasswordHash.recommended()
oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

logger = logging.getLogger(__name__)


def get_password_hash(plain_password: str) -> str:
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def generate_jwt(
    sub: str, expire_minutes: int = settings.ACCESS_TOKEN_EXPIRES_MINUTES
) -> str:
    token_data = {"sub": sub, "exp": datetime.now() + timedelta(minutes=expire_minutes)}
    token = jwt.encode(
        payload=token_data, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return token


async def get_user_by_identifier(
    db_session: AsyncSession, identifier: str
) -> UserModel | None:
    return cast(
        "UserModel | None",
        await db_session.scalar(
            select(UserModel).where(
                or_(UserModel.username == identifier, UserModel.email == identifier)
            )
        ),
    )


async def authenticate_user(
    db_session: AsyncSession, identifier: str, plain_password: str
) -> UserModel | None:
    db_user: UserModel | None = await get_user_by_identifier(db_session, identifier)

    if db_user is None:
        return None

    is_password_valid = verify_password(plain_password, db_user.password)
    if not is_password_valid:
        return None

    if not db_user.is_active:
        return None

    return db_user


async def get_current_session(request: Request) -> dict[str, Any]:
    session_id = request.cookies.get("session_id")
    logger.info(f"session_id: {session_id}")

    if not session_id:
        logger.info(f"session_id: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="There is no active session!",
        )

    session_data = await redis.get(f"session:{session_id}")
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired, or is invalid!",
        )

    return SessionData.model_validate_json(session_data).model_dump(mode="json")
