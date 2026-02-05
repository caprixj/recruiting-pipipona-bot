from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from src.models.enums import InputType


@dataclass
class QuestionData:
    """Standardized format for a survey question.

    Attributes:
        id (int): Unique identifier for the question.
        text_key (str): i18n key for the question text (e.g., 'surveys.adizes_v1.q1').
        options (List[str]): List of option keys or labels.
        input_type (InputType): Controls the UI behavior (Ranking vs Choice).
    """

    id: int
    text_key: str  # i18n key for the question text (e.g., 'surveys.adizes_v1.q1')
    options: List[str]  # List of option keys or labels
    input_type: InputType  # Controls the UI behavior (Ranking vs Choice)


class ISurveyStrategy(ABC):
    """Interface for Survey Logic Strategies.

    Any new test type (e.g., DISC, Big5) must implement these methods.
    The strategy is stateless; it relies on the passed 'config' or 'survey_key'
    to handle specific test instances.
    """

    @abstractmethod
    def get_question(self, step: int, survey_key: str) -> QuestionData:
        """Retrieve data for a specific step.

        Args:
            step (int): The 0-based index of the question.
            survey_key (str): The unique key of the survey (e.g., 'adizes_v1').

        Returns:
            QuestionData: QuestionData object containing text key, options, and UI type.

        Raises:
            ValueError: If step is out of bounds.
        """

    @abstractmethod
    def validate_answer(self, step: int, answer: Any) -> bool:
        """Validate the format and content of an answer.

        Args:
            step (int): The current question index.
            answer (Any): The data payload from the user.

        Returns:
            bool: True if valid, False otherwise.
        """

    @abstractmethod
    def calculate_results(self, answers: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """Process raw answers into final scores/categories.

        Args:
            answers (Dict[str, Any]): Dictionary of {step_index: answer_payload}.
            config (Dict[str, Any]): The loaded configuration (matrix, thresholds) for this survey.

        Returns:
            Any: Dictionary of calculated results.
        """

    @abstractmethod
    def get_total_steps(self, config: Dict[str, Any]) -> int:
        """Return total number of questions.

        Args:
            config (Dict[str, Any]): The loaded configuration.

        Returns:
            int: Total number of questions in the survey.
        """
