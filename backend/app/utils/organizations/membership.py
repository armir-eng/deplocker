import uuid

from fastapi import HTTPException, status
from sqlalchemy import Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.applications import ApplicationModel
from app.models.deployments import DeploymentModel
from app.models.organizations import OrganizationMembersModel
from app.models.projects import ProjectModel


# The helpers below answer 404 for a resource outside the caller's organizations,
# so the response does not reveal whether it exists.
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


def select_member_projects(user_id: int) -> Select[tuple[ProjectModel]]:
    return (
        select(ProjectModel)
        .join(
            OrganizationMembersModel,
            OrganizationMembersModel.organization_id == ProjectModel.organization_id,
        )
        .where(OrganizationMembersModel.user_id == user_id)
    )


def select_member_applications(user_id: int) -> Select[tuple[ApplicationModel]]:
    return (
        select(ApplicationModel)
        .join(ProjectModel, ProjectModel.id == ApplicationModel.project_id)
        .join(
            OrganizationMembersModel,
            OrganizationMembersModel.organization_id == ProjectModel.organization_id,
        )
        .where(OrganizationMembersModel.user_id == user_id)
    )


def select_member_deployments(user_id: int) -> Select[tuple[DeploymentModel]]:
    return (
        select(DeploymentModel)
        .join(ApplicationModel, ApplicationModel.id == DeploymentModel.application_id)
        .join(ProjectModel, ProjectModel.id == ApplicationModel.project_id)
        .join(
            OrganizationMembersModel,
            OrganizationMembersModel.organization_id == ProjectModel.organization_id,
        )
        .where(OrganizationMembersModel.user_id == user_id)
    )


async def get_member_project(
    db_session: AsyncSession, user_id: int, project_id: uuid.UUID
) -> ProjectModel:
    project_record = await db_session.scalar(
        select_member_projects(user_id).where(ProjectModel.id == project_id)
    )
    if project_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' was not found!",
        )

    return project_record


async def get_member_application(
    db_session: AsyncSession, user_id: int, application_id: uuid.UUID
) -> ApplicationModel:
    application_record = await db_session.scalar(
        select_member_applications(user_id).where(ApplicationModel.id == application_id)
    )
    if application_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' was not found!",
        )

    return application_record


async def get_member_deployment(
    db_session: AsyncSession, user_id: int, deployment_id: uuid.UUID
) -> DeploymentModel:
    deployment_record = await db_session.scalar(
        select_member_deployments(user_id).where(DeploymentModel.id == deployment_id)
    )
    if deployment_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment '{deployment_id}' was not found!",
        )

    return deployment_record
