import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.schemas.applications import AppStatus


class ApplicationModel(Base):
    __tablename__ = "applications"

    # Identity fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    slug: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Git source-related fields
    git_url: Mapped[str] = mapped_column(String(500), nullable=False)
    branch: Mapped[str] = mapped_column(String(100), nullable=False, default="main")
    dockerfile_path: Mapped[str] = mapped_column(
        String(255), nullable=False, default="./Dockerfile"
    )

    # Deployment config fields
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=8000)
    env_vars: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    domain: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    desired_replicas: Mapped[int] = mapped_column(Integer, default=1)

    # State
    status: Mapped[AppStatus] = mapped_column(
        Enum(AppStatus), nullable=False, default=AppStatus.CREATED
    )

    # Container info
    container_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # Docker container IDs are 64 hex chars
    image_tag: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )
    last_deployed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relational instances
    project: Mapped["ProjectModel"] = relationship(back_populates="applications")  # type: ignore[name-defined]
    deployments: Mapped[list["DeploymentModel"]] = relationship(  # type: ignore[name-defined]
        back_populates="application", cascade="all, delete-orphan"
    )
