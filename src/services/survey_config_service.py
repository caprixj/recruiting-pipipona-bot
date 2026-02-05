from pathlib import Path
from typing import Any, Dict

import yaml
from yaml import YAMLError

from src.core.exceptions import SurveyConfigError


class SurveyConfigService:
    """Service responsible for loading and caching survey configurations from data/surveys.

    Attributes:
        _cache (Dict[str, Dict[str, Any]]): In-memory cache for survey configurations.
        _base_dir (Path): Base directory where survey YAML files are stored.
    """

    def __init__(self) -> None:
        """Initialize the service with a cache and data directory."""
        # In-memory cache to prevent disk I/O on every request
        self._cache: Dict[str, Dict[str, Any]] = {}
        # Base path for survey configuration files
        self._base_dir = Path("data/surveys")

    def load_config(self, survey_key: str) -> Dict[str, Any]:
        """Load the configuration for a specific survey key.

        Args:
            survey_key (str): The unique identifier for the survey (e.g., 'adizes_v1').

        Returns:
            Dict[str, Any]: The configuration dictionary containing 'matrix', 'thresholds', etc.

        Raises:
            SurveyConfigError: If the file is missing or contains invalid YAML.
        """
        # Return from cache if available
        if survey_key in self._cache:
            return self._cache[survey_key]

        # Construct file path
        file_path = self._base_dir / f"{survey_key}.yaml"

        if not file_path.exists():
            raise SurveyConfigError(f"Configuration file for '{survey_key}' not found at {file_path}")

        # Load and parse YAML
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            # Update cache
            self._cache[survey_key] = config
            return config

        except YAMLError as e:
            raise SurveyConfigError(f"Invalid YAML in configuration '{survey_key}': {e}")
        except Exception as e:
            raise SurveyConfigError(f"Unexpected error loading config '{survey_key}': {e}")
