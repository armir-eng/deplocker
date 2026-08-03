import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.auth import SessionData, UserRegisterResponse, UserRole
from app.utils.auth import generate_jwt

REGISTER_PAYLOAD = {
    "username": "armir",
    "email": "armir.shehaj@gmail.com",
    "full_name": "Armir Shehaj",
    "role": "admin",
    "password": "Armir2026!",
}


@pytest.mark.anyio
async def test_register(client: AsyncClient) -> None:
    fake_result = MagicMock()
    fake_result.id = "550e8400-e29b-41d4-a716-446655440000"

    with patch(
        "app.routers.auth.send_confirmation_email.delay",
        return_value=fake_result,
    ):
        response = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    response_data: dict = response.json()

    try:
        schema_object = UserRegisterResponse(**response_data)
        assert schema_object.message == (
            "Signup request successfully completed! "
            "You will shortly recieve a verification request in your email address..."
        )
        assert type(schema_object.email_task_id) is uuid.UUID

    except ValidationError as e:
        pytest.fail(f"Response validation failed: {e.errors()}")


@pytest.mark.anyio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    fake_result = MagicMock()
    fake_result.id = "550e8400-e29b-41d4-a716-446655440000"

    with patch(
        "app.routers.auth.send_confirmation_email.delay",
        return_value=fake_result,
    ):
        await client.post("/auth/register", json=REGISTER_PAYLOAD)
        response = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 409


@pytest.mark.anyio
async def test_login(client: AsyncClient) -> None:
    fake_result = MagicMock()
    fake_result.id = "550e8400-e29b-41d4-a716-446655440000"

    with patch(
        "app.routers.auth.send_confirmation_email.delay", return_value=fake_result
    ):
        await client.post("/auth/register", json=REGISTER_PAYLOAD)

    token = generate_jwt(sub=REGISTER_PAYLOAD["email"])
    await client.post(
        "/auth/account/confirm",
        params={"email": REGISTER_PAYLOAD["email"], "token": token},
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": REGISTER_PAYLOAD["username"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert response.status_code == 200

    response_data: dict = response.json()

    try:
        schema_object = SessionData(**response_data)
        assert type(schema_object.user_id) is int
        assert schema_object.email == REGISTER_PAYLOAD["email"]
        assert schema_object.role == UserRole.ADMIN
        assert type(schema_object.created_at) is datetime

    except ValidationError as e:
        pytest.fail(f"Response validation failed: {e.errors()}")


@pytest.mark.anyio
async def test_session_check(client: AsyncClient) -> None:
    fake_result = MagicMock()
    fake_result.id = "550e8400-e29b-41d4-a716-446655440000"

    with patch(
        "app.routers.auth.send_confirmation_email.delay", return_value=fake_result
    ):
        await client.post("/auth/register", json=REGISTER_PAYLOAD)

    token = generate_jwt(sub=REGISTER_PAYLOAD["email"])
    await client.post(
        "/auth/account/confirm",
        params={"email": REGISTER_PAYLOAD["email"], "token": token},
    )

    await client.post(
        "/auth/login",
        data={
            "username": REGISTER_PAYLOAD["username"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    # The cookie is automatically stored and resent between requests by httpx
    response = await client.get("/auth/session/check")
    assert response.status_code == 200

    response_data: dict = response.json()

    try:
        schema_object = SessionData(**response_data)
        assert type(schema_object.user_id) is int
        assert schema_object.username == REGISTER_PAYLOAD["username"]
        assert schema_object.role == UserRole.ADMIN
        assert type(schema_object.created_at) is datetime

    except ValidationError as e:
        pytest.fail(f"Response validation failed: {e.errors()}")
