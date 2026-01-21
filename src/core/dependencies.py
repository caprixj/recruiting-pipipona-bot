from typing import AsyncGenerator

from fast_depends import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import get_session
from src.repositories.employee_repository import EmployeeRepository


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for the SQLAlchemy AsyncSession.

    Yields:
        An active AsyncSession from the session manager.
    """
    async for session in get_session():
        yield session


async def get_employee_repo(
    session: AsyncSession = Depends(get_db_session),
) -> EmployeeRepository:
    """Dependency provider for the EmployeeRepository.

    Args:
        session: The injected database session.

    Returns:
        An instance of EmployeeRepository initialized with the session.
    """
    return EmployeeRepository(session)
