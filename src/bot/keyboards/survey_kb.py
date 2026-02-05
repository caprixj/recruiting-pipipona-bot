from typing import Callable, List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_resume_keyboard(i18n: Callable[..., str], survey_key: str | None = None) -> InlineKeyboardMarkup:
    """Keyboard asking user to Resume or Start New.

    Args:
        i18n (Callable[..., str]): Function to translate button labels.
        survey_key (str | None): Optional survey key to include in the restart callback data.
                    If None, uses the old format for backward compatibility.

    Returns:
        InlineKeyboardMarkup: InlineKeyboardMarkup with localized 'Continue' and 'Start New' buttons.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n("testing.btn_continue"), callback_data="test_resume")
    
    # Include survey_key in callback data if provided
    if survey_key:
        restart_callback = f"test_restart:{survey_key}"
    else:
        restart_callback = "test_restart"
    
    builder.button(text=i18n("testing.btn_start_new"), callback_data=restart_callback)
    builder.adjust(2)
    return builder.as_markup()


def build_survey_keyboard(
    options: List[str], selected: List[str], i18n: Callable[..., str], session_id: int
) -> InlineKeyboardMarkup:
    """Dynamic keyboard for ranking questions (Adizes Style).

    Logic:
    1. Show all options (A, B, C, D).
    2. If an option is selected, show its rank: "A (1)".
    3. Show 'Reset' button at all times.
    4. Show 'Next' button only when all 4 are selected.

    Args:
        options (List[str]): Full list of options available for the question.
        selected (List[str]): List of options currently in the user's buffer.
        i18n (Callable[..., str]): Function to translate button labels.
        session_id (int): The session ID to embed in callback data for validation.

    Returns:
        InlineKeyboardMarkup: The constructed InlineKeyboardMarkup.
    """
    builder = InlineKeyboardBuilder()

    # 1. Option buttons
    for opt in options:
        text = opt
        if opt in selected:
            rank = selected.index(opt) + 1
            text = f"{opt} ({rank})"
        builder.button(text=text, callback_data=f"survey_option:{session_id}:{opt}")

    # Layout options in one row (A B C D)
    builder.adjust(len(options))

    # 2. Control buttons
    controls = InlineKeyboardBuilder()
    controls.button(text=i18n("testing.btn_reset"), callback_data=f"survey_reset:{session_id}")

    if len(selected) == len(options):
        controls.button(text=i18n("testing.btn_next"), callback_data=f"survey_next:{session_id}")

    # Combine
    builder.attach(controls)

    return builder.as_markup()
