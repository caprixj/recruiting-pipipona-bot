from typing import Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from fast_depends import Depends, inject

from src.core.dependencies import get_employee_service, get_survey_service
from src.services.employee_service import EmployeeService
from src.services.survey_service import SurveyService

router = Router(name="profile")

# Router-level filter: private chats only
router.message.filter(F.chat.type == "private")


@router.callback_query(F.data == "profile_confirm")
@inject
async def on_profile_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: Callable[..., str],
    survey_service: SurveyService = Depends(get_survey_service),
    emp_service: EmployeeService = Depends(get_employee_service),
) -> None:
    """Handle final profile confirmation.

    Stateless handler: checks database for WAITING_FOR_CONFIRMATION status
    and fetches latest profile data from DB at confirmation time.

    Args:
        callback (CallbackQuery): The button click event.
        state (FSMContext): The FSM Context.
        i18n (Callable[..., str]): The internationalization function.
        survey_service (SurveyService): Injected survey service.
        emp_service (EmployeeService): Injected employee service.
    """
    if not callback.message:
        return

    # Check for session waiting for confirmation
    waiting_session = await survey_service.get_waiting_for_confirmation(callback.from_user.id)
    if not waiting_session:
        await callback.answer(i18n("profile.no_active_test"), show_alert=True)
        return

    # Verify employee exists before proceeding
    if not await emp_service.employee_exists(callback.from_user.id):
        await callback.answer(i18n("profile.profile_not_found"), show_alert=True)
        return

    try:
        # 1. Finalize Survey (Calculate results, save to DB)
        await survey_service.finish_survey(callback.from_user.id)

        # 2. Show Success Message
        await callback.message.edit_text(text=i18n("profile.completed"), reply_markup=None)

    except ValueError as e:
        # Business logic errors (e.g., session already finished, incomplete data)
        await callback.answer(i18n("profile.error_value", error=str(e)), show_alert=True)
        return
    except Exception as e:
        await callback.answer(i18n("profile.error_generic", error=str(e)), show_alert=True)
        return

    # 3. Clear State (Session is over)
    await state.clear()
    await callback.answer()
    # Ensure any remaining UI state is reset
    await state.set_data({})
