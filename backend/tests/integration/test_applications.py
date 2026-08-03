from collections.abc import Callable

import pytest
from faker import Faker
from httpx import AsyncClient, Response
from pydantic import ValidationError

from app.schemas.applications import ApplicationResponse

fake = Faker()


@pytest.mark.anyio
async def test_list_applications(
    application_factory: Callable, client: AsyncClient
) -> None:
    for _ in range(10):
        await application_factory(
            name=fake.name(),
            description=fake.sentence(),
            git_url=fake.url(),
            env_vars={"DB_USER": fake.user_name(), "DB_PASSWORD": fake.password()},
            domain=fake.domain_name(),
        )

    response = await client.get("/applications")
    response_data = response.json()
    assert type(response_data) is list
    assert len(response_data) == 10


@pytest.mark.anyio
async def test_get_application_by_id(
    application_create_test: Response, client: AsyncClient
) -> None:
    new_application_data = application_create_test.json()
    new_application_id = new_application_data["id"]

    response = await client.get(f"/applications/{new_application_id}")
    assert response.status_code == 200

    try:
        response_data = response.json()
        schema_object = ApplicationResponse(**response_data)

        assert str(schema_object.project_id) == new_application_data["project_id"]
        assert schema_object.name == new_application_data["name"]
        assert schema_object.description == new_application_data["description"]
        assert schema_object.git_url == new_application_data["git_url"]
        assert schema_object.env_vars == new_application_data["env_vars"]
        assert schema_object.domain == new_application_data["domain"]

        # Assert the default values (intentionally not provided in the request payload)
        assert schema_object.branch == "main"
        assert schema_object.dockerfile_path == "./Dockerfile"
        assert schema_object.port == 8000
        assert schema_object.desired_replicas == 1

    except ValidationError as e:
        pytest.fail(f"Response validation failed: {e.errors()}")
