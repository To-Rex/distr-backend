from datetime import datetime

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from apps.base.models import Base


class WorkingSession(Base):
    __tablename__ = "working_sessions"

    app: Mapped[str] = mapped_column(String(250), nullable=True)
    is_testing: Mapped[bool] = mapped_column(Boolean, nullable=True)
    session: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    device_name: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    user_rel = relationship("User", back_populates="working_sessions_rel")

    def __str__(self):
        return f"{self.session} - {self.device_name} - {self.user_id}"
