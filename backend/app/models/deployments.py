import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.schemas.deployments import DeploymentStatus


class DeploymentModel(Base):
    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id"), index=True
    )
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus), nullable=False, default="pending"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=True)

    # Relational instances
    application: Mapped["ApplicationModel"] = relationship(back_populates="deployments")  # type: ignore[name-defined]
    logs: Mapped[list["DeploymentLogsModel"]] = relationship(
        back_populates="deployment", order_by="DeploymentLogsModel.id"
    )

    # Composite index that enables filtering/sorting queries by application and time
    # For example: Getting the most recent deployments for application
    __table_args__ = (
        Index("ix_deployments_app_started", "application_id", "started_at"),
    )


class DeploymentLogsModel(Base):
    __tablename__ = "deployment_logs"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, index=True, default=uuid.uuid4
    )
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=False
    )
    logged_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )
    line: Mapped[str] = mapped_column(Text, nullable=False)

    deployment: Mapped["DeploymentModel"] = relationship(back_populates="logs")
