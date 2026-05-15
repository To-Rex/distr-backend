from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.base.models import Base
from apps.company.models import Company, SecurityKey
from apps.user.models import User


class Notification(Base):
    __tablename__ = "notifications"

    title: Mapped[str] = mapped_column(String(250), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    date: Mapped[str] = mapped_column(
        String(10), nullable=True)  # Format: DD.MM.YYYY
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id"), nullable=True, index=True
    )
    company_rel: Mapped[Optional["Company"]] = relationship(
        "Company", lazy="selectin"
    )

    user_1c_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True
    )

    user_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )

    # Relationship to track read status per user
    user_statuses: Mapped[list["NotificationUserStatus"]] = relationship(
        "NotificationUserStatus",
        back_populates="notification_rel",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __str__(self):
        return f"Notification: {self.title} - {self.date}"


class NotificationUserStatus(Base):
    __tablename__ = "notification_user_status"

    notification_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    notification_rel: Mapped["Notification"] = relationship(
        "Notification", back_populates="user_statuses", lazy="selectin"
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_rel: Mapped["User"] = relationship(
        "User", lazy="selectin"
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __str__(self):
        return f"NotificationStatus: notification={self.notification_id} user={self.user_id} read={self.is_read}"
