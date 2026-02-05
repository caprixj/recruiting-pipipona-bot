from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.employee import Employee
from src.models.enums import SurveyStatus, SurveyType


class SurveySession(Base):
    """Represents a single instance of a test/survey taken by an Employee.

    Attributes:
        session_id (int): Primary key for the survey session.
        employee_id (int): Foreign key to the employee who took the survey.
        survey_key (str): Unique identifier for the survey (e.g., 'adizes_v1').
        survey_type (SurveyType): Methodology type (e.g., ADIZES).
        status (SurveyStatus): Current status of the session (e.g., IN_PROGRESS, COMPLETED).
        current_step (int): The current question index the user is on.
        answers (Dict[str, Any]): Dictionary of answers provided by the user.
        results (Dict[str, Any]): Calculated results after survey completion.
        created_at (datetime): Timestamp when the session was started.
        completed_at (Optional[datetime]): Timestamp when the session was finished.
        employee (Employee): The employee associated with this session.
    """

    __tablename__ = "survey_sessions"

    session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Key
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.tuid"), nullable=False)

    # The Survey
    survey_key: Mapped[str] = mapped_column(String, nullable=False)

    # Meta
    survey_type: Mapped[SurveyType] = mapped_column(SAEnum(SurveyType, native_enum=False), nullable=False)
    status: Mapped[SurveyStatus] = mapped_column(
        SAEnum(SurveyStatus, native_enum=False), default=SurveyStatus.IN_PROGRESS, nullable=False
    )

    # Progress Tracking
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
        """Returns a string representation of the SurveySession.

        Returns:
            str: Representation containing session_id, type, key, and status.
        """
        return (
            f"<SurveySession(id={self.session_id}, type={self.survey_type}, "
            f"key='{self.survey_key}', status={self.status})>"
        )
