import logging
from typing import Callable, List

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fast_depends import Depends, inject

from src.bot.filters.input_type import InputTypeFilter
from src.bot.keyboards.survey_kb import build_resume_keyboard
from src.bot.keyboards.survey_kb import build_survey_keyboard as build_ranking_keyboard
from src.bot.states import Profile, Testing
from src.bot.utils.decorators import require_message_lock
from src.core.dependencies import get_employee_service, get_survey_service
from src.core.exceptions import EmployeeNotFoundError, SurveySessionNotFoundError
from src.models.employee import Employee
from src.models.enums import InputType, SurveyType
from src.models.survey_session import SurveySession
from src.services.employee_service import EmployeeService
from src.services.survey_service import SurveyService

router = Router(name="testing")

logger = logging.getLogger(__name__)

# Router-level filter: These handlers must only work in private chats
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
@inject
async def command_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Handle /start with optional deep link args (e.g., /start adizes_v1).

    Args:
        message (Message): The incoming Telegram message.
        command (CommandObject): Command arguments and metadata.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
        emp_service (EmployeeService): Injected employee service.
    """
    # 1. Register/Update User record (idempotent)
    employee = await emp_service.register_entry(
        tuid=message.chat.id,
        username=message.from_user.username,
    )

    requested_survey_key = command.args
    active_session = await survey_service.get_active_session(message.chat.id)

    # 2. Check for Active Session first
    if active_session:
        if requested_survey_key and active_session.survey_key != requested_survey_key:
            # Conflict: Deep link for a different test
            # Pass the requested_survey_key so the restart button uses it
            await message.answer(
                i18n("testing.session_conflict"),
                reply_markup=build_resume_keyboard(i18n, survey_key=requested_survey_key),
            )
        else:
            # Generic /start or matching deep link -> Resume
            await _send_current_question(message, state, i18n, survey_service, emp_service)
        return

    # 3. No active session -> Check if Registration is complete
    is_registered = employee.full_name and employee.phone
    if not is_registered:
        # Not registered -> Force onboarding (save deep link for later if needed)
        if requested_survey_key:
            await state.update_data(pending_survey_key=requested_survey_key)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=i18n("onboarding.button.start"),
                        callback_data="start_onboarding_click",
                    )
                ]
            ]
        )
        await message.answer(i18n("onboarding.start_msg"), reply_markup=kb)
        return

    # 4. Registered but no active session -> Handle deep link or generic start
    if requested_survey_key:
        await _start_new_test_flow(message, state, i18n, survey_service, emp_service, requested_survey_key)
    else:
        # Show standard welcome for returning registered users
        await message.answer(i18n("onboarding.welcome_back"))


@router.message(Command("test"))
@inject
async def command_test(
    message: Message,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
) -> None:
    """Handle explicit /test command.

    Args:
        message (Message): The incoming Telegram message.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
    """
    active_session = await survey_service.get_active_session(message.chat.id)

    if active_session:
        # Use the active session's survey_key for the restart button
        await message.answer(
            i18n("testing.session_active"),
            reply_markup=build_resume_keyboard(i18n, survey_key=active_session.survey_key),
        )
    else:
        # No active session -> Inform user that they need an invitation link
        await message.answer(i18n("testing.no_active_session"))


@router.callback_query(F.data.startswith("start_test_click:"))
@router.callback_query(F.data == "command_test_click")
@inject
async def on_start_test_click(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Handle click on 'Start Test' button from onboarding success.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
        emp_service (EmployeeService): Injected employee service.
    """
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    # TODO: Move to UserRegistrationMiddleware
    # Ensure employee record exists (Safety check for IntegrityError)
    await emp_service.register_entry(
        tuid=callback.from_user.id,
        username=callback.from_user.username,
    )

    # Remove the button to prevent double-clicking
    await callback.message.edit_reply_markup(reply_markup=None)

    if callback.data == "command_test_click":
        # Act like /test command
        await command_test(callback.message, i18n, survey_service)
    else:
        # Start specific test from deep link
        survey_key = callback.data.split(":")[1]
        await _start_new_test_flow(callback.message, state, i18n, survey_service, emp_service, survey_key)


