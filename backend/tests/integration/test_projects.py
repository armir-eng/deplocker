from collections.abc import Callable
from datetime import datetime

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from pydantic import ValidationError

from app.schemas.projects import ProjectResponse, ProjectStatus

fake = Faker()


@pytest.mark.anyio
async def test_list_projects(client: AsyncClient, project_factory: Callable) -> None:
    for _ in range(10):
        await project_factory(name=fake.company(), description=fake.sentence())

    response = await client.get("/projects")
    assert response.status_code == 200

    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 10


@pytest.mark.anyio
async def test_get_project_by_id(
    client: AsyncClient, project_create_test: Response
) -> None:
    new_project_data = project_create_test.json()
    new_project_id = new_project_data["id"]

    response = await client.get(f"/projects/{new_project_id}")
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
    client: AsyncClient, project_create_test: Response
) -> None:
    new_project_data = project_create_test.json()
    new_project_name = new_project_data["name"]

    response = await client.get(f"/projects?name={new_project_name}")
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
    client: AsyncClient, project_create_test: Response
) -> None:
    created_id = project_create_test.json()["id"]

    delete_response = await client.delete(f"/projects/{created_id}")
    assert delete_response.status_code == 204
