from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, ForeignKey
from apps.base.models import Base


class App(Base):
    __tablename__ = "apps"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=True)
    versions: Mapped[list["Version"]] = relationship(
        "Version", back_populates="app_rel"
    )

    def __str__(self):
        return str(self.name)


class Version(Base):
    __tablename__ = "app_versions"

    version: Mapped[str] = mapped_column(String(20), nullable=False)
    build_number: Mapped[int] = mapped_column(Integer, nullable=False)
    force_update: Mapped[bool] = mapped_column(Boolean, default=False)
    update_url: Mapped[str] = mapped_column(String(500), nullable=True)
    message: Mapped[str] = mapped_column(String(1000), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=True)

    file_blob = None

    app_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("apps.id"), nullable=False
    )
    app_rel: Mapped["App"] = relationship("App", back_populates="versions")

    def __str__(self):
        return f"{self.app_id} - {self.platform} - {self.version}"
