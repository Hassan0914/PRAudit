"""Language registry managing Tree-sitter language bindings."""

import importlib
from typing import Dict, Optional
import tree_sitter
from app.core.exceptions import ParserNotFoundError
from app.core.logging import setup_logger
from app.core.types import Language

logger = setup_logger("parsing.languages")


class LanguageRegistry:
    """Registry for managing and fetching Tree-sitter Language instances."""

    _instance: Optional["LanguageRegistry"] = None
    _languages: Dict[Language, tree_sitter.Language]

    def __new__(cls) -> "LanguageRegistry":
        """Singleton pattern for central language management."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._languages = {}
            cls._instance._register_default_languages()
        return cls._instance

    def _register_default_languages(self) -> None:
        """Register built-in supported Tree-sitter language packages."""
        known_packages = {
            Language.PYTHON: "tree_sitter_python",
            Language.JAVASCRIPT: "tree_sitter_javascript",
            Language.TYPESCRIPT: "tree_sitter_typescript",
            Language.GO: "tree_sitter_go",
            Language.RUST: "tree_sitter_rust",
            Language.JAVA: "tree_sitter_java",
            Language.CPP: "tree_sitter_cpp",
            Language.C: "tree_sitter_c",
            Language.HTML: "tree_sitter_html",
            Language.CSS: "tree_sitter_css",
            Language.JSON: "tree_sitter_json",
        }

        for lang_enum, pkg_name in known_packages.items():
            try:
                mod = importlib.import_module(pkg_name)
                if hasattr(mod, "language"):
                    ts_lang = tree_sitter.Language(mod.language())
                    self._languages[lang_enum] = ts_lang
                    logger.debug("Successfully registered Tree-sitter binding for %s", lang_enum.value)
            except ImportError:
                logger.debug("Tree-sitter package %s not installed for %s", pkg_name, lang_enum.value)
            except Exception as exc:
                logger.warning("Error initializing Tree-sitter binding for %s: %s", lang_enum.value, exc)

    def is_supported(self, language: Language) -> bool:
        """Check if a Tree-sitter parser is available for a language.

        Args:
            language: The target Language enum.

        Returns:
            True if supported and registered, False otherwise.
        """
        return language in self._languages

    def get_language(self, language: Language) -> tree_sitter.Language:
        """Retrieve the Tree-sitter Language instance for a given language.

        Args:
            language: Target Language enum.

        Returns:
            tree_sitter.Language instance.

        Raises:
            ParserNotFoundError: If no language binding is registered.
        """
        if not self.is_supported(language):
            raise ParserNotFoundError(
                f"No Tree-sitter language binding registered for language: {language.value}"
            )
        return self._languages[language]


language_registry = LanguageRegistry()
