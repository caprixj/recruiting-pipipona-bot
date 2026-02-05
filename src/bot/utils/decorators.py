from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

P = ParamSpec("P")
R = TypeVar("R")


def require_message_lock(handler: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Decorator that enforces strict message-level locking for callback handlers.

    This ensures that the `CallbackQuery` originates strictly from the most recent
    bot message recorded in the FSM state. It effectively prevents "Time Travel"
    bugs where users interact with stale buttons left in the chat history.

    The decorator dynamically scans `kwargs` to find the required `CallbackQuery`
    and `FSMContext` objects, making it robust against variable argument naming
    in handlers (e.g., `callback` vs `event`).

    Args:
        handler (Callable[P, Awaitable[R]]): The async handler function to wrap.
            Must accept `CallbackQuery` (by type), `FSMContext` (by type), and
            an `i18n` callable (by keyword 'i18n').

    Returns:
        Callable[P, Awaitable[R]]: The wrapped handler function which includes
        the validation logic. Returns `None` if validation fails to stop execution.

    Raises:
        RuntimeError: If the decorated handler is missing required dependencies
            (`CallbackQuery`, `FSMContext`) in its arguments or if `i18n` is not
            injected via middleware.
    """

    @wraps(handler)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        # 1. Initialization
        event: CallbackQuery | None = None
        state: FSMContext | None = None

        # 2. Search in KWARGS (Dependency Injection)
        for value in kwargs.values():
            if isinstance(value, CallbackQuery):
                event = value
            elif isinstance(value, FSMContext):
                state = value

        # 3. Search in ARGS (Positional Arguments)
        # Aiogram often passes the event (CallbackQuery) as the first positional arg.
        if event is None or state is None:
            for arg in args:
                if event is None and isinstance(arg, CallbackQuery):
                    event = arg
                elif state is None and isinstance(arg, FSMContext):
                    state = arg

                # Stop early if found both
                if event is not None and state is not None:
                    break

        i18n: Callable[..., str] | None = kwargs.get("i18n")

        # 4. Dependency Check (Fail Fast)
        if event is None or state is None or i18n is None:
            found_kwargs = {k: type(v).__name__ for k, v in kwargs.items()}
            found_args = [type(a).__name__ for a in args]
            raise RuntimeError(
                "@require_message_lock failed. Missing dependencies.\n"
                f"Found Kwargs: {found_kwargs}\n"
                f"Found Args: {found_args}\n"
                "Required: `CallbackQuery`, `FSMContext`, and `i18n`."
            )

        # 5. Message Validation
        if not isinstance(event.message, Message):
            await event.answer(i18n("testing.error_old_message"), show_alert=True)
            return None

        # 6. The Lock Logic
        data = await state.get_data()
        valid_msg_id: int | None = data.get("current_msg_id")

        if valid_msg_id is not None and event.message.message_id != valid_msg_id:
            await event.answer(i18n("testing.error_old_message"), show_alert=True)
            return None

        return await handler(*args, **kwargs)

    return wrapper
