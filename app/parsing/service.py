"""Parsing Engine service providing high-level AST parsing APIs."""

import time
from pathlib import Path
from typing import Optional, Union

from app.core.exceptions import ParserNotFoundError
from app.core.logging import setup_logger
from app.core.types import Language
from app.parsing.factory import parser_factory
from app.parsing.languages import language_registry
from app.parsing.models import ParseResult, ParserError
from app.parsing.validator import ASTValidator
from app.repository.models import SourceFile

logger = setup_logger("parsing.service")


class ParsingEngine:
    """High-level service for parsing source code into Abstract Syntax Trees."""

    def __init__(self) -> None:
        """Initialize ParsingEngine with ASTValidator."""
        self.validator = ASTValidator()

    def is_language_supported(self, language: Language) -> bool:
        """Check if language parsing is supported.

        Args:
            language: Target Language enum.

        Returns:
            True if supported, False otherwise.
        """
        return language_registry.is_supported(language)

    def parse_code(
        self, code: Union[str, bytes], language: Language, file_path: str = "inline_code"
    ) -> ParseResult:
        """Parse source code content into an Abstract Syntax Tree.

        Args:
            code: Source code as string or bytes.
            language: Programming language enum.
            file_path: Relative or display path of the file being parsed.

        Returns:
            ParseResult containing the AST, errors, and metadata.
        """
        start_time = time.perf_counter()

        if isinstance(code, str):
            code_bytes = code.encode("utf-8")
        else:
            code_bytes = code

        if not language_registry.is_supported(language):
            duration = (time.perf_counter() - start_time) * 1000.0
            return ParseResult(
                file_path=file_path,
                language=language,
                root_node=None,
                has_syntax_errors=False,
                errors=[
                    ParserError(
                        line=1,
                        column=1,
                        node_type="UNSUPPORTED_LANGUAGE",
                        text="",
                        message=f"Language '{language.value}' is not supported by Tree-sitter parser registry.",
                    )
                ],
                parse_duration_ms=duration,
                is_success=False,
            )

        try:
            parser = parser_factory.create_parser(language)
            raw_tree = parser.parse(code_bytes)

            root_ast_node, errors = self.validator.build_ast_node(raw_tree.root_node, code_bytes)
            duration = (time.perf_counter() - start_time) * 1000.0

            has_errors = len(errors) > 0

            return ParseResult(
                file_path=file_path,
                language=language,
                root_node=root_ast_node,
                has_syntax_errors=has_errors,
                errors=errors,
                parse_duration_ms=duration,
                is_success=True,
                raw_tree=raw_tree,
            )

        except ParserNotFoundError as p_err:
            duration = (time.perf_counter() - start_time) * 1000.0
            logger.warning("Parser missing for language %s on file %s: %s", language, file_path, p_err)
            return ParseResult(
                file_path=file_path,
                language=language,
                root_node=None,
                has_syntax_errors=False,
                errors=[
                    ParserError(
                        line=1, column=1, node_type="PARSER_NOT_FOUND", text="", message=str(p_err)
                    )
                ],
                parse_duration_ms=duration,
                is_success=False,
            )
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000.0
            logger.error("Unexpected error during parsing file %s: %s", file_path, exc, exc_info=True)
            return ParseResult(
                file_path=file_path,
                language=language,
                root_node=None,
                has_syntax_errors=True,
                errors=[
                    ParserError(
                        line=1, column=1, node_type="PARSING_EXCEPTION", text="", message=str(exc)
                    )
                ],
                parse_duration_ms=duration,
                is_success=False,
            )

    def parse_file(self, source_file: SourceFile) -> ParseResult:
        """Parse a SourceFile object by reading its absolute path.

        Args:
            source_file: SourceFile object to parse.

        Returns:
            ParseResult for the target file.
        """
        try:
            content_bytes = source_file.absolute_path.read_bytes()
            return self.parse_code(
                code=content_bytes,
                language=source_file.language,
                file_path=source_file.relative_path,
            )
        except Exception as exc:
            logger.error("Failed to read file for parsing %s: %s", source_file.absolute_path, exc)
            return ParseResult(
                file_path=source_file.relative_path,
                language=source_file.language,
                root_node=None,
                has_syntax_errors=True,
                errors=[
                    ParserError(
                        line=1, column=1, node_type="FILE_READ_ERROR", text="", message=str(exc)
                    )
                ],
                parse_duration_ms=0.0,
                is_success=False,
            )
