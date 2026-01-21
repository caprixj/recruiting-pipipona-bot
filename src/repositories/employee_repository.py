from sqlalchemy import select, update
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
            session: The active SQLAlchemy AsyncSession.
        """
        self.session = session

    async def get(self, tuid: int) -> Employee:
        """Fetch an employee by their Telegram User ID (PK).

        Args:
            tuid: The Telegram User ID.

        Returns:
            The Employee model instance.

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
            tuid: The Telegram User ID.

        Returns:
            The Employee model instance or None if it does not exist.
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
            tuid: The Telegram User ID.
            username: The Telegram username (optional).

        Returns:
            The newly created Employee instance.
        """
        employee = Employee(tuid=tuid, username=username)
        self.session.add(employee)
        await self.session.flush()
        return employee

    async def update(
        self,
        tuid: int,
        full_name: str | None = None,
        phone: str | None = None,
        cv_link: str | None = None,
    ) -> Employee:
        """Update specific profile fields for an employee.

        Args:
            tuid: The Telegram User ID.
            full_name: The candidate's full name.
            phone: The candidate's phone number.
            cv_link: Link to the candidate's CV/Resume.

        Returns:
            The updated Employee instance.

        Raises:
            EmployeeNotFoundError: If the employee does not exist.
        """
        values_to_update = {}
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
