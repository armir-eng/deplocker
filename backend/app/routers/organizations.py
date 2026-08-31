import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.organizations import OrganizationMembersModel, OrganizationModel
from app.schemas.organizations import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationRole,
)
from app.utils.auth.deplocker_auth import get_current_session
from app.utils.slug_generator import generate_slug

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/create",
    summary="New organization creation endpoint",
    response_model=OrganizationResponse,
)
async def create_organization(
    payload: OrganizationCreate,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> OrganizationModel:
    new_organization = OrganizationModel(
        owner_id=payload.user_id, name=payload.name, slug=generate_slug(payload.name)
    )
    db_session.add(new_organization)
    await db_session.commit()
    await db_session.refresh(new_organization)

    new_org_member = OrganizationMembersModel(
        user_id=payload.user_id,
        organization_id=new_organization.id,
        role=OrganizationRole.ADMIN,
    )
    db_session.add(new_org_member)
    await db_session.commit()

    return new_organization


@router.get("/{user_id}", summary="Get all organizations a user belongs to")
async def get_user_organizations(
    user_id: int,
    auth_session: dict = Depends(get_current_session),
    db_session: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    result = await db_session.scalars(
        select(OrganizationMembersModel.organization_id)
        .where(OrganizationMembersModel.user_id == user_id)
        .order_by(OrganizationMembersModel.joined_at)
    )

    organization_ids = result.all()

    organization_names_query_result = await db_session.execute(
        select(OrganizationModel.name).where(OrganizationModel.id.in_(organization_ids))
    )
    organization_names = organization_names_query_result.scalars().all()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"user_id": user_id, "organizations": organization_names},
    )
