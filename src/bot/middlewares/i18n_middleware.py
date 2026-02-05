from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from fast_depends import Depends, inject

from src.core.dependencies import get_employee_service
from src.services.employee_service import EmployeeService
from src.services.i18n_service import I18nService


@inject
async def fetch_user_language(
    tuid: int,
    service: EmployeeService = Depends(get_employee_service),
) -> str | None:
    """Helper: Uses DI to get the service and fetch language.

    This function is decorated with @inject so FastDepends handles
    the session creation, repository initialization, and cleanup.

    Args:
        tuid (int): Telegram User ID.
        service (EmployeeService): Injected EmployeeService instance.

    Returns:
        str | None: The user's preferred language code or None.
    """
    return await service.get_language(tuid)


class I18nMiddleware(BaseMiddleware):
    """Middleware for handling internationalization.

    Detects the user's preferred language from the database (via Service Layer)
    and injects a localized translator helper into the handler's data.

    Attributes:
        i18n (I18nService): The initialized I18nService instance.
    """

    def __init__(self, i18n_service: I18nService) -> None:
        """Initialize the middleware.

        Args:
            i18n_service (I18nService): The initialized I18nService instance.
        """
        self.i18n = i18n_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Execute the middleware logic.

        1. Identify the user.
        2. Resolve language (DB > Default).
        3. Inject 'i18n' helper into context data.

        Args:
            handler (Callable): The next handler in the chain.
            event (TelegramObject): The incoming Telegram event.
            data (Dict[str, Any]): The context data dictionary.

        Returns:
            Any: The result of the next handler.
        """
        user: User | None = data.get("event_from_user")
        locale = self.i18n.default_locale

        if user:
            # Clean call: The @inject decorator on the helper manages the DB session.
            found_lang = await fetch_user_language(tuid=user.id)
            if found_lang:
                locale = found_lang

        # Inject the helper function
        # Usage in handler: i18n("key", name="John")
        data["i18n"] = lambda key, **kwargs: self.i18n.get(key, locale, **kwargs)
        data["locale_code"] = locale

        return await handler(event, data)
