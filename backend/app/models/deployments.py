import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
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

    # Log storage information
    log_uri: Mapped[str] = mapped_column(
        String(255), nullable=True
    )  # URI to the log file locally, or in a cloud storage service (e.g., S3, GCS)
    log_size: Mapped[int] = mapped_column(
        nullable=True
    )  # The log file size is expressed in bytes

    # Relational instances
    application: Mapped["ApplicationModel"] = relationship(back_populates="deployments")  # type: ignore[name-defined]

    # Composite index that enables filtering/sorting queries by application and time
    # For example: Getting the most recent deployments for application
    __table_args__ = (
        Index("ix_deployments_app_started", "application_id", "started_at"),
    )
