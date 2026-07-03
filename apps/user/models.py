import enum as python_enum  # Rename the import to avoid conflict
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SQLAlchemyEnum  # Explicitly import the SA type
from sqlalchemy import ForeignKey
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from apps.base.models import Base
from apps.branch.models import Branch
from apps.company.models import Company
from apps.location.models import Location
from apps.working_session_tracking.models import WorkingSession
from config.security import generate_access_token, get_expiration_date


class UserType(str, python_enum.Enum):
    USER = "USER"
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    SUPERVISOR = "SUPERVISOR"
    AGENT = "AGENT"
    DELIVERER = "DELIVERER"
    VENDOR_AGENT = "VENDOR_AGENT"
    CLIENT = "CLIENT"
    DEALER = "DEALER"
    FACTORY = "FACTORY"
    CEO = "CEO"
    FINANCIST = "FINANCIST"
    WAREHOUSE = "WAREHOUSE"
    SALESMAN = "SALESMAN"
    CASHIER = "CASHIER"
    HR = "HR"
    MARKETING = "MARKETING"
    EXTERNAL_SELLER = "EXTERNAL_SELLER"
    MERCHANDISER = "MERCHANDISER"


class UserStatus(str, python_enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"


class User(Base):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(1024), nullable=False)

    first_name: Mapped[Optional[str]] = mapped_column(String)
    last_name: Mapped[Optional[str]] = mapped_column(String)

    phone_number: Mapped[Optional[str]] = mapped_column(String)
   

    user_type: Mapped[UserType] = mapped_column(
        SQLAlchemyEnum(UserType, native_enum=False),
        default=UserType.USER,
        nullable=False,
        index=True
    )

    user_status: Mapped[UserStatus] = mapped_column(
        SQLAlchemyEnum(UserStatus, native_enum=False),
        default=UserStatus.ACTIVE,
        nullable=True,
        index=True
    )

    user_1c_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True)

    user_1c_login: Mapped[Optional[str]] = mapped_column(
        String, nullable=True)
    user_1c_password: Mapped[Optional[str]
                             ] = mapped_column(String, nullable=True)

    fcm_token: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True)

    # 1. Add the Foreign Key column
    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id"), nullable=True)
    # 2. Add the relationship object
    company_rel: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="users")

    branch_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("branches.id"), nullable=True)
    branch_rel: Mapped[Optional["Branch"]] = relationship(
        "Branch", back_populates="users")

    # 1. The Foreign Key pointing to another user's ID
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # 2. The relationship to the Manager (the "Parent")
    # CHANGE THIS LINE: Wrap id in quotes or use a lambda
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side="User.id",  # <--- Change this to a string
        back_populates="agents"
    )

    # 3. The relationship to the Agents (the "Children")
    agents: Mapped[list["User"]] = relationship(
        "User",
        back_populates="manager"
    )

    # Location
    location_rel: Mapped[list["Location"]] = relationship(
        "Location", back_populates="user_rel",  cascade="all, delete-orphan")

    working_sessions_rel: Mapped[list["WorkingSession"]] = relationship(
        "WorkingSession", back_populates="user_rel", cascade="all, delete-orphan"
    )

    def __str__(self):
        return str(self.username)


class AccessToken(Base):
    __tablename__ = 'access_tokens'
    access_token: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True, default=generate_access_token)
    expires_in: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=get_expiration_date)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user: Mapped[User] = relationship("User", lazy="joined", )
