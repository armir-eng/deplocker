import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, EmailStr


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
