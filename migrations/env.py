import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Must import all models here so Alembic can "see" them
from src.models.employee import Employee  # noqa: F401
from src.models.survey_session import SurveySession  # noqa: F401

# 1. Import Project Settings & Models
# We add the root path to sys.path if necessary, but poetry usually handles it.
from src.configs.env_settings import Settings
from src.models.base import Base

# 2. Configuration
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Target Metadata
# This tells Alembic what the "Target" schema looks like
target_metadata = Base.metadata

# 4. Load DB URL from Pydantic Settings
settings = Settings()  # type: ignore
config.set_main_option("sqlalchemy.url", settings.DB_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Executes the migration context using a synchronous connection.

    Acts as the bridge between the AsyncEngine and Alembic's synchronous core,
    ensuring the migration transaction is handled correctly.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
