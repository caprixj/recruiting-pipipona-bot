from fast_depends import Depends, inject
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db_session, get_employee_repo
from src.models.employee import Employee
from src.repositories.employee_repository import EmployeeRepository


class EmployeeService:
    """Business Logic Layer for Employee Management.

    Orchestrates the lifecycle of candidate profiles, ensuring transactional integrity.
    """

    @inject
    def __init__(
        self,
        repo: EmployeeRepository = Depends(get_employee_repo),
        session: AsyncSession = Depends(get_db_session),
    ) -> None:
        """Initialize the service with dependencies.

        Args:
            repo: The Employee Data Access Object.
            session: The active database session for transaction management.
        """
        self.repo = repo
        self.session = session

    async def register_entry(self, tuid: int, username: str | None) -> Employee:
        """Handle the entry point for a user (e.g., /start command).

        Idempotent operation:
        1. Checks if the employee exists.
        2. If not, creates a new record.
        3. Commits the transaction.

        Args:
            tuid: Telegram User ID.
            username: Telegram Username.

        Returns:
            The existing or newly created Employee entity.
        """
        existing_employee = await self.repo.find(tuid)
        if existing_employee:
            return existing_employee

        new_employee = await self.repo.add(tuid, username)
        await self.session.commit()
        return new_employee

    async def update_profile(
        self,
        tuid: int,
        full_name: str | None = None,
        phone: str | None = None,
        cv_link: str | None = None,
    ) -> Employee:
        """Update candidate profile fields and commit changes.

        Args:
            tuid: Telegram User ID.
            full_name: Candidate's full name.
            phone: Candidate's phone number.
            cv_link: Link to the candidate's CV.

        Returns:
            The updated Employee entity.

        Raises:
            EmployeeNotFoundError: If the employee does not exist.
        """
        # The repo.update method handles the lookup and flushing.
        updated_employee = await self.repo.update(tuid, full_name=full_name, phone=phone, cv_link=cv_link)
        await self.session.commit()
        return updated_employee

    async def get_employee(self, tuid: int) -> Employee:
        """Retrieve an employee strictly, raising an error if missing.

        Args:
            tuid: Telegram User ID.

        Returns:
            The Employee entity.

        Raises:
            EmployeeNotFoundError: If the employee does not exist.
        """
        return await self.repo.get(tuid)
