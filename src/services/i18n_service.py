import logging
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


class I18nService:
    """Service for handling text localization with support for nested structures.

    Attributes:
        default_locale (str): The fallback language code (default: "ru").
        locales (Dict[str, Dict[str, Any]]): Memory storage for all loaded translations.
    """

    def __init__(self, locales_dir: Path, default_locale: str = "ru") -> None:
        """Initialize the I18n service.

        Args:
            locales_dir (Path): Path to the root 'locales' directory.
                         Expected structure: locales/{lang_code}/**/*.yaml
            default_locale (str): The fallback language code (default: "ru").
        """
        self.default_locale = default_locale
        # Structure: {'ru': {'ui': ..., 'surveys': ...}, 'en': ...}
        self.locales: Dict[str, Dict[str, Any]] = {}
        self._load_locales(locales_dir)

    def _load_locales(self, locales_dir: Path) -> None:
        """Load and merge all .yaml files from language subdirectories.

        Args:
            locales_dir (Path): The root directory containing language folders.

        Raises:
            RuntimeError: If the directory does not exist.
        """
        if not locales_dir.exists():
            error_msg = f"Locales directory not found: {locales_dir}"
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

        # Iterate over language folders (e.g., 'ru', 'en')
        for lang_path in locales_dir.iterdir():
            if not lang_path.is_dir():
                continue

            locale_code = lang_path.name
            self.locales.setdefault(locale_code, {})

            # Recursively find all .yaml files in this language folder
            for file_path in lang_path.rglob("*.yaml"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        # Deep merge this file's content into the main locale dict
                        self._deep_merge(self.locales[locale_code], data)
                except yaml.YAMLError as e:
                    logger.error("Error parsing YAML file %s: %s", file_path, e)
                except Exception as e:
                    logger.error("Unexpected error loading %s: %s", file_path, e)

        logger.info("Loaded locales for languages: %s", list(self.locales.keys()))

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Recursively merge source dictionary into target dictionary.

        This ensures that multiple files can contribute to the same top-level keys
        (e.g., 'surveys') without overwriting each other.

        Args:
            target (Dict[str, Any]): The dictionary to update (in-place).
            source (Dict[str, Any]): The dictionary containing new data.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def get(self, key: str, locale: str | None = None, **kwargs: Any) -> str:
        """Retrieve a localized string.

        Args:
            key (str): Dot-separated key (e.g., 'surveys.adizes_v1.q1').
            locale (str | None): The language code ('ru', 'en'). Defaults to service default.
            **kwargs (Any): Format arguments for dynamic strings.

        Returns:
            str: The localized string formatted with kwargs, or the key itself if not found.
        """
        target_locale = locale if locale and locale in self.locales else self.default_locale

        # Traverse the dictionary
        keys = key.split(".")
        value = self.locales.get(target_locale, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
            else:
                # Key path broken (e.g., trying to access 'a.b' but 'a' is a string)
                return str(key)

        if not isinstance(value, str):
            # Key points to a dict (incomplete path) or None
            return str(key)

        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.warning(
                    "Missing format key '%s' for string '%s' in locale '%s'",
                    e,
                    key,
                    target_locale,
                )
                return value

        return value
