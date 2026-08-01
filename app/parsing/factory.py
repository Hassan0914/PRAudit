"""Parser factory and thread-safe parser cache."""

import threading
from typing import Dict
import tree_sitter

from app.core.exceptions import ParserNotFoundError
from app.core.logging import setup_logger
from app.core.types import Language
from app.parsing.languages import language_registry

logger = setup_logger("parsing.factory")


class ParserCache:
    """Thread-safe cache for Tree-sitter Parser instances."""

    def __init__(self) -> None:
        """Initialize parser cache."""
        self._parsers: Dict[Language, tree_sitter.Parser] = {}
        self._lock = threading.Lock()

    def get_parser(self, language: Language) -> tree_sitter.Parser:
        """Get or create a Tree-sitter Parser for the given language.

        Args:
            language: Target Language enum.

        Returns:
            Configured tree_sitter.Parser instance.

        Raises:
            ParserNotFoundError: If language binding is unavailable.
        """
        with self._lock:
            if language not in self._parsers:
                ts_lang = language_registry.get_language(language)
                parser = tree_sitter.Parser(ts_lang)
                self._parsers[language] = parser
                logger.debug("Created new cached parser for %s", language.value)

            return self._parsers[language]


class ParserFactory:
    """Factory interface for producing Tree-sitter parser instances."""

    def __init__(self) -> None:
        """Initialize factory with internal cache."""
        self._cache = ParserCache()

    def create_parser(self, language: Language) -> tree_sitter.Parser:
        """Create or retrieve a cached parser for the specified language.

        Args:
            language: Target Language enum.

        Returns:
            tree_sitter.Parser instance.
        """
        return self._cache.get_parser(language)


parser_factory = ParserFactory()
