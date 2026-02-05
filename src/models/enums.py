from enum import Enum, unique


@unique
class SurveyType(str, Enum):
    """Types of supported methodologies."""

    ADIZES = "ADIZES"


@unique
class SurveyStatus(str, Enum):
    """Lifecycle status of a survey session."""

    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


@unique
class InputType(str, Enum):
    """Defines the UI interaction model for a question."""

    SINGLE_CHOICE = "SINGLE_CHOICE"  # Click one, auto-submit
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"  # Select multiple, confirm
    RANKING = "RANKING"  # Sort options (e.g., Adizes)
    FREE_TEXT = "FREE_TEXT"  # Text input
