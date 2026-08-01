"""Compression service reducing prompt token footprint."""

import re
from app.core.logging import setup_logger

logger = setup_logger("optimization.compression")


class CompressionService:
    """Service providing prompt context text compression."""

    def compress_text(self, text: str) -> str:
        """Compress text by removing redundant whitespace and line breaks.

        Args:
            text: Uncompressed text string.

        Returns:
            Compressed text string.
        """
        if not text:
            return ""

        # Collapse multiple blank lines into a single newline
        lines = [line.rstrip() for line in text.splitlines()]
        cleaned = [lines[i] for i in range(len(lines)) if i == 0 or lines[i] or lines[i - 1]]

        compressed = "\n".join(cleaned)
        orig_tokens = len(text.split())
        comp_tokens = len(compressed.split())

        logger.debug("Compressed prompt context from %d to %d words", orig_tokens, comp_tokens)
        return compressed
