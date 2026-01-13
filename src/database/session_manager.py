from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.configs.env_settings import Settings


def setup_database(settings: Settings) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initializes the PostgreSQL Async Engine and Session Factory.

    Args:
        settings: The application configuration object.

    Returns:
        A tuple containing the AsyncEngine (for lifecycle management)
        and the async_sessionmaker (for dependency injection).
    """
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

    return engine, session_factory
