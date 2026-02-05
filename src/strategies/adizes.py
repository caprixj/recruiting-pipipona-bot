from typing import Any, Dict

from src.core.interfaces.survey_strategy import ISurveyStrategy, QuestionData
from src.models.enums import InputType


class AdizesStrategy(ISurveyStrategy):
    """Implementation of the Adizes (PAEI) Management Style methodology.

    This strategy handles:
    1. Validation of ranking inputs (sorting 4 options).
    2. Dynamic question retrieval based on survey keys.
    3. Calculation of PAEI scores using a configurable matrix.

    Attributes:
        OPTIONS (List[str]): Standard options for this test: A, B, C, D representing 4 traits.
        RANK_WEIGHTS (Dict[int, int]): Points for ranks: 1st place -> 4 points, ..., 4th place -> 1 point.
    """

    # Options are standard for this test: A, B, C, D representing 4 traits
    OPTIONS = ["A", "B", "C", "D"]

    # Points for ranks: 1st place -> 4 points, ... 4th place -> 1 point
    RANK_WEIGHTS = {0: 4, 1: 3, 2: 2, 3: 1}

    def get_total_steps(self, config: Dict[str, Any]) -> int:
        """Return total number of questions based on the configuration matrix.

        Args:
            config (Dict[str, Any]): The loaded configuration dictionary containing the 'matrix'.

        Returns:
            int: The count of questions defined in the matrix.
        """
        # The matrix keys represent questions.
        matrix = config.get("matrix", {})
        return len(matrix)

    def get_question(self, step: int, survey_key: str) -> QuestionData:
        """Retrieve data for a specific step.

        Args:
            step (int): The 0-based index of the question.
            survey_key (str): The unique key of the survey (e.g., 'adizes_v1').

        Returns:
            QuestionData: QuestionData object containing the specific text key, options, and UI type.

        Raises:
            ValueError: If step is negative.
        """
        if step < 0:
            raise ValueError(f"Step {step} cannot be negative.")

        # Question IDs standardly start at 1, while steps start at 0
        question_id = step + 1

        # Construct i18n key. e.g.: surveys.adizes_v1.q1
        text_key = f"surveys.{survey_key}.q{question_id}"

        return QuestionData(
            id=question_id,
            text_key=text_key,
            options=self.OPTIONS,
            input_type=InputType.RANKING,
        )

    def validate_answer(self, step: int, answer: Any) -> bool:
        """Validate the format and content of an answer.

        Adizes answer format must be a list of 4 unique options ordered by preference.
        Example: ["B", "A", "D", "C"]

        Args:
            step (int): The current question index.
            answer (Any): The data payload from the user.

        Returns:
            bool: True if the answer is a list of 4 unique valid options.
        """
        # Type Check
        if not isinstance(answer, list):
            return False

        # Length Check
        if len(answer) != 4:
            return False

        # Content Check
        unique_answers = set(answer)
        valid_options = set(self.OPTIONS)

        # Must contain only valid options, and count must remain 4 (implies uniqueness)
        return unique_answers.issubset(valid_options) and len(unique_answers) == 4

    def calculate_results(self, answers: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw answers into final PAEI scores and string representation.

        Args:
            answers (Dict[str, Any]): Dictionary of {step_index: [rank1, rank2, rank3, rank4]}.
            config (Dict[str, Any]): Configuration dict containing 'matrix' and 'thresholds'.

        Returns:
            Dict[str, Any]: Dictionary with keys: 'P', 'A', 'E', 'I', 'string_rep' (e.g., 'Pa-i').
        """
        # Changed type hint to Any to accommodate the final string string_rep
        scores: Dict[str, Any] = {"P": 0, "A": 0, "E": 0, "I": 0}
        matrix = config.get("matrix", {})

        # Summation
        for step_str, user_rank_list in answers.items():
            # Steps are stored as strings in JSONB.
            # Convert step (0-based) to Matrix ID (1-based)
            question_id = int(step_str) + 1

            # Matrix structure: { 1: {"A": "P", "B": "E", ...}, ... }
            question_map = matrix.get(question_id)

            if not question_map:
                # If matrix is incomplete or mismatched, skip safely
                continue

            # Iterate through the user's ranked list
            # index 0 = 1st choice (4 pts), index 3 = 4th choice (1 pt)
            for rank_index, option_char in enumerate(user_rank_list):
                # Look up which trait this option represents for this specific question
                trait = question_map.get(option_char)

                if trait and trait in scores:
                    points = self.RANK_WEIGHTS.get(rank_index, 0)
                    scores[trait] += points

        # String Representation (PaEi)
        thresholds = config.get("thresholds", {"high": 30, "low": 10})
        string_rep = self._generate_string_rep(scores, thresholds)  # type: ignore

        scores["string_rep"] = string_rep
        return scores

    @staticmethod
    def _generate_string_rep(scores: Dict[str, int], thresholds: Dict[str, int]) -> str:
        """Generate the Adizes code (e.g., 'Pa-i') based on thresholds.

        Args:
            scores (Dict[str, int]): Dictionary of calculated scores {'P': int, 'A': int...}.
            thresholds (Dict[str, int]): Dictionary defining 'high' and 'low' cutoffs.

        Returns:
            str: A 4-character string representing the personality profile (e.g., 'PaEi', '--ei').
        """
        result = []
        high = thresholds.get("high", 30)
        low = thresholds.get("low", 10)

        # Order must be P, A, E, I
        for trait in ["P", "A", "E", "I"]:
            val = scores.get(trait, 0)
            if val >= high:
                result.append(trait)  # Uppercase
            elif val >= low:
                result.append(trait.lower())  # Lowercase
            else:
                result.append("-")  # Dash

        return "".join(result)
