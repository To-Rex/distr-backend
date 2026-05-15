

from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PureBase(DeclarativeBase):
    pass


class AlembicVersion(PureBase):
    __tablename__ = 'alembic_version'

    # Alembic uses version_num as the primary key usually,
    # and it's a VARCHAR(32), not an Integer.
    version_num: Mapped[str] = mapped_column(String, primary_key=True)

    def __str__(self):
        return self.version_num
