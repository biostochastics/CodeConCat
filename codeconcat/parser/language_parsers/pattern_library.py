# file: codeconcat/parser/language_parsers/pattern_library.py

"""
Pattern library for language parsers.

This module provides common regex patterns that can be reused across different
language parsers to improve consistency and reduce duplication. Patterns are
organized by their purpose and language family compatibility.
"""

import logging
import re
from typing import List, Optional, Pattern

from ...utils.security import InputSanitizer

logger = logging.getLogger(__name__)

# Common identifier patterns
IDENTIFIER_BASIC = r"[a-zA-Z_][a-zA-Z0-9_]*"
IDENTIFIER_UNICODE = (
    r"[\w\u0080-\uffff]+"  # Unicode word character class for international identifiers
)

# Common modifiers across multiple languages
C_FAMILY_MODIFIERS = [
    "public",
    "private",
    "protected",
    "static",
    "final",
    "abstract",
    "synchronized",
    "native",
    "strictfp",
    "const",
    "volatile",
    "transient",
    "virtual",
    "override",
    "sealed",
    "readonly",
    "inline",
    "explicit",
    "extern",
]

PYTHON_DECORATORS = r"(?:@[\w\.]+(?:\([^)]*\))?\s*)*"


class DocstringPatterns:
    """Patterns for extracting docstrings in different languages."""

    # Python triple-quoted docstrings
    PYTHON_TRIPLE_QUOTE = re.compile(r'^\s*(""".*?"""|\'\'\'.*?\'\'\')', re.DOTALL)

    # Java/C#/Kotlin style docstrings
    JAVADOC = re.compile(r"/\*\*.*?\*/", re.DOTALL)

    # Go style docstrings (block comments)
    GO_DOC = re.compile(r"/\*.*?\*/", re.DOTALL)

    # Single-line comment docstrings (e.g., ///, ///, #)
    SINGLE_LINE_DOC = {
        "csharp": re.compile(r"^\s*///.*$", re.MULTILINE),
        "python": re.compile(r"^\s*#.*$", re.MULTILINE),
        "javascript": re.compile(r"^\s*//.*$", re.MULTILINE),
    }

    @staticmethod
    def extract_python_docstring(lines: List[str], start: int, end: int) -> str:
        """Extract Python-style docstring from lines."""
        for i in range(start, min(end + 1, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                doc_lines: list[str] = []
                quote = line[:3]
                if line.endswith(quote) and len(line) > 3:
                    return line[3:-3].strip()
                doc_lines.append(line[3:])
                for j in range(i + 1, end + 1):
                    line2 = lines[j]
                    if line2.strip().endswith(quote):
                        doc_lines.append(line2.strip()[:-3])
                        return "\n".join(doc_lines).strip()
                    doc_lines.append(line2.strip())
        return ""


class CommentPatterns:
    """Patterns for identifying comments in different languages."""

    # Single-line comments
    SINGLE_LINE = {
        "python": r"#",
        "javascript": r"//",
        "cpp": r"//",
        "java": r"//",
        "csharp": r"//",
        "ruby": r"#",
        "bash": r"#",
        "go": r"//",
        "rust": r"///",
        "php": r"//",
    }

    # Block comment start/end
    BLOCK_COMMENT = {
        "javascript": (r"/\*", r"\*/"),
        "cpp": (r"/\*", r"\*/"),
        "java": (r"/\*", r"\*/"),
        "csharp": (r"/\*", r"\*/"),
        "go": (r"/\*", r"\*/"),
        "rust": (r"/\*", r"\*/"),
        "php": (r"/\*", r"\*/"),
        "css": (r"/\*", r"\*/"),
    }


class FunctionPatterns:
    """Patterns for identifying functions in different languages."""

    # C-style function patterns with optional modifiers and return type
    # Security: Sanitize pattern to prevent ReDoS attacks
    c_style_pattern = (
        r"^\s*(?:(?:" + "|".join(C_FAMILY_MODIFIERS) + r")\s+)*"
        r"(?:(?P<return_type>[\w\.\$<>,\[\]?]+\s+)+?)?"
        r"(?P<name>" + IDENTIFIER_BASIC + r")\s*\([^)]*\)"
    )
    C_STYLE = re.compile(InputSanitizer.sanitize_regex(c_style_pattern, max_length=500))

    # Python function pattern with optional decorators
    # Security: Sanitize pattern to prevent ReDoS attacks
    python_pattern = (
        r"^\s*"
        + PYTHON_DECORATORS
        + r"def\s+(?P<name>"
        + IDENTIFIER_BASIC
        + r")\s*\([^)]*\)\s*(?:->\s*[^:]+)?:"
    )
    PYTHON = re.compile(InputSanitizer.sanitize_regex(python_pattern, max_length=500))

    # JavaScript/TypeScript function patterns (including arrow functions)
    # Security: Sanitize patterns to prevent ReDoS attacks
    js_function_pattern = (
        r"^\s*(?:export\s+)?(?:async\s+)?function\s+(?P<name>" + IDENTIFIER_BASIC + r")\s*\([^)]*\)"
    )
    js_method_pattern = (
        r"^\s*(?:static\s+)?(?:async\s+)?(?P<name>" + IDENTIFIER_BASIC + r")\s*\([^)]*\)"
    )
    js_arrow_pattern = (
        r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>"
        + IDENTIFIER_BASIC
        + r")\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z_][a-zA-Z0-9_]*)\s*=>"
    )

    JS_TS = {
        "function_declaration": re.compile(
            InputSanitizer.sanitize_regex(js_function_pattern, max_length=500)
        ),
        "method_declaration": re.compile(
            InputSanitizer.sanitize_regex(js_method_pattern, max_length=500)
        ),
        "arrow_function": re.compile(
            InputSanitizer.sanitize_regex(js_arrow_pattern, max_length=500)
        ),
    }


class ClassPatterns:
    """Patterns for identifying classes in different languages."""

    # C-style class definitions
    # Security: Sanitize pattern to prevent ReDoS attacks
    c_class_pattern = (
        r"^\s*(?:(?:" + "|".join(C_FAMILY_MODIFIERS) + r")\s+)*"
        r"class\s+(?P<name>"
        + IDENTIFIER_BASIC
        + r")(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?"
    )
    C_STYLE = re.compile(InputSanitizer.sanitize_regex(c_class_pattern, max_length=500))

    # Python class with optional decorators and inheritance
    # Security: Sanitize pattern to prevent ReDoS attacks
    python_class_pattern = (
        r"^\s*"
        + PYTHON_DECORATORS
        + r"class\s+(?P<name>"
        + IDENTIFIER_BASIC
        + r")(?:\s*\([^)]*\))?:"
    )
    PYTHON = re.compile(InputSanitizer.sanitize_regex(python_class_pattern, max_length=500))

    # JavaScript/TypeScript class
    # Security: Sanitize pattern to prevent ReDoS attacks
    js_class_pattern = (
        r"^\s*(?:export\s+)?class\s+(?P<name>"
        + IDENTIFIER_BASIC
        + r")(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?"
    )
    JS_TS = re.compile(InputSanitizer.sanitize_regex(js_class_pattern, max_length=500))


class ImportPatterns:
    """Patterns for identifying imports in different languages."""

    # Python imports
    # Security: Sanitize patterns to prevent ReDoS attacks
    python_import_pattern = (
        r"^\s*import\s+(?P<module>[a-zA-Z0-9_.,\s]+)(?:\s+as\s+(?P<alias>[a-zA-Z0-9_]+))?"
    )
    python_from_import_pattern = (
        r"^\s*from\s+(?P<source>[a-zA-Z0-9_.]+)\s+import\s+(?P<imports>[a-zA-Z0-9_.*,\s]+)"
    )

    PYTHON = {
        "import": re.compile(InputSanitizer.sanitize_regex(python_import_pattern, max_length=300)),
        "from_import": re.compile(
            InputSanitizer.sanitize_regex(python_from_import_pattern, max_length=300)
        ),
    }

    # JavaScript/TypeScript imports
    # Security: Sanitize patterns to prevent ReDoS attacks
    js_import_pattern = (
        r'^\s*import\s+(?:{[^}]+}|\*\s+as\s+[a-zA-Z0-9_]+|[a-zA-Z0-9_]+)\s+from\s+[\'"][^\'"]+[\'"]'
    )
    js_require_pattern = r'^\s*(?:const|let|var)\s+(?P<name>[a-zA-Z0-9_{}:,\s]+)\s*=\s*require\s*\([\'"][^\'"]+[\'"]\)'

    JS_TS = {
        "import": re.compile(InputSanitizer.sanitize_regex(js_import_pattern, max_length=300)),
        "require": re.compile(InputSanitizer.sanitize_regex(js_require_pattern, max_length=300)),
    }

    # Java imports
    # Security: Sanitize pattern to prevent ReDoS attacks
    java_import_pattern = (
        r"^\s*import\s+(?:static\s+)?(?P<package>[a-zA-Z0-9_.]+(?:\.[a-zA-Z0-9_]+|\*));"
    )
    JAVA = re.compile(InputSanitizer.sanitize_regex(java_import_pattern, max_length=300))

    # Go imports
    # Security: Sanitize pattern to prevent ReDoS attacks
    go_import_pattern = r'^\s*import\s+(?:\([^)]+\)|"[^"]+")'
    GO = re.compile(InputSanitizer.sanitize_regex(go_import_pattern, max_length=300))


def create_pattern_with_modifiers(
    base_pattern: str, modifiers: Optional[List[str]] = None, prefix: str = r"^\s*"
) -> Pattern:
    """
    Create a regex pattern with optional modifiers.

    Args:
        base_pattern: The core pattern to match after the modifiers.
        modifiers: A list of modifier keywords (e.g., 'public', 'static').
        prefix: Prefix to add at the start of the pattern (default: whitespace).

    Returns:
        A compiled regex pattern.
    """
    if modifiers:
        modifier_pattern = f"(?:(?:{'|'.join(modifiers)})\\s+)*"
        full_pattern = f"{prefix}{modifier_pattern}{base_pattern}"
    else:
        full_pattern = f"{prefix}{base_pattern}"

    # Security: Sanitize the final pattern to prevent ReDoS attacks
    sanitized_pattern = InputSanitizer.sanitize_regex(full_pattern, max_length=500)
    return re.compile(sanitized_pattern)
