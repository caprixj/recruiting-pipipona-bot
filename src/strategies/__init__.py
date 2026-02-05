from src.core.interfaces.survey_strategy import ISurveyStrategy
from src.models.enums import SurveyType
from src.strategies.adizes import AdizesStrategy

# Registry mapping Enums to Concrete Implementations
_SURVEY_REGISTRY = {
    SurveyType.ADIZES: AdizesStrategy(),
}


def get_strategy(survey_type: SurveyType) -> ISurveyStrategy:
    """Retrieve the strategy implementation for a given survey type.

    Args:
        survey_type (SurveyType): The enum type of the survey.

    Returns:
        ISurveyStrategy: The concrete strategy instance.

    Raises:
        NotImplementedError: If the strategy for the type is not registered.
    """
    strategy = _SURVEY_REGISTRY.get(survey_type)
    if not strategy:
        raise NotImplementedError(f"Strategy for survey type '{survey_type}' is not implemented.")

    return strategy
