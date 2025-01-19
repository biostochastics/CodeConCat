"""Python code parser for CodeConcat."""

import ast
import re
from typing import List, Optional

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


def parse_python(file_path: str, content: str) -> ParsedFileData:
    """Parse Python code and return ParsedFileData."""
    parser = PythonParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path, language="python", content=content, declarations=declarations
    )


class PythonParser(BaseParser):
    """Python language parser."""

    def __init__(self):
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """
        Enhanced patterns for Python:
        - We define one pattern for 'class' and 'function' that can handle decorators,
          but we rely on the logic in parse() to gather multiple lines if needed.
        """
        # Common pattern for names
        name = r"[a-zA-Z_][a-zA-Z0-9_]*"

        self.patterns = {
            "class": re.compile(
                r"^class\s+(?P<n>" + name + r")"  # Class name
                r"(?:\s*\([^)]*\))?"  # Optional parent class
                r"\s*:"  # Class definition end
            ),
            "function": re.compile(
                r"^(?:async\s+)?def\s+(?P<n>" + name + r")"  # Function name with optional async
                r"\s*\([^)]*\)?"  # Function parameters, optional closing parenthesis
                r"\s*(?:->[^:]+)?"  # Optional return type
                r"\s*:?"  # Optional colon (for multi-line definitions)
            ),
            "variable": re.compile(
                r"^(?P<n>[a-z_][a-zA-Z0-9_]*)\s*"  # Variable name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]"  # Assignment but not comparison
            ),
            "constant": re.compile(
                r"^(?P<n>[A-Z][A-Z0-9_]*)\s*"  # Constant name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]"  # Assignment but not comparison
            ),
            "decorator": re.compile(
                r"^@(?P<n>[a-zA-Z_][\w.]*)(?:\s*\([^)]*\))?"  # Decorator with optional args
            ),
        }

        # Python doesn't always rely on '{' or '}', so we use the base logic for line by line
        self.block_start = ":"
        self.block_end = None
        self.line_comment = "#"
        self.block_comment_start = '"""'
        self.block_comment_end = '"""'

        # Our recognized modifiers (for demonstration)
        self.modifiers = {
            "@classmethod",
            "@staticmethod",
            "@property",
            "@abstractmethod",
        }

    def parse(self, content: str) -> List[Declaration]:
        """Parse Python code content and return list of declarations."""
        declarations = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                i += 1
                continue

            # Collect decorators
            decorators = []
            while line.startswith("@"):
                # Handle multi-line decorators
                decorator = line
                while "(" in decorator and ")" not in decorator:
                    i += 1
                    if i >= len(lines):
                        break
                    decorator += " " + lines[i].strip()
                decorators.append(decorator)
                i += 1
                if i >= len(lines):
                    break
                line = lines[i].strip()

            # Try to match patterns
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("n")
                    if not name:
                        continue

                    # Find block end and extract docstring
                    end_line = i
                    docstring = ""

                    if kind in ("function", "class"):
                        # Find the block end by counting indentation
                        base_indent = len(lines[i]) - len(line)
                        j = i + 1

                        # Look for docstring
                        while j < len(lines):
                            next_line = lines[j].strip()
                            if next_line and not next_line.startswith("#"):
                                curr_indent = len(lines[j]) - len(lines[j].lstrip())
                                if curr_indent > base_indent:
                                    if next_line.startswith('"""') or next_line.startswith("'''"):
                                        # Extract docstring
                                        quote_char = next_line[0] * 3
                                        doc_lines = []

                                        # Handle single-line docstring
                                        if next_line.endswith(quote_char) and len(next_line) > 6:
                                            docstring = next_line[3:-3].strip()
                                        else:
                                            # Multi-line docstring
                                            doc_lines.append(next_line[3:].strip())
                                            j += 1
                                            while j < len(lines):
                                                doc_line = lines[j].strip()
                                                if doc_line.endswith(quote_char):
                                                    doc_lines.append(doc_line[:-3].strip())
                                                    break
                                                doc_lines.append(doc_line)
                                                j += 1
                                            docstring = "\n".join(doc_lines).strip()
                                break
                            j += 1

                        # Continue finding the block end and nested declarations
                        while j < len(lines):
                            if j >= len(lines):
                                break
                            curr_line = lines[j].strip()
                            if curr_line and not curr_line.startswith("#"):
                                curr_indent = len(lines[j]) - len(lines[j].lstrip())

                                # Check for nested declarations
                                if curr_indent > base_indent:
                                    nested_content = []
                                    nested_base_indent = curr_indent
                                    while j < len(lines):
                                        if j >= len(lines):
                                            break
                                        curr_line = lines[j].strip()
                                        if curr_line and not curr_line.startswith("#"):
                                            curr_indent = len(lines[j]) - len(lines[j].lstrip())
                                            if curr_indent < nested_base_indent:
                                                break
                                            nested_content.append(lines[j][nested_base_indent:])
                                        j += 1

                                    # Parse nested content recursively
                                    if nested_content:
                                        nested_declarations = self.parse("\n".join(nested_content))
                                        for decl in nested_declarations:
                                            decl.start_line += j - len(nested_content)
                                            decl.end_line += j - len(nested_content)
                                            declarations.append(decl)

                                if curr_indent <= base_indent:
                                    end_line = j - 1
                                    break
                            j += 1
                            end_line = j - 1

                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=end_line + 1,
                            modifiers=set(decorators),
                            docstring=docstring,
                        )
                    )
                    i = end_line + 1
                    break
            else:
                i += 1

        return declarations
