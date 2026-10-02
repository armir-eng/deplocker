import logging
import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.projects import ProjectModel
from app.schemas.projects import ProjectCreate, ProjectFields, ProjectResponse
from app.utils.auth.shared import get_current_session
from app.utils.organizations.membership import (
    ensure_organization_member,
    get_member_project,
)
from app.utils.text.slug_generator import generate_slug

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "",
    summary="Project creation endpoint",
    status_code=201,
    response_model=ProjectResponse,
)
async def create_project(
    payload: ProjectCreate,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> ProjectModel:
    await ensure_organization_member(
        db_session, auth_session["user_id"], payload.organization_id
    )

    existing_project_name = await db_session.scalar(
        select(ProjectModel.name).where(ProjectModel.name == payload.name)
    )

    if existing_project_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A project with name '{payload.name}' already exists!",
        )

    new_project = ProjectModel(
        organization_id=payload.organization_id,
        name=payload.name,
        slug=generate_slug(payload.name),
        description=payload.description,
    )
    db_session.add(new_project)
    await db_session.commit()
    await db_session.refresh(new_project)

    return new_project


@router.get(
    "",
    summary="List an organization's projects, optionally filtered by name",
    response_model=list[ProjectResponse],
)
async def get_all_projects(
    org_id: uuid.UUID,
    name: str | None = None,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> Sequence[ProjectModel]:
    await ensure_organization_member(db_session, auth_session["user_id"], org_id)

    query = select(ProjectModel).where(ProjectModel.organization_id == org_id)
    if name is not None:
        query = query.where(ProjectModel.name == name)

    result = await db_session.execute(query)
    return result.scalars().all()


@router.get("/{id}", summary="Get project by ID", response_model=ProjectResponse)
async def get_project_by_id(
    id: uuid.UUID,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> ProjectModel:
    return await get_member_project(db_session, auth_session["user_id"], id)


@router.patch(
    "/{id}", summary="Project detail update endpoint", response_model=ProjectResponse
)
async def update_project(
    id: uuid.UUID,
    payload: ProjectFields,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> ProjectModel:
    project_record = await get_member_project(db_session, auth_session["user_id"], id)

    project_record.name = payload.name
    project_record.description = payload.description
    project_record.updated_at = func.now()
    await db_session.commit()
    await db_session.refresh(project_record)

    return project_record


@router.delete("/{id}", status_code=204, summary="Delete a project by ID")
async def delete(
    id: uuid.UUID,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> None:
    project_record = await get_member_project(db_session, auth_session["user_id"], id)

    await db_session.delete(project_record)
    await db_session.commit()
