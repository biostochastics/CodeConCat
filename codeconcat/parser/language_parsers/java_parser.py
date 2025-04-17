# file: codeconcat/parser/language_parsers/java_parser.py

import re
from typing import List, Optional

from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.base_parser import BaseParser, Declaration, ParseResult


def parse_java(file_path: str, content: str) -> ParseResult:
    parser = JavaParser()
    try:
        declarations = parser.parse(content)
    except Exception as e:
        # Wrap internal parser errors in LanguageParserError
        raise LanguageParserError(
            message=f"Failed to parse Java file: {e}", file_path=file_path, original_exception=e
        )
    return ParseResult(
        file_path=file_path, language="java", content=content, declarations=declarations
    )


class JavaParser(BaseParser):
    def __init__(self):
        """Initialize Java parser with regex patterns."""
        super().__init__()
        self.patterns = {
            "class": re.compile(
                r"^(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+)*class\s+(?P<name>\w+)"
            ),
            "interface": re.compile(
                r"^(?:public\s+|private\s+|protected\s+|static\s+)*interface\s+(?P<name>\w+)"
            ),
            "method": re.compile(
                r"^(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+)*(?:[\w<>[\],\s]+\s+)?(?P<name>\w+)\s*\([^)]*\)"
            ),
            "field": re.compile(
                r"^(?:public\s+|private\s+|protected\s+|static\s+|final\s+|volatile\s+|transient\s+)*(?:[\w<>[\],\s]+\s+)(?P<name>\w+)\s*(?:=|;)"
            ),
        }

    def parse(self, content: str) -> List[Declaration]:
        """Parse Java code and return declarations."""
        declarations = []
        lines = content.split("\n")
        i = 0
        current_class = None

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

                    # Extract modifiers
                    modifiers = set()
                    for mod in ["public", "private", "protected", "static", "final", "abstract"]:
                        if f"{mod} " in line:
                            modifiers.add(mod)

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
                        start_line=i + 1,  # Convert to 1-based line numbers
                        end_line=end_line + 1,
                        modifiers=modifiers,
                        docstring="",
                        children=[],
                    )

                    # For classes and interfaces, parse their members
                    if kind in ["class", "interface"]:
                        current_class = decl
                        declarations.append(decl)
                        i = end_line
                    else:
                        if current_class is not None:
                            current_class.children.append(decl)
                        else:
                            declarations.append(decl)
                        i = end_line
                    break
            i += 1

        return declarations

    def extract_docstring(self, lines, start, end):
        """Extract docstring from Java code."""
        docstring = ""
        for line in lines[start + 1 : end]:
            if line.strip().startswith("//"):
                docstring += line.strip().replace("//", "", 1).strip() + "\n"
        return docstring.strip()
