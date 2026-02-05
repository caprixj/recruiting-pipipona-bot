from sqlalchemy import select, update, exists
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import EmployeeNotFoundError
from src.models.employee import Employee


class EmployeeRepository:
    """Data Access Layer for Employee entities.

    Handles CRUD operations for the 'employees' table.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session (AsyncSession): The active SQLAlchemy AsyncSession.
        """
        self.session = session

    async def get(self, tuid: int) -> Employee:
        """Fetch an employee by their Telegram User ID (PK).

        Args:
            tuid (int): The Telegram User ID.

        Returns:
            Employee: The Employee model instance.

        Raises:
            EmployeeNotFoundError: If the employee does not exist.
        """
        stmt = select(Employee).where(Employee.tuid == tuid)
        result = await self.session.execute(stmt)
        employee = result.scalar_one_or_none()

        if not employee:
            raise EmployeeNotFoundError(f"Employee {tuid} not found")

        return employee

    async def find(self, tuid: int) -> Employee | None:
        """Fetch an employee by their Telegram User ID (PK).

        Args:
            tuid (int): The Telegram User ID.

        Returns:
            Employee | None: The Employee model instance or None if it does not exist.
        """
        stmt = select(Employee).where(Employee.tuid == tuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, tuid: int, username: str | None) -> Employee:
        """Create a new employee record.

        Note:
            This method flushes the object to generating primary keys/defaults
            but does not commit the transaction. The Service layer is responsible
            for committing.

        Args:
            tuid (int): The Telegram User ID.
            username (str | None): The Telegram username (optional).

        Returns:
            Employee: The newly created Employee instance.
        """
        employee = Employee(tuid=tuid, username=username)
        self.session.add(employee)
        await self.session.flush()
        return employee

    async def update(
        self,
        tuid: int,
        username: str | None = None,
        full_name: str | None = None,
        phone: str | None = None,
        cv_link: str | None = None,
    ) -> Employee:
        """Update specific profile fields for an employee.

        Args:
            tuid (int): The Telegram User ID.
            username (str | None): Telegram Username.
            full_name (str | None): The candidate's full name.
            phone (str | None): The candidate's phone number.
            cv_link (str | None): Link to the candidate's CV/Resume.

        Returns:
            Employee: The updated Employee instance.

        Raises:
            EmployeeNotFoundError: If the employee does not exist.
        """
        values_to_update = {}
        if username is not None:
            values_to_update["username"] = username
        if full_name is not None:
            values_to_update["full_name"] = full_name
        if phone is not None:
            values_to_update["phone"] = phone
        if cv_link is not None:
            values_to_update["cv_link"] = cv_link

        if not values_to_update:
            return await self.get(tuid)

        stmt = update(Employee).where(Employee.tuid == tuid).values(**values_to_update).returning(Employee)

        result = await self.session.execute(stmt)
        employee = result.scalar_one_or_none()

        if not employee:
            raise EmployeeNotFoundError(f"Employee {tuid} not found")

        return employee

    async def get_language(self, tuid: int) -> str | None:
        """Fetch the preferred language code for an employee.

        Args:
            tuid (int): The Telegram User ID.

        Returns:
            str | None: The language code (e.g., 'ru', 'en') or None if user not found.
        """
        stmt = select(Employee.language_code).where(Employee.tuid == tuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, tuid: int) -> bool:
        """Check if an employee exists by their Telegram User ID.

        Args:
            tuid (int): The Telegram User ID.

        Returns:
            bool: True if the employee exists, False otherwise.
        """
        stmt = select(exists().where(Employee.tuid == tuid))
        result = await self.session.execute(stmt)
        return result.scalar_one() is True
