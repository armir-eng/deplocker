from __future__ import annotations

import logging
import re
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Annotated, Any
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError

from app.core import redis
from app.core.conf import settings
from app.core.database import get_db_session
from app.models import OrganizationModel, UserModel
from app.models.organizations import OrganizationMembersModel
from app.schemas.auth import SessionData, UserRegister, UserRole
from app.schemas.organizations import OrganizationRole
from app.tasks.account_confirmation import send_confirmation_email
from app.utils.auth.deplocker_auth import (
    authenticate_user,
    generate_jwt,
    get_current_session,
    get_password_hash,
)
from app.utils.auth.github_oauth import (
    fetch_github_access_token,
    fetch_github_user_email,
    fetch_github_user_info,
)
from app.utils.auth.google_oauth import (
    fetch_google_access_token,
    fetch_google_user_info,
)
from app.utils.slug_generator import generate_slug

if TYPE_CHECKING:
    from celery import Task
    from celery.result import AsyncResult
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/check-username")
async def check_username_availability(
    username: str, db_session: AsyncSession = Depends(get_db_session)
) -> dict[str, bool]:
    result = await db_session.execute(
        select(exists().where(UserModel.username == username))
    )

    return {"available": not result.scalar()}


async def _add_default_organization(db_session: AsyncSession, user: UserModel) -> None:
    # `organizations.name` and `.slug` are both globally unique, so the default
    # organization is named after its owner rather than a fixed string.
    name = f"{user.username}'s organization"
    organization = OrganizationModel(
        owner_id=user.id,
        name=name,
        slug=generate_slug(name),
    )
    db_session.add(organization)
    await db_session.flush()

    db_session.add(
        OrganizationMembersModel(
            user_id=user.id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
        )
    )


@router.post("/register", summary="Register a new user in platform")
async def register_new_user(
    payload: UserRegister, db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:

    existing_email = await db_session.scalar(
        select(UserModel.email).where(UserModel.email == payload.email)
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{payload.email}' email already exists!",
        )

    new_user = UserModel(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        password=get_password_hash(payload.password),
        role=payload.role,
    )
    db_session.add(new_user)
    await db_session.flush()
    await _add_default_organization(db_session, new_user)
    await db_session.commit()
    await db_session.refresh(new_user)

    # Send the confirmation email to the registered email address
    confirmation_email_task: Task = send_confirmation_email
    jwt_token = generate_jwt(
        sub=new_user.email, expire_minutes=1440
    )  # Generate a 24-hour valid token
    result: AsyncResult = confirmation_email_task.delay(new_user.email, jwt_token)
    task_id = result.id

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": (
                "Signup request successfully completed! "
                "You will shortly recieve a verification request in your email address..."
            ),
            "email_task_id": task_id,
        },
    )


@router.post("/account/confirm", summary="Account activation endpoint")
async def confirm_new_account(
    email: EmailStr, token: str, db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    try:
        token_data: dict[str, Any] = jwt.decode(
            token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

    except jwt.ExpiredSignatureError as exc:
        await redis.set("expired_activation:email", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Activation token has expired. Please request a new confirmation email.",
        ) from exc

    subject: str | None = token_data.get("sub")

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Token failed to validate! Account could not be activated!",
        )

    db_user: UserModel | None = await db_session.scalar(
        select(UserModel).where(UserModel.email == subject)
    )

    if db_user:
        db_user.is_active = True
        await db_session.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Account was successfully activated!"},
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "New account was not found in the system! "
                "Something must be wrong! Please, try the registration again."
            ),
        )


@router.post("/account/confirm/retry")
async def resend_confirmation_email(email: EmailStr) -> JSONResponse:
    # Send the confirmation email to the registered email address
    confirmation_email_task: Task = send_confirmation_email
    jwt_token = generate_jwt(sub=email)
    result: AsyncResult = confirmation_email_task.delay(email, jwt_token)
    task_id = result.id

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "A new confirmation request is being sent is being to your email.",
            "email_task_id": task_id,
        },
    )


@router.post("/login", summary="Login endpoint", response_model=SessionData)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    db_user = await authenticate_user(
        db_session, form_data.username, form_data.password
    )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate! Incorrect credentials were provided, or the account is not yet activated.",
        )

    db_user.last_login = func.now()
    await db_session.commit()

    session_data = SessionData(
        user_id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        role=db_user.role,
        created_at=db_user.created_at,
    )

    # Store login session data on cache
    session_id = str(uuid.uuid4())
    serialized_session_data = session_data.model_dump_json()
    await redis.setex(
        f"session:{session_id}", timedelta(days=1), serialized_session_data
    )

    response = JSONResponse(
        status_code=status.HTTP_200_OK, content=session_data.model_dump(mode="json")
    )

    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        secure=settings.ENVIRONMENT != "dev",
        samesite="strict",
        expires=int(timedelta(days=1).total_seconds()),
    )

    return response


