# file: codeconcat/parser/language_parsers/cpp_parser.py

import logging
import re
from typing import List

from ...base_types import Declaration, ParseResult
from .base_parser import BaseParser, LanguageParserError

logger = logging.getLogger(__name__)


def parse_cpp_code(file_path: str, content: str) -> ParseResult:
    parser = CppParser()
    try:
        declarations = parser.parse(content)
    except Exception as e:
        # Wrap internal parser errors in LanguageParserError
        raise LanguageParserError(
            message=f"Failed to parse C++ file: {e}",
            file_path=file_path,
            original_exception=e,
        )
    return ParseResult(
        file_path=file_path, language="cpp", content=content, declarations=declarations
    )


# For backward compatibility
def parse_cpp(file_path: str, content: str) -> ParseResult:
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
                re.MULTILINE | re.DOTALL,
            ),
            "using": re.compile(r"^using\s+(?P<name>\w+)\s*="),
            "enum": re.compile(r"^enum(?:\s+class)?\s+(?P<name>\w+)"),
        }

        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> ParseResult:
        """Parse C++ code using regex patterns to extract declarations and imports.

        Processes the code line by line, attempting to match patterns for:
        - Namespaces (tracks current namespace)
        - Classes/Structs
        - Functions/Methods
        - Typedefs
        - Using directives
        - Enums

        Handles simple brace counting to determine the end line for blocks
        starting with '{'. Also extracts #include directives separately.

        Args:
            content: The C++ code content as a string.

        Returns:
            ParseResult: An object containing:
                - file_path: The path of the parsed file.
                - language: Set to 'cpp'.
                - content: The original file content.
                - declarations: A list of Declaration objects found.
                - imports: A list of strings representing included file paths.
                - token_stats: Currently None (can be added later).
                - security_issues: Currently empty (can be added later).
        """
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
                            children=[],
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
                        children=[],
                    )

                    declarations.append(decl)
                    i = end_line
                    break
            else:
                # This block executes if the inner 'for' loop completes without 'break'
                # Meaning no pattern matched the current line
                if line:  # Avoid logging for comments/empty lines already skipped
                    logger.warning(
                        f"No matching pattern found for line {i + 1}: {line!r}"
                    )
            i += 1

        # Extract includes/imports from the content
        imports = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#include"):
                include_match = re.match(r'#include\s+[<"]([^>"]+)[>"]', line)
                if include_match:
                    imports.append(include_match.group(1))

        logger.debug(
            f"[CppParser] Finished parsing for {self.current_file_path}. Found {len(declarations)} declarations, {len(imports)} imports."
        )

        return ParseResult(
            file_path=self.current_file_path,
            language="cpp",
            content=content,
            declarations=declarations,
            imports=imports,
            token_stats=None,
            security_issues=[],
        )

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
            line = lines[i]

            # remove // inline comment
            comment_pos = line.find("//")
            if comment_pos >= 0:
                line = line[:comment_pos]

            brace_count += line.count("{") - line.count("}")

            if brace_count < 0:  # Found closing brace before matching open
                return i
        # Not found => return last line
        return n - 1

    def _find_class_start(
        self, lines: List[str], start_line: int, class_type: str, name: str
    ) -> int:
        """
        Find the line number where the class definition starts
        """
        for line_num, line_content in enumerate(lines[start_line:], start=start_line):
            if re.match(rf"\s*{class_type}\s+{name}\b", line_content):
                return line_num

    def _find_namespace_start(
        self, lines: List[str], start_line: int, name: str
    ) -> int:
        """
        Find the line number where the namespace definition starts
        """
        for line_num, line_content in enumerate(lines[start_line:], start=start_line):
            if re.match(rf"\s*namespace\s+{name}\b", line_content):
                return line_num
