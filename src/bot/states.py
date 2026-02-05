from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    """FSM States for the candidate registration process.

    Attributes:
        waiting_for_name (State): User is expected to provide their full name.
        waiting_for_phone (State): User is expected to provide their phone number.
        waiting_for_cv (State): User is expected to provide a link to their CV.
    """

    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_cv = State()


class Testing(StatesGroup):
    """FSM States for the survey process.

    Attributes:
        in_progress (State): User is currently answering questions.
    """

    in_progress = State()  # User is currently answering questions


class Profile(StatesGroup):
    """FSM States for profile management and validation.

    Attributes:
        validating (State): User finished test, reviewing profile before submission.
    """

    validating = State()  # User finished test, reviewing profile before submission
