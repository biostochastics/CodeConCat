# file: codeconcat/parser/language_parsers/cpp_parser.py

import re
from typing import List, Optional

from codeconcat.base_types import ParseResult
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol, Declaration


def parse_cpp_code(file_path: str, content: str) -> Optional[ParseResult]:
    parser = CppParser()
    declarations = parser.parse(content)
    return ParseResult(
        file_path=file_path, language="cpp", content=content, declarations=declarations
    )


# For backward compatibility
def parse_cpp(file_path: str, content: str) -> Optional[ParseResult]:
    return parse_cpp_code(file_path, content)


class CppParser(BaseParser):
    """C++ code parser."""

    def __init__(self):
        """Initialize C++ parser with regex patterns."""
        super().__init__()
        self.patterns = {
            "namespace": re.compile(r"^namespace\s+(?P<name>\w+)"),
            "class": re.compile(r"^(?:class|struct)\s+(?P<name>\w+)"),
            "function": re.compile(r"^(?:[\w:]+\s+)?(?P<name>[\w~]+)\s*\([^)]*\)"),
            "typedef": re.compile(
                r"^typedef\s+"  # typedef keyword
                r"(?:"
                r"(?:(?:const\s+)?[^;]+?\s+\*?\s*\(\s*\*\s*(?P<fname>\w+)\s*\)\s*\([^)]*\))|"  # Function pointer
                r"(?:(?:const\s+)?[^;]+?\s+(?P<tname>\w+))"  # Regular typedef
                r")\s*;",
                re.MULTILINE | re.DOTALL
            ),
            "using": re.compile(r"^using\s+(?P<name>\w+)\s*="),
            "enum": re.compile(r"^enum(?:\s+class)?\s+(?P<name>\w+)"),
        }

        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        """Parse C++ code and return declarations."""
        declarations = []
        lines = content.split("\n")
        i = 0
        current_namespace = None

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
                    name = None
                    if kind == "typedef":
                        name = match.group("fname") or match.group("tname")
                        if not name:
                            i += 1
                            continue
                    else:
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
                    if current_namespace and kind not in ["typedef", "using"]:
                        name = f"{current_namespace}::{name}"

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

    def _remove_block_comments(self, text: str) -> str:
        """
        Remove all /* ... */ comments (including multi-line).
        Simple approach: repeatedly find the first /* and the next */, remove them,
        and continue until none remain.
        """
        pattern = re.compile(r"/\*.*?\*/", re.DOTALL)
        return re.sub(pattern, "", text)

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """
        Find the end of a block that starts at 'start' if there's an unmatched '{'.
        We'll count braces until balanced or until we run out of lines.
        We'll skip lines that start with '#' as they are preprocessor directives (not code).
        """
        # Check if there's a brace in the start line
        line = lines[start]
        brace_count = 0

        # remove inline comment
        comment_pos = line.find("//")
        if comment_pos >= 0:
            line = line[:comment_pos]

        brace_count += line.count("{") - line.count("}")

        # If balanced on the same line, return
        if brace_count <= 0:
            return start

        n = len(lines)
        for i in range(start + 1, n):
            l = lines[i]

            # skip preprocessor lines
            if l.strip().startswith("#"):
                continue

            # remove // inline comment
            comment_pos = l.find("//")
            if comment_pos >= 0:
                l = l[:comment_pos]

            brace_count += l.count("{") - l.count("}")
            if brace_count <= 0:
                return i
        # Not found => return last line
        return n - 1

    def _find_class_start(self, lines: List[str], start_line: int, class_type: str, name: str) -> int:
        """
        Find the line number where the class definition starts
        """
        for line_num, line_content in enumerate(lines[start_line:], start=start_line):
            if re.match(rf"\s*{class_type}\s+{name}\b", line_content):
                return line_num

    def _find_namespace_start(self, lines: List[str], start_line: int, name: str) -> int:
        """
        Find the line number where the namespace definition starts
        """
        for line_num, line_content in enumerate(lines[start_line:], start=start_line):
            if re.match(rf"\s*namespace\s+{name}\b", line_content):
                return line_num
