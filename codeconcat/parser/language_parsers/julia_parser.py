# file: codeconcat/parser/language_parsers/julia_parser.py

import re
from typing import List, Optional

from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.base_parser import BaseParser, Declaration, ParseResult


def parse_julia(file_path: str, content: str) -> ParseResult:
    parser = JuliaParser()
    try:
        declarations = parser.parse_file(content)
    except Exception as e:
        # Wrap internal parser errors in LanguageParserError
        raise LanguageParserError(
            message=f"Failed to parse Julia file: {e}", file_path=file_path, original_exception=e
        )
    return ParseResult(
        file_path=file_path,
        language="julia",
        content=content,
        declarations=declarations,
    )


class JuliaParser(BaseParser):
    def __init__(self):
        """Initialize Julia parser with regex patterns."""
        super().__init__()
        self.patterns = {
            "module": re.compile(r"^module\s+(?P<name>\w+)"),
            "struct": re.compile(r"^(?:mutable\s+)?struct\s+(?P<name>\w+)"),
            "function": re.compile(r"^function\s+(?P<name>[\w.]+)"),
            "macro": re.compile(r"^macro\s+(?P<name>\w+)"),
            "inline_function": re.compile(r"^(?P<name>\w+)\s*\([^)]*\)\s*="),
            "type": re.compile(r"^(?:abstract|primitive)\s+type\s+(?P<name>\w+)"),
        }
        self.line_comment = "#"
        self.block_comment_start = "#="
        self.block_comment_end = "=#"

    def parse_file(self, content: str) -> List[Declaration]:
        """Parse Julia file content and return list of declarations."""
        return self.parse(content)

    def parse(self, content: str) -> List[Declaration]:
        """Parse Julia code and return declarations."""
        declarations = []
        lines = content.split("\n")
        i = 0
        current_module = None

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                i += 1
                continue

            # Try each pattern
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    if not name:
                        continue

                    # Extract modifiers
                    modifiers = set()
                    if kind == "struct" and "mutable" in line:
                        modifiers.add("mutable")
                    if "@inline" in line:
                        modifiers.add("inline")

                    # Find end line
                    end_line = i
                    if kind in ["module", "struct", "function", "macro", "type"]:
                        j = i + 1
                        while j < len(lines):
                            curr_line = lines[j].strip()
                            if curr_line == "end":
                                end_line = j
                                break
                            j += 1
                    elif kind == "inline_function":
                        j = i + 1
                        while j < len(lines):
                            curr_line = lines[j].strip()
                            if curr_line.endswith(";") or curr_line.endswith("end"):
                                end_line = j
                                break
                            j += 1

                    # Create declaration
                    decl = Declaration(
                        kind="function" if kind == "inline_function" else kind,
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=modifiers,
                        docstring="",
                        children=[],
                    )

                    # Handle module declarations
                    if kind == "module":
                        current_module = decl
                        declarations.append(decl)
                        i = end_line
                    else:
                        if current_module is not None:
                            current_module.children.append(decl)
                        else:
                            declarations.append(decl)
                        i = end_line
                    break
            i += 1

        return declarations
