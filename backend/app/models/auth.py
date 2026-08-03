from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.schemas.auth import UserRole


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.USER
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # This field indicates the verification status of a registered user.
    # Before account's confirmation, the user's identity is not presumably trusted.
    # Through an email verification step, the registration is fully completed.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    organizations: Mapped[list["OrganizationModel"]] = relationship(  # type: ignore[name-defined]
        secondary="organization_members", back_populates="members", viewonly=True
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, email={self.email})"
