from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Employee(Base):
    """Represents a candidate/user.

    Profile fields are nullable to allow creating the row on /start
    before the onboarding survey is complete.
    """

    __tablename__ = "employees"

    # Identity
    tuid: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Profile Data
    # Optional for start's partial initialization of a user
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cv_link: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Settings
    language_code: Mapped[str] = mapped_column(String, default="en", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    sessions: Mapped[List["SurveySession"]] = relationship(  # noqa: F821
        back_populates="employee", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Returns a string representation of the Employee."""
        return f"<Employee(tuid={self.tuid}, username={self.username})>"
