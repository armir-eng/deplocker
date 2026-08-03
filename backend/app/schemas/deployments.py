import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DeploymentStatus(StrEnum):
    # Queue/preparation
    PENDING = "pending"  # Created, waiting to start

    # Active phases
    CLONING = "cloning"  # Cloning Git repository
    BUILDING = "building"  # Building Docker image
    PUSHING = "pushing"  # Pushing image to registry (optional)
    DEPLOYING = "deploying"  # Starting container
    HEALTH_CHECKING = "health_checking"  # Waiting for health checks

    # Terminal states
    SUCCESS = "success"  # Deployment completed successfully
    FAILED = "failed"  # Deployment failed
    CANCELLED = "cancelled"  # User cancelled deployment


class DeploymentBase(BaseModel):
    id: uuid.UUID
    status: DeploymentStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    commit_hash: str | None = None


class DeploymentCreate(BaseModel):
    application_id: uuid.UUID


class DeploymentResponse(DeploymentBase, DeploymentCreate):
    pass
