from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.conf import settings
from app.models import UserModel
from app.schemas.auth import UserRole

GOOGLE_USER = {
    "email": "oauth.user@gmail.com",
    "name": "OAuth User",
}


@pytest.mark.anyio
async def test_google_login_redirects_to_google(client: AsyncClient) -> None:
    """`GET /auth/google` should 307-redirect to Google's consent screen with
    the expected OAuth query parameters."""

    response = await client.get("/auth/google", follow_redirects=False)

    assert response.status_code == 307

    location = response.headers["location"]
    assert location.startswith(settings.GOOGLE_AUTH_URL)

    query = parse_qs(urlparse(location).query)
    assert query["client_id"] == [settings.GOOGLE_CLIENT_ID]
    assert query["redirect_uri"] == [settings.GOOGLE_REDIRECT_URI]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["openid email profile"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]


@pytest.mark.anyio
async def test_google_callback_creates_new_user(
    client: AsyncClient, test_db_session: AsyncSession
) -> None:
    """A callback for an unknown Google account should provision a new active
    user, set a session cookie and redirect to the frontend."""

    with (
        patch(
            "app.routers.auth.fetch_google_access_token",
            new=AsyncMock(return_value={"access_token": "valid-access-token"}),
        ),
        patch(
            "app.routers.auth.fetch_google_user_info",
            new=AsyncMock(return_value=GOOGLE_USER),
        ),
    ):
        response = await client.get(
            "/auth/google/callback",
            params={"code": "valid-auth-code"},
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == settings.FRONTEND_URL
    assert "session_id" in response.cookies

    db_user = await test_db_session.scalar(
        select(UserModel).where(UserModel.email == GOOGLE_USER["email"])
    )
    assert db_user is not None
    assert db_user.username == "oauth.user"
    assert db_user.full_name == GOOGLE_USER["name"]
    assert db_user.role == UserRole.ADMIN
    assert db_user.is_active is True


@pytest.mark.anyio
async def test_google_callback_existing_user_does_not_duplicate(
    client: AsyncClient, test_db_session: AsyncSession
) -> None:
    """A callback for an already-registered email should log the user in
    without creating a second account."""

    mock_token = AsyncMock(return_value={"access_token": "valid-access-token"})
    mock_user_info = AsyncMock(return_value=GOOGLE_USER)

    with (
        patch("app.routers.auth.fetch_google_access_token", new=mock_token),
        patch("app.routers.auth.fetch_google_user_info", new=mock_user_info),
    ):
        first = await client.get(
            "/auth/google/callback",
            params={"code": "valid-auth-code"},
            follow_redirects=False,
        )
        second = await client.get(
            "/auth/google/callback",
            params={"code": "another-valid-code"},
            follow_redirects=False,
        )

    assert first.status_code == 307
    assert second.status_code == 307

    user_count = await test_db_session.scalar(
        select(func.count())
        .select_from(UserModel)
        .where(UserModel.email == GOOGLE_USER["email"])
    )
    assert user_count == 1


@pytest.mark.anyio
async def test_google_callback_missing_access_token(client: AsyncClient) -> None:
    """If Google's token exchange returns no access token, the callback should
    fail with a 400."""

    with patch(
        "app.routers.auth.fetch_google_access_token",
        new=AsyncMock(return_value={}),
    ):
        response = await client.get(
            "/auth/google/callback",
            params={"code": "bad-auth-code"},
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Failed to obtain access token from Google."


@pytest.mark.anyio
async def test_google_callback_missing_email(client: AsyncClient) -> None:
    """If Google's user info contains no email, the callback should fail with a
    400."""

    with (
        patch(
            "app.routers.auth.fetch_google_access_token",
            new=AsyncMock(return_value={"access_token": "valid-access-token"}),
        ),
        patch(
            "app.routers.auth.fetch_google_user_info",
            new=AsyncMock(return_value={"name": "No Email"}),
        ),
    ):
        response = await client.get(
            "/auth/google/callback",
            params={"code": "valid-auth-code"},
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Failed to obtain user email from Google."


@pytest.mark.anyio
async def test_google_callback_requires_code(client: AsyncClient) -> None:
    """The `code` query parameter is required by the callback endpoint."""

    response = await client.get("/auth/google/callback", follow_redirects=False)
    assert response.status_code == 422
