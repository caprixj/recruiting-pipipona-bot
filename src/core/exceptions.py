class RecruitingBotError(Exception):
    """Base exception for the Recruiting Bot application."""


class EmployeeNotFoundError(RecruitingBotError):
    """Raised when an employee record cannot be found in the database."""


class SurveySessionNotFoundError(RecruitingBotError):
    """Raised when a survey session record cannot be found in the database."""
