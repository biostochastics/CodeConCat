"""R code parser for CodeConcat."""

import re
from typing import Dict, List, Pattern

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


class RParser(BaseParser):
    """R language parser."""

    def _setup_patterns(self):
        """Set up R-specific patterns."""
        self.patterns = {
            "function": re.compile(
                r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
                r"(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Function name
                r"\s*<?-\s*function\s*\("  # Assignment and function declaration
            ),
            "class": re.compile(
                r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
                r'setClass\s*\(\s*["\'](?P<class_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']'  # S4 class definition
            ),
            "method": re.compile(
                r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
                r'setMethod\s*\(\s*["\'](?P<method_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']'  # S4 method definition
            ),
            "constant": re.compile(
                r"^(?P<const_name>[A-Z][A-Z0-9_]*)"  # Constant name
                r"\s*<?-\s*"  # Assignment
            ),
            "variable": re.compile(
                r"^(?P<var_name>[a-z][a-z0-9_.]*)"  # Variable name
                r"\s*<?-\s*(?!function)"  # Assignment, not a function
            ),
            "package": re.compile(
                r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
                r'(?:library|require)\s*\(\s*["\']?(?P<package_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']?\s*\)'  # Package import
            ),
        }

        self.modifiers = {"export"}
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "#"
        self.block_comment_start = None  # R doesn't have block comments
        self.block_comment_end = None

    def parse(self, content: str) -> List[Declaration]:
        """Parse R code content."""
        lines = content.split("\n")
        symbols = []
        brace_count = 0
        current_class = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                i += 1
                continue

            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name_group = f"{kind}_name"
                    name = match.group(name_group)
                    modifiers = set()
                    if "modifiers" in match.groupdict() and match.group("modifiers"):
                        modifiers = {m.strip() for m in match.group("modifiers").split()}

                    # Create symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=i,
                        modifiers=modifiers,
                        parent=current_class,
                    )

                    # Handle block-level constructs
                    if kind in ("function", "class", "method"):
                        # Find the end of the block
                        brace_count = line.count("{")
                        j = i + 1
                        while j < len(lines) and (brace_count > 0 or "{" not in line):
                            line = lines[j].strip()
                            brace_count += line.count("{") - line.count("}")
                            j += 1

                        if j > i + 1:
                            symbol.end_line = j - 1
                            i = j - 1

                        # Update current class context
                        if kind == "class":
                            current_class = symbol

                    symbols.append(symbol)
                    break

            i += 1

        # Convert to Declarations for backward compatibility
        return [
            Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
            for symbol in symbols
        ]


def parse_r(file_path: str, content: str) -> ParsedFileData:
    """Parse R code and return ParsedFileData."""
    parser = RParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path, language="r", content=content, declarations=declarations
    )
