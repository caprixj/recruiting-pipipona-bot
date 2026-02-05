from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.configs.env_settings import Settings

# Global reference to the session factory.
# Populated by setup_database() at runtime.
_session_maker: async_sessionmaker[AsyncSession] | None = None


def setup_database(
    settings: Settings,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initialize the PostgreSQL Async Engine and Session Factory.

    Args:
        settings (Settings): The application configuration object.

    Returns:
        tuple[AsyncEngine, async_sessionmaker[AsyncSession]]: A tuple containing the AsyncEngine and the async_sessionmaker.
    """
    global _session_maker

    engine = create_async_engine(
        settings.DB_URL,
        echo=(settings.LOG_LEVEL == "DEBUG"),
        future=True,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Mandatory for asyncio
        autoflush=False,
    )

    # Store in global variable for DI access
    _session_maker = session_factory

    return engine, session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency Generator that yields a database session.

    Yields:
        AsyncSession: An active AsyncSession.

    Raises:
        RuntimeError: If setup_database() has not been called yet.
    """
    global _session_maker

    if _session_maker is None:
        raise RuntimeError("Database not initialized. Call setup_database() first.")

    async with _session_maker() as session:
        yield session
