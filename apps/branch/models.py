from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.base.models import Base


class Branch(Base):
    __tablename__ = "branches"

    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id"), nullable=True, index=True
    )

    company_rel: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="branches"
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="branch_rel"
    )

    def __str__(self):
        return str(self.name)
