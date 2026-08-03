from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.applications import ApplicationModel
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)
from app.utils.auth import get_current_session
from app.utils.slug_generator import generate_slug

router = APIRouter()


@router.post(
    "",
    summary="Application creation endpoint",
    status_code=201,
    response_model=ApplicationResponse,
)
async def create_application(
    payload: ApplicationCreate,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> ApplicationModel:
    existing_application_name = await db_session.scalar(
        select(ApplicationModel.name).where(ApplicationModel.name == payload.name)
    )

    if existing_application_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Application '{payload.name}' already exists!",
        )

    new_application = ApplicationModel(
        name=payload.name,
        slug=generate_slug(payload.name),
        project_id=payload.project_id,
        description=payload.description,
        git_url=payload.git_url,
        branch=payload.branch,
        dockerfile_path=payload.dockerfile_path,
        port=payload.port,
        env_vars=payload.env_vars,
        domain=payload.domain,
    )

    db_session.add(new_application)
    await db_session.commit()
    await db_session.refresh(new_application)

    return new_application


@router.get(
    "",
    summary="List applications, optionally filtered by name",
    response_model=list[ApplicationResponse],
)
async def list_applications(
    name: str | None = None,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> Sequence[ApplicationModel]:
    query = select(ApplicationModel)

    if name is not None:
        query = query.where(ApplicationModel.name == name)

    result = await db_session.execute(query)
    return result.scalars().all()


@router.get(
    "/{id}",
    summary="Get application by ID",
    response_model=ApplicationResponse,
)
async def get_application_by_id(
    id: str,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> ApplicationModel:
    result = await db_session.execute(
        select(ApplicationModel).where(ApplicationModel.id == id)
    )
    app_record = result.scalar()

    if app_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{id}' was not found!",
        )

    return app_record


@router.patch(
    "/{id}",
    summary="Application details update endpoint",
    response_model=ApplicationResponse,
)
async def update_application(
    id: str,
    payload: ApplicationUpdate,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> ApplicationModel:
    result = await db_session.execute(
        select(ApplicationModel).where(ApplicationModel.id == id)
    )

    app_record = result.scalar_one_or_none()

    if app_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{id}' was not found!",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(app_record, field, value)

    await db_session.commit()
    await db_session.refresh(app_record)

    return app_record


@router.delete(
    "/{id}",
    status_code=204,
    summary="Project deletion endpoint",
)
async def delete_application(
    id: str,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> None:
    result = await db_session.execute(
        select(ApplicationModel).where(ApplicationModel.id == id)
    )

    app_record = result.scalar_one_or_none()

    if app_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{id}' was not found!",
        )

    await db_session.delete(app_record)
    await db_session.commit()
