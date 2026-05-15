from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Integer, String, Text
from datetime import datetime


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, default=None
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, default=None
    )
