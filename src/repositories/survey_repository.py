import logging
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import SurveySessionNotFoundError
from src.models.enums import SurveyStatus, SurveyType
from src.models.survey_session import SurveySession


logger = logging.getLogger(__name__)
class SurveyRepository:
    """Data Access Layer for SurveySession entities.

    Handles lifecycle management of survey sessions (creation, progress updates, completion).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session (AsyncSession): The active SQLAlchemy AsyncSession.
        """
        self.session = session

    async def get_active(self, tuid: int) -> SurveySession | None:
        """Retrieve an active (IN_PROGRESS) session for a specific employee.

        Args:
            tuid (int): The Employee's Telegram User ID.

        Returns:
            SurveySession | None: The active SurveySession or None if none exists.
        """
        stmt = select(SurveySession).where(
            SurveySession.employee_id == tuid,
            SurveySession.status == SurveyStatus.IN_PROGRESS,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, tuid: int, survey_type: SurveyType, survey_key: str) -> SurveySession:
        """Initialize a new survey session.

        Args:
            tuid (int): The Employee's Telegram User ID.
            survey_type (SurveyType): The type of survey (e.g., ADIZES).
            survey_key (str): The specific config key (e.g., 'adizes_v1').

        Returns:
            SurveySession: The newly created SurveySession instance.
        """
        session_entry = SurveySession(
            employee_id=tuid,
            survey_key=survey_key,
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
            session_id (int): The primary key of the session.
            current_step (int): The index of the question just answered (or next step).
            answers (dict): The complete dictionary of answers collected so far.

        Returns:
            SurveySession: The updated SurveySession.

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
            logger.warning(f"Survey session {session_id} not found during update_progress")
            raise SurveySessionNotFoundError(f"Session {session_id} not found")

        return session_entry

    async def complete(self, session_id: int, results: dict) -> SurveySession:
        """Finalize a session by marking it COMPLETED and saving scores.

        Args:
            session_id (int): The primary key of the session.
            results (dict): The calculated scoring results/categories.

        Returns:
            SurveySession: The completed SurveySession.

        Raises:
            SurveySessionNotFoundError: If the session ID does not exist.
        """
        stmt = (
            update(SurveySession)
            .where(SurveySession.session_id == session_id)
            .values(status=SurveyStatus.COMPLETED, results=results, completed_at=func.now())
            .returning(SurveySession)
        )
        result = await self.session.execute(stmt)
        session_entry = result.scalar_one_or_none()

        if not session_entry:
            logger.warning(f"Survey session {session_id} not found during complete")
            raise SurveySessionNotFoundError(f"Session {session_id} not found")

        return session_entry

    async def abandon(self, session_id: int) -> None:
        """Mark a survey session as ABANDONED.

        Used when a user decides to start over.

        Args:
            session_id (int): The primary key of the session to abandon.
        """
        stmt = update(SurveySession).where(SurveySession.session_id == session_id).values(status=SurveyStatus.ABANDONED)
        await self.session.execute(stmt)

    async def get_by_status(self, tuid: int, status: SurveyStatus) -> SurveySession | None:
        """Retrieve a session with a specific status for a user.

        If multiple sessions exist with the same status, returns the most recent one
        (by created_at timestamp).

        Args:
            tuid (int): The Employee's Telegram User ID.
            status (SurveyStatus): The status to filter by.

        Returns:
            SurveySession | None: The most recent SurveySession with the specified status or None if none exists.
        """
        stmt = (
            select(SurveySession)
            .where(
                SurveySession.employee_id == tuid,
                SurveySession.status == status,
            )
            .order_by(SurveySession.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def abandon_all_waiting(self, tuid: int) -> int:
        """Abandon all WAITING_FOR_CONFIRMATION sessions for a user.

        Used when a user starts a new test to clean up any stale waiting sessions.

        Args:
            tuid (int): The Employee's Telegram User ID.

        Returns:
            int: The number of sessions that were abandoned.
        """
        stmt = (
            update(SurveySession)
            .where(
                SurveySession.employee_id == tuid,
                SurveySession.status == SurveyStatus.WAITING_FOR_CONFIRMATION,
            )
            .values(status=SurveyStatus.ABANDONED)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def set_waiting_for_confirmation(self, session_id: int) -> SurveySession:
        """Mark a session as WAITING_FOR_CONFIRMATION.

        Used when a test is completed and waiting for user confirmation.

        Args:
            session_id (int): The primary key of the session.

        Returns:
            SurveySession: The updated SurveySession.

        Raises:
            SurveySessionNotFoundError: If the session ID does not exist.
        """
        stmt = (
            update(SurveySession)
            .where(SurveySession.session_id == session_id)
            .values(status=SurveyStatus.WAITING_FOR_CONFIRMATION)
            .returning(SurveySession)
        )
        result = await self.session.execute(stmt)
        session_entry = result.scalar_one_or_none()

        if not session_entry:
            logger.warning(f"Survey session {session_id} not found during set_waiting_for_confirmation")
            raise SurveySessionNotFoundError(f"Session {session_id} not found")

        return session_entry