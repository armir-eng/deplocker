import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class OrganizationRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class OrganizationCreate(BaseModel):
    user_id: int
    name: str


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    owner_id: int
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