@router.callback_query(F.data.startswith("test_restart"))
@inject
async def on_test_restart(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Handle the 'Start New' button click, abandoning any active session.

    User chose to abandon the old test and start over.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
        emp_service (EmployeeService): Injected employee service.
    """
    await callback.answer()
    if not callback.message:
        return

    # Remove inline keyboard immediately to avoid double-clicking
    await callback.message.edit_reply_markup(reply_markup=None)

    # TODO: Move to UserRegistrationMiddleware
    # Ensure employee record exists
    await emp_service.register_entry(
        tuid=callback.from_user.id,
        username=callback.from_user.username,
    )

    active = await survey_service.get_active_session(callback.from_user.id)
    if active:
        await survey_service.abandon_session(active.session_id)

    # Clean up any stale WAITING_FOR_CONFIRMATION sessions
    await survey_service.abandon_all_waiting_sessions(callback.from_user.id)

    # Extract survey_key from callback data
    # Format: "test_restart" (old) or "test_restart:{survey_key}" (new)
    if callback.data == "test_restart":
        # Backward compatibility: fallback to default
        survey_key = "adizes_v1"
    else:
        # Extract from "test_restart:{survey_key}"
        parts = callback.data.split(":", 1)
        survey_key = parts[1] if len(parts) > 1 else "adizes_v1"

    await _start_new_test_flow(callback.message, state, i18n, survey_service, emp_service, survey_key=survey_key)


@router.callback_query(F.data == "test_resume")
@inject
async def on_test_resume(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Handle the 'Continue' button click, resuming the active session.

    User chose to continue their existing test.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
        emp_service (EmployeeService): Injected employee service.
    """
    await callback.answer()
    if not callback.message:
        return

    # Remove inline keyboard immediately to avoid double-clicking
    await callback.message.edit_reply_markup(reply_markup=None)

    # TODO: Move to UserRegistrationMiddleware
    # Ensure employee record exists
    await emp_service.register_entry(
        tuid=callback.from_user.id,
        username=callback.from_user.username,
    )

    await _send_current_question(callback.message, state, i18n, survey_service, emp_service)


# --- POLYMORPHIC HANDLERS ---


@router.callback_query(
    Testing.in_progress,
    InputTypeFilter(InputType.RANKING),
    F.data.startswith("survey_option:"),
)
@require_message_lock
@inject
async def handle_ranking_click(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
) -> None:
    """Handle click on an option button in a ranking question.

    Updates the user's selection buffer in FSM state and refreshes the keyboard.
    Handler specific for RANKING questions (Append to buffer).

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
    """
    # Validate session and extract option
    result = await _validate_survey_option_callback(callback, survey_service, i18n)
    if result is None:
        return

    current_session, option = result

    # Read Cache (No DB)
    data = await state.get_data()
    options: List[str] = data.get("options", [])
    selection: List[str] = data.get("selection", [])

    if option not in selection:
        selection.append(option)
    else:
        # Already selected -> Ignore (or we could remove it, but task says "ignore clicks on already selected ones")
        await callback.answer()
        return

    await state.update_data(selection=selection)

    # Update UI
    kb = build_ranking_keyboard(options, selection, i18n, current_session.session_id)
    await callback.message.edit_reply_markup(reply_markup=kb)  # type: ignore
    await callback.answer()


@router.callback_query(Testing.in_progress, F.data.startswith("survey_reset:"))
@require_message_lock
@inject
async def on_survey_reset(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
) -> None:
    """Handle the 'Reset' button click, clearing the selection buffer.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
    """
    # Validate session
    current_session = await _validate_survey_control_callback(callback, survey_service, i18n)
    if current_session is None:
        return

    # Check if there is anything to reset
    data = await state.get_data()
    selection = data.get("selection", [])

    if not selection:
        # Already empty -> Just answer callback to stop animation
        await callback.answer()
        return

    await state.update_data(selection=[])

    # Read cached options
    data = await state.get_data()
    options = data.get("options", [])

    kb = build_ranking_keyboard(options, [], i18n, current_session.session_id)
    await callback.message.edit_reply_markup(reply_markup=kb)  # type: ignore
    await callback.answer(i18n("testing.btn_reset"))


@router.callback_query(Testing.in_progress, F.data.startswith("survey_next:"))
@require_message_lock
@inject
async def on_survey_next(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Submit selection for Ranking.

    Validates that the selection is complete before proceeding to the next step.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
        emp_service (EmployeeService): Injected employee service.
    """
    # Validate session
    current_session = await _validate_survey_control_callback(callback, survey_service, i18n)
    if current_session is None:
        return

    data = await state.get_data()
    selection: List[str] = data.get("selection", [])
    options: List[str] = data.get("options", [])

    # Validation
    if len(selection) < len(options):
        await callback.answer(i18n("testing.error_format"), show_alert=True)
        return

    await _submit_answer_and_next(callback, state, i18n, survey_service, emp_service, answer=selection)


async def _start_new_test_flow(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService,
    emp_service: EmployeeService,
    survey_key: str,
) -> None:
    """Initialize a new session and render the first question.

    Args:
        message (Message): The Telegram message to respond to.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): The survey service instance.
        emp_service (EmployeeService): The employee service instance.
        survey_key (str): The unique key of the survey to start.
    """
    if not survey_key:
        await message.answer(i18n("testing.no_survey_key"))
        return

    try:
        await survey_service.create_session(
            tuid=message.chat.id,
            survey_type=SurveyType.ADIZES,
            survey_key=survey_key,
        )
        await _send_current_question(message, state, i18n, survey_service, emp_service)
    except ValueError as e:
        logger.warning(f"Session conflict for user {message.chat.id}: {e}")
        await message.answer(i18n("testing.error_session_conflict"))


async def _submit_answer_and_next(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService,
    emp_service: EmployeeService,
    answer: str | List[str],
) -> None:
    """Common logic to save answer, freeze UI, and load next question.

    Handles session expiration and survey transition logic.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): The survey service instance.
        emp_service (EmployeeService): The employee service instance.
        answer (str | List[str]): The answer payload to save.
    """
    if not callback.message:
        return

    session = await survey_service.get_active_session(callback.from_user.id)  # type: ignore

    # Dead End Handling
    if not session:
        await callback.answer(i18n("testing.session_expired"), show_alert=True)
        # Visually disable the dead UI
        original_text = callback.message.html_text or ""
        await callback.message.edit_text(text=f"{original_text}\n\n❌ (Session Expired)", reply_markup=None)
        return

    try:
        await survey_service.save_answer(
            tuid=callback.from_user.id,
            step=session.current_step,
            answer=answer,
        )
    except ValueError as e:
        logger.error(f"Invalid answer for user {callback.from_user.id}: {e}")
        await callback.answer(f"Error: {e}", show_alert=True)
        return

    # Freeze UI
    display_text = " > ".join(answer) if isinstance(answer, list) else str(answer)
    original_text = callback.message.html_text or ""
    # Remove the prompt (italics) from the frozen message
    clean_text = original_text.split("\n\n<i>")[0]

    await callback.message.edit_text(text=f"{clean_text}\n\n✅ {display_text}", reply_markup=None)

    # Next
    await _send_current_question(callback.message, state, i18n, survey_service, emp_service)
    await callback.answer()


async def _send_current_question(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService,
    emp_service: EmployeeService,
) -> None:
    """Fetch step data, cache it in FSM, and render UI.

    Args:
        message (Message): The message context to respond to.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): The survey service instance.
        emp_service (EmployeeService): The employee service instance.
    """
    try:
        # 1. Get Data from DB (returns None if finished)
        session = await survey_service.get_active_session(message.chat.id)
        if not session:
            raise SurveySessionNotFoundError(f"No active session for user {message.chat.id}")

        q_data = await survey_service.get_question_data(message.chat.id)
    except SurveySessionNotFoundError as e:
        logger.warning(f"Session not found for user {message.chat.id}: {e}")
        # Should not happen in normal flow, but good for safety
        if message.reply_markup:
            await message.edit_reply_markup(reply_markup=None)
        await message.answer(i18n("testing.session_expired"))
        return

    # 2. Check Completion
    if q_data is None:
        await _handle_test_completion(message, state, i18n, emp_service, survey_service)
        return

    # 3. Cache Metadata to FSM (The "Cached Step Pattern")
    await state.set_state(Testing.in_progress)
    await state.update_data(
        step_id=q_data.id,
        input_type=q_data.input_type,
        options=q_data.options,
        selection=[],
    )

    # 4. Render
    header = i18n("testing.question_header", n=q_data.id)
    text = i18n(q_data.text_key)

    # Dynamically generate options text
    options_lines = []
    for opt in q_data.options:
        opt_text = i18n(f"surveys.{session.survey_key}.q{q_data.id}_opt.{opt}")
        options_lines.append(f"<b>{opt})</b> {opt_text}")
    options_block = "\n".join(options_lines)

    prompt = i18n(f"testing.prompt_{q_data.input_type.value.lower()}")
    full_text = f"<b>{header}</b>\n\n{text}\n\n{options_block}\n\n<i>{prompt}</i>"

    # Select Keyboard Strategy based on InputType
    if q_data.input_type == InputType.RANKING:
        kb = build_ranking_keyboard(q_data.options, [], i18n, session.session_id)
    else:
        # Fallback for Single Choice: Simple vertical list
        builder = InlineKeyboardBuilder()
        for opt in q_data.options:
            builder.button(text=opt, callback_data=f"survey_option:{session.session_id}:{opt}")
        builder.adjust(1)
        kb = builder.as_markup()

    # Send message and capture its ID for message locking
    msg = await message.answer(full_text, reply_markup=kb)
    await state.update_data(current_msg_id=msg.message_id)


async def _validate_survey_control_callback(
    callback: CallbackQuery,
    survey_service: SurveyService,
    i18n: Callable[..., str],
) -> SurveySession | None:
    """Validate session_id from survey control button callbacks (reset/next).

    Args:
        callback (CallbackQuery): The callback query object.
        survey_service (SurveyService): SurveyService instance to fetch active session.
        i18n (Callable[..., str]): Internationalization function.

    Returns:
        SurveySession | None: The active SurveySession if valid, None otherwise.
    """
    if not callback.message:
        return None

    # Extract session_id from callback data: "survey_reset:{session_id}" or "survey_next:{session_id}"
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer(i18n("testing.session_no_longer_active"), show_alert=True)
        return None

    try:
        callback_session_id = int(parts[1])
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid callback data format '{callback.data}': {e}")
        await callback.answer(i18n("testing.session_no_longer_active"), show_alert=True)
        return None

    # Guard Clause: Validate session_id against database
    current_session = await survey_service.get_active_session(callback.from_user.id)  # type: ignore
    if current_session is None or current_session.session_id != callback_session_id:
        await callback.answer(i18n("testing.session_no_longer_active"), show_alert=True)
        # Remove the keyboard from the old message
        await callback.message.edit_reply_markup(reply_markup=None)
        return None

    return current_session


async def _validate_survey_option_callback(
    callback: CallbackQuery,
    survey_service: SurveyService,
    i18n: Callable[..., str],
) -> tuple[SurveySession, str] | None:
    """Validate session_id from survey option button callbacks and extract option.

    Args:
        callback (CallbackQuery): The callback query object.
        survey_service (SurveyService): SurveyService instance to fetch active session.
        i18n (Callable[..., str]): Internationalization function.

    Returns:
        tuple[SurveySession, str] | None: Tuple of (current_session, option) if valid, None if validation fails.
    """
    if not callback.message:
        return None

    # Extract session_id and option from callback data: "survey_option:{session_id}:{opt}"
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer(i18n("testing.session_no_longer_active"), show_alert=True)
        return None

    try:
        callback_session_id = int(parts[1])
        option = parts[2]
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid callback data format '{callback.data}': {e}")
        await callback.answer(i18n("testing.session_no_longer_active"), show_alert=True)
        return None

    # Guard Clause: Validate session_id against database
    current_session = await survey_service.get_active_session(callback.from_user.id)  # type: ignore
    if current_session is None or current_session.session_id != callback_session_id:
        await callback.answer(i18n("testing.session_no_longer_active"), show_alert=True)
        # Remove the keyboard from the old message
        await callback.message.edit_reply_markup(reply_markup=None)
        return None

    return current_session, option


def _generate_confirmation_message(
    employee: Employee,
    i18n: Callable[..., str],
) -> tuple[str, InlineKeyboardMarkup]:
    """Generate the confirmation message and keyboard from employee data.

    Args:
        employee (Employee): The Employee model instance.
        i18n (Callable[..., str]): The internationalization function.

    Returns:
        tuple[str, InlineKeyboardMarkup]: Tuple of (summary_text, keyboard).
    """
    # Format employee data (handle None values)
    full_name = employee.full_name if employee.full_name else i18n("testing.not_specified")
    phone = employee.phone if employee.phone else i18n("testing.not_specified")
    cv_link = employee.cv_link if employee.cv_link else i18n("testing.not_specified")

    # Build the summary message using i18n
    summary_text = i18n(
        "testing.completion_summary",
        full_name=full_name,
        phone=phone,
        cv_link=cv_link,
    )

    # Create confirmation button
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Confirm & Submit", callback_data="profile_confirm")]]
    )
    return summary_text, kb


async def _handle_test_completion(
    message: Message,
    state: FSMContext,
    i18n: Callable[..., str],
    emp_service: EmployeeService,
    survey_service: SurveyService,
) -> None:
    """Transition to Profile Validation with employee data summary.

    Args:
        message (Message): The message context to reply to.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        emp_service (EmployeeService): The employee service instance.
        survey_service (SurveyService): The survey service instance.
    """
    # Fetch employee profile
    try:
        employee = await emp_service.get_employee(message.chat.id)
    except EmployeeNotFoundError:
        # Fallback if employee not found (shouldn't happen, but safety first)
        await message.answer(i18n("testing.finished"))
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="✅ Confirm & Submit", callback_data="profile_confirm")]]
        )
        await message.answer("Please confirm your profile.", reply_markup=kb)
        return

    # Set status to WAITING_FOR_CONFIRMATION
    try:
        await survey_service.set_waiting_for_confirmation(message.chat.id)
    except SurveySessionNotFoundError:
        # If no session found, we can't proceed
        await message.answer(i18n("testing.session_expired"))
        return

    # Generate and send confirmation message
    summary_text, kb = _generate_confirmation_message(employee, i18n)
    await message.answer(summary_text, reply_markup=kb)

    # Set FSM state for context (but handler is now stateless)
    await state.set_state(Profile.validating)
