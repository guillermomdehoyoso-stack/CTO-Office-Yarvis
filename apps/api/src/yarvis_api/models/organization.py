from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yarvis_api.models.base import Base, TimestampedUUIDMixin


class Organization(TimestampedUUIDMixin, Base):
    __tablename__ = "organizations"

    legal_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_type: Mapped[str] = mapped_column(String(50), nullable=False, default="organization")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    cases = relationship("Case", back_populates="owner_organization")
