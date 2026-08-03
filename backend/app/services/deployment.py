import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationModel
from app.models.deployments import DeploymentModel


class DeploymentService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def _get_application(self, application_id: uuid.UUID) -> uuid.UUID | None:
        result = await self.db_session.execute(
            select(ApplicationModel.id).where(ApplicationModel.id == application_id)
        )
        application = result.scalar()
        return application

    async def _get_deployment(self, id: uuid.UUID) -> DeploymentModel:
        result = await self.db_session.execute(
            select(DeploymentModel).where(DeploymentModel.id == id)
        )

        deployment = result.scalar()

        if deployment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment '{id}' was not found!",
            )

        return deployment

    async def _delete_deployment_record(self, id: uuid.UUID) -> None:
        deployment = await self._get_deployment(id)
        await self.db_session.delete(deployment)
        await self.db_session.commit()

    async def create_deployment(self, application_id: uuid.UUID) -> DeploymentModel:
        application = await self._get_application(application_id)

        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application '{application_id}' was not found!",
            )

        new_deployment = DeploymentModel(application_id=application_id)
        self.db_session.add(new_deployment)
        await self.db_session.commit()
        await self.db_session.refresh(new_deployment)
        return new_deployment

    async def get_deployment(self, id: uuid.UUID) -> DeploymentModel:
        return await self._get_deployment(id)

    async def get_all_deployments(self) -> Sequence[DeploymentModel]:
        result = await self.db_session.execute(select(DeploymentModel))
        return result.scalars().all()

    async def delete_deployment(self, id: uuid.UUID) -> None:
        await self._delete_deployment_record(id)
