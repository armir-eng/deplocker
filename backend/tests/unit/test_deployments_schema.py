import uuid

import pytest

from app.schemas.deployments import DeploymentCreate


@pytest.mark.anyio
async def test_deployment_create_defaults() -> None:
    payload = {"application_id": str(uuid.uuid4())}
    schema_object = DeploymentCreate(**payload)

    assert type(schema_object.application_id) is uuid.UUID
