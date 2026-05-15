
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey

from apps.base.models import Base
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class Company(Base):
    __tablename__ = 'companies'

    name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True)

    # sparse=True in Mongo is usually handled by unique=True + nullable=True in SQL
    inn: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)

    base_url: Mapped[str] = mapped_column(String, default="", )

    asl_belgi_token: Mapped[str] = mapped_column(String, default="")

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="company_rel")
    security_key_rel: Mapped["SecurityKey"] = relationship(
        "SecurityKey", back_populates="company_rel", uselist=False)

    def __str__(self):
        return str(self.name)


class SecurityKey(Base):
    __tablename__ = 'security_keys'

    # Add ForeignKey here linking to the 'companies' table 'id' column
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id"),  # This is the missing piece
        unique=True,
        nullable=False,
        index=True
    )

    company_rel: Mapped["Company"] = relationship(
        "Company",
        back_populates="security_key_rel"
    )

    key: Mapped[str] = mapped_column(String, nullable=False)

    def __str__(self):
        return f"Company ID: {self.company_id} - Key: {self.key}"
