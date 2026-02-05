from typing import Union

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.models.enums import InputType


class InputTypeFilter(BaseFilter):
    """Filter to route updates based on the current survey Step Input Type.

    Checks the 'input_type' field stored in the FSM state data.

    Attributes:
        input_type (InputType): The expected InputType to filter for.
    """

    def __init__(self, input_type: InputType):
        """Initialize the filter.

        Args:
            input_type (InputType): The expected InputType (e.g., InputType.RANKING).
        """
        self.input_type = input_type

    async def __call__(self, event: Union[Message, CallbackQuery], state: FSMContext) -> bool:
        """Check if the current state matches the expected input type.

        Args:
            event (Union[Message, CallbackQuery]): The incoming update (Message or Callback).
            state (FSMContext): The FSM Context.

        Returns:
            bool: True if the FSM data contains the matching input_type.
        """
        data = await state.get_data()
        current_type = data.get("input_type")

        # Compare strings (enum values) to be safe across serialization
        return current_type == self.input_type
