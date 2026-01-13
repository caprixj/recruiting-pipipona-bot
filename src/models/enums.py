from enum import StrEnum, auto


class SurveyType(StrEnum):
    """Available test types."""

    ADIZES = auto()  # PAEI Management Style


class SurveyStatus(StrEnum):
    """Progress status of a survey session."""

    IN_PROGRESS = auto()
    COMPLETED = auto()
    ABANDONED = auto()
