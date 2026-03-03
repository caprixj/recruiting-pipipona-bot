import logging
from typing import Callable

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from fast_depends import Depends, inject

from src.bot.handlers.testing import _generate_confirmation_message
from src.bot.states import Onboarding, Profile
from src.core.dependencies import get_employee_service, get_survey_service
from src.core.exceptions import EmployeeNotFoundError
from src.services.employee_service import EmployeeService
from src.services.survey_service import SurveyService

router = Router(name="onboarding")

logger = logging.getLogger(__name__)


@router.message(Command("onboard"))
@inject
async def command_onboard(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Trigger the Onboarding FSM explicitly via command.

    Useful if a user gets stuck or wants to update their profile data.

    Args:
        message (Message): The incoming Telegram message.
        state (FSMContext): The FSM Context for state management.
        i18n (Callable[..., str]): The internationalization function.
        emp_service (EmployeeService): The EmployeeService injected by DI.
    """
    if not message.from_user:
        return

    # Register in DB
    await emp_service.register_entry(
        tuid=message.chat.id,
        username=message.from_user.username,
    )

    # Update in DB
    await emp_service.update_profile(
        tuid=message.chat.id,
        username=message.from_user.username,
    )

    await _start_onboarding(message, state, i18n)


@router.callback_query(F.data == "start_onboarding_click")
@inject
async def on_start_onboarding_click(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
) -> None:
    """Trigger the Onboarding FSM when user clicks the 'Start!' button.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
    """
    # Acknowledge callback to stop loading animation
    await callback.answer()

    if isinstance(callback.message, Message):
        # Remove the inline keyboard to prevent double-clicking
        await callback.message.edit_reply_markup(reply_markup=None)
        await _start_onboarding(callback.message, state, i18n)


async def _start_onboarding(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
) -> None:
    """Helper to transition the user into the first step of onboarding.

    Args:
        message (Message): The message context to reply to.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
    """
    await state.set_state(Onboarding.waiting_for_name)
    await message.answer(i18n("onboarding.ask_name"))


@router.message(Onboarding.waiting_for_name)
@inject
async def process_name(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Process the user's name input.

    Validates input and moves the user to the phone number collection step.
    Transitions state to 'waiting_for_phone' and shows the contact request keyboard.

    Args:
        message (Message): The user's input message containing the name.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        emp_service (EmployeeService): Service for employee profile updates.
    """
    if not message.from_user:
        return

    # Ensure employee record exists
    await emp_service.register_entry(
        tuid=message.chat.id,
        username=message.from_user.username,
    )

    text = message.text.strip() if message.text else ""

    await emp_service.update_profile(
        tuid=message.chat.id,
        full_name=text,
    )

    await state.set_state(Onboarding.waiting_for_phone)

    # Phone Request Keyboard
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i18n("onboarding.button.phone"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=i18n("onboarding.button.phone"),
    )

    await message.answer(i18n("onboarding.ask_phone"), reply_markup=kb)


@router.message(Onboarding.waiting_for_phone)
@inject
async def process_phone(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Process the user's phone number input.

    Accepts either a Telegram Contact object (via button) or manual text input.
    Performs anti-spoofing check on Contact objects and moves to the CV link step.

    Args:
        message (Message): The user's input message (or contact).
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        emp_service (EmployeeService): Service for employee profile updates.
    """
    if not message.from_user:
        return

    # Case A: User shared contact via button
    if message.contact:
        # Anti-spoofing: Ensure the contact belongs to the sender
        if message.contact.user_id != message.chat.id:
            await message.answer(i18n("onboarding.error.wrong_contact"))
            return
        phone_number = message.contact.phone_number

    # Case B: User typed it manually
    elif message.text:
        phone_number = message.text

    else:
        await message.answer(i18n("onboarding.error.phone_invalid"))
        return

    # Ensure employee record exists
    await emp_service.register_entry(
        tuid=message.chat.id,
        username=message.from_user.username,
    )

    await emp_service.update_profile(
        tuid=message.chat.id,
        phone=phone_number,
    )

    await state.set_state(Onboarding.waiting_for_cv)

    # Remove the phone keyboard
    await message.answer(i18n("onboarding.ask_cv"), reply_markup=ReplyKeyboardRemove())


@router.message(Onboarding.waiting_for_cv)
@inject
async def process_cv(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
    emp_service: EmployeeService = Depends(get_employee_service),
    survey_service: SurveyService = Depends(get_survey_service),
) -> None:
    """Process the user's CV link and finalize registration.

    Validates the CV link, updates the employee profile, and initiates
    the survey confirmation flow. After saving the profile, checks for
    pending test confirmations and resumes if found.

    Args:
        message (Message): The user's input message containing the link.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        emp_service (EmployeeService): Service for employee profile updates.
        survey_service (SurveyService): Service to handle survey state transitions.
    """
    if not message.from_user:
        return

    text = message.text.strip() if message.text else ""

    await emp_service.update_profile(
        tuid=message.chat.id,
        cv_link=text,
    )

    # Get pending_survey_key before clearing state
    data = await state.get_data()
    pending_survey_key = data.get("pending_survey_key")

    # Check for pending test confirmation
    waiting_session = await survey_service.get_waiting_for_confirmation(message.chat.id)

    if waiting_session:
        # Test pending - resume the confirmation flow
        await state.set_state(Profile.validating)

        # Fetch latest employee data from DB
        try:
            employee = await emp_service.get_employee(message.chat.id)
        except EmployeeNotFoundError as e:
            logger.warning(f"Employee {message.chat.id} not found during onboarding resumption: {e}")
            # Fallback: clear state and show standard message
            await state.clear()
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=i18n("onboarding.button.start_test"),
                            callback_data=f"start_test_click:{pending_survey_key}"
                            if pending_survey_key
                            else "command_test_click",
                        )
                    ]
                ]
            )
            await message.answer(i18n("onboarding.success"), reply_markup=kb)
            return

        # Send resume message and re-send confirmation
        await message.answer(i18n("onboarding.profile_updated_resume"))
        summary_text, kb = _generate_confirmation_message(employee, i18n)
        await message.answer(summary_text, reply_markup=kb)
    else:
        # No pending test - standard flow
        await state.clear()

        # Create keyboard with "Start Test" button
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=i18n("onboarding.button.start_test"),
                        callback_data=f"start_test_click:{pending_survey_key}"
                        if pending_survey_key
                        else "command_test_click",
                    )
                ]
            ]
        )

        await message.answer(i18n("onboarding.success"), reply_markup=kb)
