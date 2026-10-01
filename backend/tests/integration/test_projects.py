import uuid
from collections.abc import Callable
from datetime import datetime

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from pydantic import ValidationError

from app.core import redis
from app.schemas.projects import ProjectResponse, ProjectStatus

fake = Faker()
PROJECT_ID = uuid.uuid4()
PROJECT_ROUTES = [
    ("POST", "/projects"),
    ("GET", "/projects"),
    ("GET", f"/projects/{PROJECT_ID}"),
    ("PATCH", f"/projects/{PROJECT_ID}"),
    ("DELETE", f"/projects/{PROJECT_ID}"),
]


@pytest.mark.anyio
async def test_list_projects(
    authenticated_client: AsyncClient, project_factory: Callable
) -> None:
    for _ in range(10):
        await project_factory(name=fake.company(), description=fake.sentence())

    response = await authenticated_client.get("/projects")
    assert response.status_code == 200

    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 10


@pytest.mark.anyio
async def test_get_project_by_id(
    authenticated_client: AsyncClient, project_create_test: Response
) -> None:
    new_project_data = project_create_test.json()
    new_project_id = new_project_data["id"]

    response = await authenticated_client.get(f"/projects/{new_project_id}")
    assert response.status_code == 200

    try:
        response_data = response.json()
        schema_object = ProjectResponse(**response_data)
        assert str(schema_object.id) == new_project_id
        assert schema_object.name == new_project_data["name"]
        assert schema_object.description == new_project_data["description"]
        assert schema_object.slug == new_project_data["slug"]
        assert schema_object.status == ProjectStatus.ACTIVE
        assert type(schema_object.created_at) is datetime
        assert type(schema_object.updated_at) is datetime

    except ValidationError as e:
        pytest.fail(f"Response data is invalid: {response_data}:{e.errors()}")


@pytest.mark.anyio
async def test_get_project_by_name(
    authenticated_client: AsyncClient, project_create_test: Response
) -> None:
    new_project_data = project_create_test.json()
    new_project_name = new_project_data["name"]

    response = await authenticated_client.get(f"/projects?name={new_project_name}")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1

    try:
        schema_object = ProjectResponse(**response_data[0])
        assert str(schema_object.id) == new_project_data["id"]
        assert schema_object.name == new_project_name
        assert schema_object.description == new_project_data["description"]
        assert schema_object.slug == new_project_data["slug"]
        assert schema_object.status == ProjectStatus.ACTIVE
        assert type(schema_object.created_at) is datetime
        assert type(schema_object.updated_at) is datetime

    except ValidationError as e:
        pytest.fail(f"Response data is invalid: {e.errors()!s}")


@pytest.mark.anyio
async def test_delete_project(
    authenticated_client: AsyncClient, project_create_test: Response
) -> None:
    created_id = project_create_test.json()["id"]

    delete_response = await authenticated_client.delete(f"/projects/{created_id}")
    assert delete_response.status_code == 204


@pytest.mark.anyio
async def test_create_project_in_foreign_organization(
    authenticated_client: AsyncClient,
) -> None:
    payload = {
        "name": "Deplocker",
        "description": "Easily deploy and scale your dockerized projects.",
        "organization_id": str(uuid.uuid4()),
    }

    response = await authenticated_client.post("/projects", json=payload)
    assert response.status_code == 404


@pytest.mark.anyio
@pytest.mark.parametrize(("method", "path"), PROJECT_ROUTES)
@pytest.mark.parametrize("session_id", [None, "invalid-session"])
async def test_projects_require_authentication(
    client: AsyncClient, method: str, path: str, session_id: str | None
) -> None:
    if session_id is not None:
        client.cookies.set("session_id", session_id)

    response = await client.request(method, path)
    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize(("method", "path"), PROJECT_ROUTES)
async def test_projects_reject_expired_session(
    authenticated_client: AsyncClient, method: str, path: str
) -> None:
    # A session expires when Redis drops its key at the end of the TTL; deleting
    # the key reaches the same state without waiting for it.
    session_key = f"session:{authenticated_client.cookies['session_id']}"
    assert await redis.client.delete(session_key) == 1

    response = await authenticated_client.request(method, path)
    assert response.status_code == 401
