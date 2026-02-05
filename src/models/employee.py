from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Employee(Base):
    """Represents a candidate/user.

    Profile fields are nullable to allow creating the row on /start
    before the onboarding survey is complete.

    Attributes:
        tuid (int): Telegram user ID, used as the primary key.
        username (Optional[str]): Telegram username.
        full_name (Optional[str]): Full name of the candidate.
        phone (Optional[str]): Contact phone number.
        cv_link (Optional[str]): Link to the candidate's CV.
        language_code (str): Preferred language for the bot interface (default: "ru").
        created_at (datetime): Timestamp when the record was created.
        updated_at (Optional[datetime]): Timestamp when the record was last updated.
        sessions (List[SurveySession]): List of survey sessions associated with the employee.
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
    language_code: Mapped[str] = mapped_column(String, default="ru", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    sessions: Mapped[List["SurveySession"]] = relationship(  # noqa: F821
        back_populates="employee", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Returns a string representation of the Employee.

        Returns:
            str: Representation containing tuid and username.
        """
        return f"<Employee(tuid={self.tuid}, username={self.username})>"
