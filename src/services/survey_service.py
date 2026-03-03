import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import SurveySessionNotFoundError
from src.core.interfaces.survey_strategy import QuestionData
from src.models.enums import SurveyType
from src.models.survey_session import SurveySession
from src.repositories.survey_repository import SurveyRepository
from src.services.survey_config_service import SurveyConfigService
from src.strategies import get_strategy


logger = logging.getLogger(__name__)
class SurveyService:
    """Business Logic Layer for Survey Management.

    Orchestrates the interaction between the Data Layer (Repositories),
    the Logic Layer (Strategies), and the Configuration Layer (ConfigService).

    Attributes:
        repo (SurveyRepository): Data access for sessions.
        config_service (SurveyConfigService): Service to load YAML matrices/logic of the surveys.
        session (AsyncSession): DB session for transaction management.
    """

    def __init__(
        self,
        repo: SurveyRepository,
        config_service: SurveyConfigService,
        session: AsyncSession,
    ) -> None:
        """Initialize the service with dependencies.

        Args:
            repo (SurveyRepository): Data access for sessions.
            config_service (SurveyConfigService): Service to load YAML matrices/logic of the surveys.
            session (AsyncSession): DB session for transaction management.
        """
        self.repo = repo
        self.config_service = config_service
        self.session = session

    async def get_active_session(self, tuid: int) -> SurveySession | None:
        """Retrieve the user's current IN_PROGRESS session, if any.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            SurveySession | None: The active SurveySession object or None.
        """
        return await self.repo.get_active(tuid)

    async def abandon_session(self, session_id: int) -> None:
        """Explicitly mark a specific session as ABANDONED.

        Used when a user decides to start a new one instead of resuming.

        Args:
            session_id (int): The primary key of the session to abandon.
        """
        await self.repo.abandon(session_id)
        await self.session.commit()

    async def abandon_all_waiting_sessions(self, tuid: int) -> int:
        """Abandon all WAITING_FOR_CONFIRMATION sessions for a user.

        Used when a user starts a new test to clean up any stale waiting sessions.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            int: The number of sessions that were abandoned.
        """
        count = await self.repo.abandon_all_waiting(tuid)
        await self.session.commit()
        return count

    async def create_session(self, tuid: int, survey_type: SurveyType, survey_key: str) -> SurveySession:
        """Start a fresh survey session.

        Automatically cleans up any WAITING_FOR_CONFIRMATION sessions before creating a new one.
        The Handler must ensure any IN_PROGRESS session is abandoned first if needed.

        Args:
            tuid (int): Telegram User ID.
            survey_type (SurveyType): The generic type (e.g., ADIZES).
            survey_key (str): The specific config key (e.g., 'adizes_v1').

        Returns:
            SurveySession: The newly created SurveySession.

        Raises:
            ValueError: If an active session still exists (safety guard).
        """
        active = await self.repo.get_active(tuid)
        if active:
            logger.warning(f"User {tuid} already has an active session. Abandon it first.")
            raise ValueError(f"User {tuid} already has an active session. Abandon it first.")

        # Clean up any stale WAITING_FOR_CONFIRMATION sessions
        await self.abandon_all_waiting_sessions(tuid)

        new_session = await self.repo.create(tuid, survey_type, survey_key)
        await self.session.commit()
        return new_session

    async def get_question_data(self, tuid: int) -> QuestionData | None:
        """Get the question data for the user's current step.

        Checks if the user has reached the end of the survey.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            QuestionData | None: If the survey is in progress, returns QuestionData.
            If the survey is finished (current_step >= total_steps), returns None.

        Raises:
            SurveySessionNotFoundError: If no active session exists for the user.
        """
        session = await self.repo.get_active(tuid)
        if not session:
            logger.warning(f"No active session for user {tuid} when getting question data")
            raise SurveySessionNotFoundError(f"No active session for user {tuid}")

        # Load Strategy & Config
        strategy = get_strategy(session.survey_type)
        config = self.config_service.load_config(session.survey_key)

        # Check Completion
        total_steps = strategy.get_total_steps(config)
        if session.current_step >= total_steps:
            return None

        # Get Question
        return strategy.get_question(session.current_step, session.survey_key)

    async def save_answer(self, tuid: int, step: int, answer: Any) -> SurveySession:
        """Validate and save a user's answer.

        1. Validates answer format using the Strategy.
        2. Saves to DB.
        3. Advances step counter.

        Args:
            tuid (int): Telegram User ID.
            step (int): The current question index (0-based).
            answer (Any): The answer payload (e.g., list of ranks).

        Returns:
            SurveySession: The updated SurveySession.

        Raises:
            SurveySessionNotFoundError: If no active session exists.
            ValueError: If the answer format is invalid according to the Strategy.
        """
        session = await self.repo.get_active(tuid)
        if not session:
            logger.warning(f"No active session for user {tuid} when saving answer")
            raise SurveySessionNotFoundError(f"No active session for user {tuid}")

        # Validation
        strategy = get_strategy(session.survey_type)
        if not strategy.validate_answer(step, answer):
            logger.error(f"Invalid answer format for user {tuid}, step {step}")
            raise ValueError(f"Invalid answer format for step {step}")

        # Update State (Safe Copy)
        updated_answers = dict(session.answers)
        updated_answers[str(step)] = answer

        next_step = step + 1

        # Persist
        updated_session = await self.repo.update_progress(
            session_id=session.session_id,
            current_step=next_step,
            answers=updated_answers,
        )
        await self.session.commit()
        return updated_session

    async def get_waiting_for_confirmation(self, tuid: int) -> SurveySession | None:
        """Retrieve a session waiting for confirmation.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            SurveySession | None: The SurveySession with WAITING_FOR_CONFIRMATION status or None.
        """
        from src.models.enums import SurveyStatus

        return await self.repo.get_by_status(tuid, SurveyStatus.WAITING_FOR_CONFIRMATION)

    async def set_waiting_for_confirmation(self, tuid: int) -> SurveySession:
        """Mark the active session as WAITING_FOR_CONFIRMATION.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            SurveySession: The updated SurveySession.

        Raises:
            SurveySessionNotFoundError: If no active session exists.
        """
        session = await self.repo.get_active(tuid)
        if not session:
            logger.warning(f"No active session for user {tuid} when setting waiting for confirmation")
            raise SurveySessionNotFoundError(f"No active session for user {tuid}")

        updated_session = await self.repo.set_waiting_for_confirmation(session.session_id)
        await self.session.commit()
        return updated_session

    async def finish_survey(self, tuid: int) -> SurveySession:
        """Calculate results and mark the survey as COMPLETED.

        Delegates the math to the Strategy, injecting the loaded Configuration.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            SurveySession: The completed SurveySession with results populated.

        Raises:
            SurveySessionNotFoundError: If no active session exists.
        """
        from src.models.enums import SurveyStatus

        # Check for WAITING_FOR_CONFIRMATION first, then fallback to IN_PROGRESS
        session = await self.repo.get_by_status(tuid, SurveyStatus.WAITING_FOR_CONFIRMATION)
        if not session:
            session = await self.repo.get_active(tuid)

        if not session:
            logger.warning(f"No active session for user {tuid} when finishing survey")
            raise SurveySessionNotFoundError(f"No active session for user {tuid}")

        # Load Strategy & Config
        strategy = get_strategy(session.survey_type)
        config = self.config_service.load_config(session.survey_key)

        # Calculate
        results = strategy.calculate_results(session.answers, config)

        # Complete
        completed_session = await self.repo.complete(session.session_id, results)
        await self.session.commit()
        return completed_session
