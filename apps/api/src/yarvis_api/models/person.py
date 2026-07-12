from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class Person(TimestampedUUIDMixin, Base):
    __tablename__ = "people"

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    primary_cases = relationship("Case", back_populates="primary_person")
