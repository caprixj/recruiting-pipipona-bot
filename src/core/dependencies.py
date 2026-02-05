from typing import AsyncGenerator

from fast_depends import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import get_session
from src.repositories.employee_repository import EmployeeRepository
from src.repositories.survey_repository import SurveyRepository
from src.services.employee_service import EmployeeService
from src.services.survey_config_service import SurveyConfigService
from src.services.survey_service import SurveyService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for the SQLAlchemy AsyncSession.

    Yields:
        AsyncSession: An active AsyncSession from the session manager.
    """
    async for session in get_session():
        yield session


async def get_employee_repo(
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeRepository:
    """Dependency provider for the EmployeeRepository.

    Args:
        session (AsyncSession): The injected database session.

    Returns:
        EmployeeRepository: An instance of EmployeeRepository initialized with the session.
    """
    return EmployeeRepository(session)


async def get_survey_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SurveyRepository:
    """Dependency provider for the SurveyRepository.

    Args:
        session (AsyncSession): The injected database session.

    Returns:
        SurveyRepository: An instance of SurveyRepository initialized with the session.
    """
    return SurveyRepository(session)


def get_survey_config_service() -> SurveyConfigService:
    """Dependency provider for SurveyConfigService.

    Returns:
        SurveyConfigService: A new or singleton instance of SurveyConfigService.
    """
    return SurveyConfigService()


async def get_employee_service(
    repo: EmployeeRepository = Depends(get_employee_repo),
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeService:
    """Dependency provider for the EmployeeService.

    Args:
        repo (EmployeeRepository): The employee repository instance.
        session (AsyncSession): The database session.

    Returns:
        EmployeeService: An instance of EmployeeService.

    Note:
        We use it in I18nMiddleware, because FastDepends is not available in the middleware.
        EmployeeService has @inject instead.
    """
    return EmployeeService(repo, session)


async def get_survey_service(
    repo: SurveyRepository = Depends(get_survey_repo),
    config_service: SurveyConfigService = Depends(get_survey_config_service),
    session: AsyncSession = Depends(get_db_session),
) -> SurveyService:
    """Dependency provider for the SurveyService.

    Args:
        repo (SurveyRepository): The survey repository for data access.
        config_service (SurveyConfigService): The service for loading survey configurations.
        session (AsyncSession): The database session for transaction management.

    Returns:
        SurveyService: An instance of SurveyService with all dependencies injected.
    """
    return SurveyService(repo, config_service, session)
