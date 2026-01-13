from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="base_router")


@router.message(CommandStart())
async def start(message: Message) -> None:
    """Handles the /start command.

    Acts as a heartbeat check to confirm the bot is responsive.
    """
    await message.answer("<b>System Online.</b>\nRecruiting Bot is running.")
