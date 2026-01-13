import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import text

from src.bot.handlers import base
from src.configs.env_settings import Settings
from src.configs.logging import setup_logging
from src.database.session_manager import setup_database


async def main() -> None:
    """Application Entry Point."""
    # 1. Configuration
    settings = Settings()  # type: ignore
    setup_logging(settings)
    logger = logging.getLogger(__name__)

    logger.info("Starting Recruiting Bot...")

    # 2. Infrastructure (Database)
    # We initialize the engine to prove connectivity, even without tables.
    engine, session_factory = setup_database(settings)

    # Health Check: Verify DB Connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully.")
    except Exception as e:
        logger.critical(f"Database connection failed: {e}")
        sys.exit(1)

    # 3. Bot & Dispatcher
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # 4. Router Registration
    dp.include_router(base.router)

    # 5. Start Polling
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await bot.session.close()
        await engine.dispose()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")
