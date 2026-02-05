import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy import text

from src.bot.handlers import base, onboarding, profile, testing
from src.bot.middlewares.i18n_middleware import I18nMiddleware
from src.configs.env_settings import Settings
from src.configs.logging import setup_logging
from src.database.redis_manager import get_redis_client
from src.database.session_manager import setup_database
from src.services.i18n_service import I18nService


async def main() -> None:
    """Application Entry Point.

    Initializes configuration, logging, database connections (PostgreSQL & Redis),
    internationalization service, and bot dispatcher with all necessary routers.

    Raises:
        SystemExit: If database connection fails during health check.
    """
    # 1. Configuration
    settings = Settings()  # type: ignore
    setup_logging(settings)
    logger = logging.getLogger(__name__)

    logger.info("Starting Recruiting Bot...")

    # 2. Infrastructure (Database)
    # We initialize the engine to prove connectivity.
    engine, session_factory = setup_database(settings)

    # Health Check: Verify DB Connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully.")
    except Exception as e:
        logger.critical(f"Database connection failed: {e}")
        sys.exit(1)

    # 3. Infrastructure (Redis & I18n)
    logger.info("Initializing Redis & I18n...")
    redis = get_redis_client(settings)
    storage = RedisStorage(redis=redis)

    # Load Locales (Assumes run from project root)
    project_root = Path(__file__).resolve().parents[1]
    locales_path = project_root / "data" / "locales"
    i18n_service = I18nService(locales_path, default_locale="ru")

    # 4. Bot & Dispatcher
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    # 5. Middlewares
    dp.update.outer_middleware(I18nMiddleware(i18n_service))

    # 6. Router Registration
    # Order matters: Specific flows first, base/generic last
    dp.include_router(testing.router)  # Survey Logic
    dp.include_router(profile.router)  # Completion/Profile Logic
    dp.include_router(onboarding.router)  # /start and Registration
    dp.include_router(base.router)  # Fallbacks or /help

    # 7. Start Polling
    try:
        # Drop pending updates to prevent processing old messages on restart
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await bot.session.close()
        await engine.dispose()
        await redis.close()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")
