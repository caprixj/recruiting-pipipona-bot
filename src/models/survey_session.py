from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.employee import Employee
from src.models.enums import SurveyStatus, SurveyType


class SurveySession(Base):
    """Represents a single instance of a test/survey taken by an Employee."""

    __tablename__ = "survey_sessions"

    session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Key
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.tuid"), nullable=False)

    # Meta (Enums)
    survey_type: Mapped[SurveyType] = mapped_column(SAEnum(SurveyType, native_enum=False), nullable=False)
    status: Mapped[SurveyStatus] = mapped_column(
        SAEnum(SurveyStatus, native_enum=False), default=SurveyStatus.IN_PROGRESS, nullable=False
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Payload
    answers: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        """Returns a string representation of the SurveySession."""
        return f"<SurveySession(id={self.session_id}, type={self.survey_type}, status={self.status})>"
