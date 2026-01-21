from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import SurveySessionNotFoundError
from src.models.enums import SurveyStatus, SurveyType
from src.models.survey_session import SurveySession


class SessionRepository:
    """Data Access Layer for SurveySession entities.

    Handles lifecycle management of survey sessions (creation, progress updates, completion).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLAlchemy AsyncSession.
        """
        self.session = session

    async def get_active(self, tuid: int) -> SurveySession | None:
        """Retrieve an active (IN_PROGRESS) session for a specific employee.

        Args:
            tuid: The Employee's Telegram User ID.

        Returns:
            The active SurveySession or None if none exists.
        """
        stmt = select(SurveySession).where(
            SurveySession.employee_id == tuid,
            SurveySession.status == SurveyStatus.IN_PROGRESS,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, tuid: int, survey_type: SurveyType) -> SurveySession:
        """Initialize a new survey session.

        Args:
            tuid: The Employee's Telegram User ID.
            survey_type: The type of survey (e.g., ADIZES).

        Returns:
            The newly created SurveySession instance.
        """
        session_entry = SurveySession(
            employee_id=tuid,
            survey_type=survey_type,
            status=SurveyStatus.IN_PROGRESS,
            current_step=0,
            answers={},
            results={},
        )
        self.session.add(session_entry)
        await self.session.flush()
        return session_entry

    async def update_progress(self, session_id: int, current_step: int, answers: dict) -> SurveySession:
        """Update the current step and answer payload of a session.

        Args:
            session_id: The primary key of the session.
            current_step: The index of the question just answered.
            answers: The complete dictionary of answers collected so far.

        Returns:
            The updated SurveySession.

        Raises:
            SurveySessionNotFoundError: If the session ID does not exist.
        """
        stmt = (
            update(SurveySession)
            .where(SurveySession.session_id == session_id)
            .values(current_step=current_step, answers=answers)
            .returning(SurveySession)
        )
        result = await self.session.execute(stmt)
        session_entry = result.scalar_one_or_none()

        if not session_entry:
            raise SurveySessionNotFoundError(f"Session {session_id} not found")

        return session_entry

    async def complete(self, session_id: int, results: dict) -> SurveySession:
        """Finalize a session by marking it COMPLETED and saving scores.

        Args:
            session_id: The primary key of the session.
            results: The calculated scoring results/categories.

        Returns:
            The completed SurveySession.

        Raises:
            SurveySessionNotFoundError: If the session ID does not exist.
        """
        stmt = (
            update(SurveySession)
            .where(SurveySession.session_id == session_id)
            .values(status=SurveyStatus.COMPLETED, results=results)
            .returning(SurveySession)
        )
        result = await self.session.execute(stmt)
        session_entry = result.scalar_one_or_none()

        if not session_entry:
            raise SurveySessionNotFoundError(f"Session {session_id} not found")

        return session_entry