@router.get("/session/check")
async def validate_session(
    session: dict = Depends(get_current_session),
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=session,
    )


def _oauth_failure_redirect(reason: str) -> RedirectResponse:
    """OAuth callbacks are browser navigations, so failures go back to the login
    page as a query parameter rather than rendering an API error body."""
    # `reason` can carry a provider-supplied error, so keep it to an opaque slug.
    code = re.sub(r"[^a-z_]", "", reason.lower())[:40] or "unknown_error"
    query = urlencode({"error": code})
    return RedirectResponse(f"{settings.FRONTEND_URL}/login?{query}")


async def _unique_username(db_session: AsyncSession, base: str) -> str:
    root = re.sub(r"[^a-zA-Z0-9_.-]", "", base).strip(".-_") or "user"
    candidate = root
    suffix = 1
    while await db_session.scalar(
        select(exists().where(UserModel.username == candidate))
    ):
        suffix += 1
        candidate = f"{root}-{suffix}"
    return candidate


async def _get_or_create_oauth_user(
    db_session: AsyncSession,
    *,
    email: str,
    full_name: str | None,
    username_hint: str,
) -> UserModel:
    db_user: UserModel | None = await db_session.scalar(
        select(UserModel).where(UserModel.email == email)
    )
    if db_user:
        return db_user

    username = await _unique_username(db_session, username_hint)
    new_user = UserModel(
        username=username,
        email=email,
        full_name=full_name or username,
        password=get_password_hash(uuid.uuid4().hex),
        role=UserRole.ADMIN,
        is_active=True,  # The provider already verified the address
    )

    try:
        db_session.add(new_user)
        await db_session.flush()
        await _add_default_organization(db_session, new_user)
        await db_session.commit()
    except IntegrityError:
        # A concurrent callback for the same account won the race.
        await db_session.rollback()
        db_user = await db_session.scalar(
            select(UserModel).where(UserModel.email == email)
        )
        if db_user is None:
            logger.exception("Could not provision an account for %s", email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Could not create an account for this email address.",
            ) from None
        return db_user

    await db_session.refresh(new_user)
    return new_user


async def _login_response(db_user: UserModel) -> RedirectResponse:
    session_data = SessionData(
        user_id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        role=db_user.role,
        created_at=db_user.created_at,
    )

    session_id = str(uuid.uuid4())
    await redis.setex(
        f"session:{session_id}", timedelta(days=1), session_data.model_dump_json()
    )

    response = RedirectResponse(settings.FRONTEND_URL)
    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        secure=settings.ENVIRONMENT != "dev",
        samesite="strict",
        expires=int(timedelta(days=1).total_seconds()),
    )
    return response


@router.get("/google/login")
async def google_oauth2_login() -> RedirectResponse:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(f"{settings.GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_oauth2_callback(
    code: str | None = None,
    error: str | None = None,
    db_session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    if error or not code:
        logger.info("Google callback without a usable code: %s", error or "no code")
        return _oauth_failure_redirect(error or "missing_code")

    try:
        token_response = await fetch_google_access_token(code)
        access_token = token_response.get("access_token")

        if not access_token:
            logger.warning("Google token exchange returned no access token")
            return _oauth_failure_redirect("google_token_exchange_failed")

        user_info = await fetch_google_user_info(access_token)
    except HTTPException:
        return _oauth_failure_redirect("google_unavailable")

    email = user_info.get("email")
    if not email:
        return _oauth_failure_redirect("google_email_missing")

    # An unverified address would let anyone claim an existing account by signing
    # up to the provider with its email.
    if not user_info.get("email_verified", False):
        logger.warning("Rejected an unverified Google address")
        return _oauth_failure_redirect("google_email_unverified")

    db_user = await _get_or_create_oauth_user(
        db_session,
        email=email,
        full_name=user_info.get("name"),
        username_hint=email.split("@")[0],
    )

    return await _login_response(db_user)


@router.get("/github/login")
async def github_oauth2_login() -> RedirectResponse:
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
    }
    return RedirectResponse(f"{settings.GITHUB_AUTH_URL}?{urlencode(params)}")


@router.get("/github/callback")
async def github_oauth2_callback(
    code: str | None = None,
    error: str | None = None,
    db_session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    if error or not code:
        logger.info("GitHub callback without a usable code: %s", error or "no code")
        return _oauth_failure_redirect(error or "missing_code")

    try:
        token_response = await fetch_github_access_token(code)
        access_token = token_response.get("access_token")

        if not access_token:
            logger.warning("GitHub token exchange returned no access token")
            return _oauth_failure_redirect("github_token_exchange_failed")

        user_info = await fetch_github_user_info(access_token)
        email = await fetch_github_user_email(access_token)
    except HTTPException:
        return _oauth_failure_redirect("github_unavailable")

    db_user = await _get_or_create_oauth_user(
        db_session,
        email=email,
        full_name=user_info.get("name"),
        username_hint=user_info.get("login") or email.split("@")[0],
    )

    return await _login_response(db_user)
