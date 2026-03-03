import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.employee import Employee
from src.repositories.employee_repository import EmployeeRepository


logger = logging.getLogger(__name__)
class EmployeeService:
    """Business Logic Layer for Employee Management.

    Orchestrates the lifecycle of candidate profiles, ensuring transactional integrity.
    """

    def __init__(
        self,
        repo: EmployeeRepository,
        session: AsyncSession,
    ) -> None:
        """Initialize the service with dependencies.

        Args:
            repo (EmployeeRepository): The Employee Data Access Object.
            session (AsyncSession): The active database session for transaction management.
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
            tuid (int): Telegram User ID.
            username (str | None): Telegram Username.

        Returns:
            Employee: The existing or newly created Employee entity.
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
        username: str | None = None,
        full_name: str | None = None,
        phone: str | None = None,
        cv_link: str | None = None,
    ) -> Employee:
        """Update candidate profile fields and commit changes.

        Args:
            tuid (int): Telegram User ID.
            username (str | None): Telegram Username.
            full_name (str | None): Candidate's full name.
            phone (str | None): Candidate's phone number.
            cv_link (str | None): Link to the candidate's CV.

        Returns:
            Employee: The updated Employee entity.

        Raises:
            EmployeeNotFoundError: If the employee does not exist.
        """
        updated_employee = await self.repo.update(
            tuid, username=username, full_name=full_name, phone=phone, cv_link=cv_link
        )
        await self.session.commit()
        return updated_employee

    async def get_employee(self, tuid: int) -> Employee:
        """Retrieve an employee strictly, raising an error if missing.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            Employee: The Employee entity.

        Raises:
            EmployeeNotFoundError: If the employee does not exist.
        """
        return await self.repo.get(tuid)

    async def get_language(self, tuid: int) -> str | None:
        """Retrieve the preferred language for an employee.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            str | None: The language code (e.g., 'ru', 'en') or None if unknown.
        """
        return await self.repo.get_language(tuid)

    async def employee_exists(self, tuid: int) -> bool:
        """Check if an employee exists.

        Args:
            tuid (int): Telegram User ID.

        Returns:
            bool: True if the employee exists, False otherwise.
        """
        return await self.repo.exists(tuid)