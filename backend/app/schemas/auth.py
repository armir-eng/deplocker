import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(Enum):
    OWNER = "owner"  # dedicated for platform-level operators (owners or administrators)
    ADMIN = "admin"  # dedicated for organization-level operators (admins or managers)
    USER = "user"  # the majority of users (who merely use the platform for their needs)


class UserBase(BaseModel):
    id: int


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: UserRole


class UserRegisterResponse(BaseModel):
    message: Literal[
        (
            "Signup request successfully completed! "
            "You will shortly recieve a verification request in your email address..."
        )
    ]
    email_task_id: uuid.UUID


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase, UserRegister):
    created_at: datetime
    updated_at: datetime
    last_login: datetime
    is_active: bool


class SessionData(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class PasskeyRegistration(BaseModel):
    """The credential `navigator.credentials.create()` produced, plus the label
    the user gives it. The credential is passed through to the WebAuthn library,
    which owns its shape."""

    name: str = Field(min_length=1, max_length=255)
    credential: dict[str, Any]


class PasskeyAuthentication(BaseModel):
    credential: dict[str, Any]


class PasskeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    last_used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
