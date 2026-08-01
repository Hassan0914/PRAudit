"""Core type definitions and enumerations for PRAudit."""

from enum import Enum, auto


class Language(str, Enum):
    """Supported programming languages in PRAudit."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    MARKDOWN = "markdown"
    YAML = "yaml"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, extension: str) -> "Language":
        """Map file extension to standard Language enum.

        Args:
            extension: File extension including or excluding leading dot (e.g. '.py' or 'py').

        Returns:
            Corresponding Language enum value.
        """
        ext = extension.lower().lstrip(".")
        mapping = {
            "py": cls.PYTHON,
            "js": cls.JAVASCRIPT,
            "jsx": cls.JAVASCRIPT,
            "ts": cls.TYPESCRIPT,
            "tsx": cls.TYPESCRIPT,
            "go": cls.GO,
            "rs": cls.RUST,
            "java": cls.JAVA,
            "cpp": cls.CPP,
            "cc": cls.CPP,
            "cxx": cls.CPP,
            "hpp": cls.CPP,
            "h": cls.C,
            "c": cls.C,
            "html": cls.HTML,
            "htm": cls.HTML,
            "css": cls.CSS,
            "json": cls.JSON,
            "md": cls.MARKDOWN,
            "yaml": cls.YAML,
            "yml": cls.YAML,
        }
        return mapping.get(ext, cls.UNKNOWN)


class ChunkType(str, Enum):
    """Types of semantic code chunks extracted from source code."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"
    BLOCK = "block"


class SymbolKind(str, Enum):
    """Kinds of programming language symbols extracted from code."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    EXPORT = "export"
    VARIABLE = "variable"
    CONSTANT = "constant"
    MODULE = "module"
