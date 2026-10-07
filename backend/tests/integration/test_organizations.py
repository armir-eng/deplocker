"""An organization's name is a display label any organization may reuse; its
slug is the organization's handle, unique across all of them."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrganizationModel, ProjectModel, UserModel


@pytest.fixture()
async def test_user_id(
    test_db_session: AsyncSession, default_organization_id: uuid.UUID
) -> int:
    owner_id = await test_db_session.scalar(
        select(OrganizationModel.owner_id).where(
            OrganizationModel.id == default_organization_id
        )
    )
    assert owner_id is not None
    return owner_id


@pytest.fixture()
async def squatted_default_slug(test_db_session: AsyncSession) -> OrganizationModel:
    """Another user's organization holding the name and slug the test user's
    default organization would get."""
    owner = UserModel(
        username="squatter",
        email="squatter@deplocker.com",
        full_name="Squatter",
        password="not-a-real-hash",
    )
    test_db_session.add(owner)
    await test_db_session.flush()

    organization = OrganizationModel(
        owner_id=owner.id,
        name="test_user's organization",
        slug="test-users-organization",
    )
    test_db_session.add(organization)
    await test_db_session.flush()

    return organization


@pytest.mark.anyio
async def test_create_organization_with_taken_slug(
    authenticated_client: AsyncClient,
    test_user_id: int,
    foreign_project: ProjectModel,
) -> None:
    # "FOREIGN organization" is a different name, but gives the same slug as the
    # foreign project's organization.
    payload = {"user_id": test_user_id, "name": "FOREIGN organization"}

    response = await authenticated_client.post("/orgs/create", json=payload)
    assert response.status_code == 409


# `squatted_default_slug` comes first, so it exists before the test user
# registers.
@pytest.mark.anyio
async def test_default_organization_slug_is_suffixed_when_taken(
    squatted_default_slug: OrganizationModel,
    test_db_session: AsyncSession,
    default_organization_id: uuid.UUID,
) -> None:
    default_organization = await test_db_session.get(
        OrganizationModel, default_organization_id
    )
    assert default_organization is not None
    assert default_organization.name == squatted_default_slug.name
    assert default_organization.slug == "test-users-organization-2"
