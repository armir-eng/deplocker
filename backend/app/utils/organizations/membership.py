import uuid

from fastapi import HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organizations import OrganizationMembersModel
from app.models.projects import ProjectModel


# Both helpers answer 404 for a resource outside the caller's organizations, so
# the response does not reveal whether it exists.
async def ensure_organization_member(
    db_session: AsyncSession, user_id: int, organization_id: uuid.UUID
) -> None:
    is_member = await db_session.scalar(
        select(
            exists().where(
                OrganizationMembersModel.user_id == user_id,
                OrganizationMembersModel.organization_id == organization_id,
            )
        )
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{organization_id}' was not found!",
        )


async def get_member_project(
    db_session: AsyncSession, user_id: int, project_id: uuid.UUID
) -> ProjectModel:
    project_record = await db_session.scalar(
        select(ProjectModel)
        .join(
            OrganizationMembersModel,
            OrganizationMembersModel.organization_id == ProjectModel.organization_id,
        )
        .where(
            ProjectModel.id == project_id,
            OrganizationMembersModel.user_id == user_id,
        )
    )
    if project_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' was not found!",
        )

    return project_record
