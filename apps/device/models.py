from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey

from apps.base.models import Base


class Device(Base):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    device_uuid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    def __str__(self):
        return f"{self.name} ({self.device_uuid})"
