"""PHP code parser for CodeConcat."""

import re
from typing import List, Optional

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.errors import LanguageParserError

def parse_php(file_path: str, content: str) -> ParseResult:
    """Parse PHP code and return declarations."""
    try:
        parser = PhpParser()
        declarations = parser.parse(content)
        return ParseResult(
            file_path=file_path,
            language="php",
            content=content,
            declarations=declarations
        )
    except Exception as e:
        # Wrap internal parser errors in LanguageParserError
        raise LanguageParserError(
            message=f"Failed to parse PHP file: {e}",
            file_path=file_path,
            original_exception=e
        )


class PhpParser(BaseParser):
    def __init__(self):
        """Initialize PHP parser with regex patterns."""
        super().__init__()
        self.patterns = {
            "namespace": re.compile(r"^namespace\s+(?P<name>[\w\\]+)"),
            "class": re.compile(r"^(?:abstract\s+)?class\s+(?P<name>\w+)"),
            "interface": re.compile(r"^interface\s+(?P<name>\w+)"),
            "trait": re.compile(r"^trait\s+(?P<name>\w+)"),
            "function": re.compile(
                r"^(?:(?:public|private|protected|static|final|abstract)\s+)*"
                r"function\s+(?:&\s*)?(?P<name>\w+)\s*\("
            ),
            "arrow_function": re.compile(r"^\$(?P<name>\w+)\s*=\s*fn\s*\([^)]*\)\s*=>"),
            "property": re.compile(
                r"^(?:(?:public|private|protected|static|final|var)\s+)*"
                r"\$(?P<name>\w+)"
            ),
        }

        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        """Parse PHP code and return declarations."""
        declarations = []
        lines = content.split("\n")
        i = 0
        current_namespace = None
        in_class = False

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("//") or line.startswith("/*"):
                i += 1
                continue

            # Try each pattern
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    if not name:
                        continue

                    # Handle namespaces
                    if kind == "namespace":
                        current_namespace = name
                        decl = Declaration(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=i + 1,
                            modifiers=set(),
                            docstring="",
                            children=[]
                        )
                        declarations.append(decl)
                        i += 1
                        break

                    # Add namespace prefix to name if in a namespace
                    if current_namespace and kind not in ["property"]:
                        name = f"{current_namespace}\\{name}"

                    # Track class context
                    if kind == "class":
                        in_class = True
                    elif line.strip() == "}":
                        in_class = False

                    # Convert arrow functions to regular functions
                    if kind == "arrow_function":
                        kind = "function"

                    # Find end line
                    end_line = i
                    if "{" in line:
                        brace_count = 1
                        j = i + 1
                        while j < len(lines):
                            curr_line = lines[j].strip()
                            if "{" in curr_line:
                                brace_count += curr_line.count("{")
                            if "}" in curr_line:
                                brace_count -= curr_line.count("}")
                                if brace_count == 0:
                                    end_line = j
                                    break
                            j += 1
                    elif ";" in line:
                        end_line = i

                    # Create declaration
                    decl = Declaration(
                        kind=kind,
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(),
                        docstring="",
                        children=[]
                    )

                    declarations.append(decl)
                    i = end_line
                    break
            i += 1

        return declarations
