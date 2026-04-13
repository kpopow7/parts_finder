import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shade_catalog.db.base import Base
from shade_catalog.models.enums import UserRole


class User(Base):
    # "user" is a reserved identifier in PostgreSQL; avoid quoting footguns.
    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(String(32), nullable=False, default=UserRole.VIEWER)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
