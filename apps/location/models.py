from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.base.models import Base
from datetime import datetime
from typing import Any
from sqlalchemy import ForeignKey, String, Boolean, JSON, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean


class Location(Base):
    __tablename__ = "locations"

    latitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    longitude: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0)

    device_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)
    user_rel = relationship(
        "User", back_populates="location_rel", lazy="selectin"
    )

    def __str__(self):
        return f"Location: {self.latitude}, {self.longitude} {self.is_active} {self.user_id}"
