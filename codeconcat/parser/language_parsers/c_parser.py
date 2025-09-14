# file: codeconcat/parser/language_parsers/c_parser.py

import logging
import re
from typing import List

from codeconcat.base_types import ParseResult
from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

logger = logging.getLogger(__name__)


def parse_c_code(file_path: str, content: str) -> ParseResult:
    """Parse C code from a given file path and content.
    Parameters:
        - file_path (str): The path of the C file being parsed.
        - content (str): The content of the C file to be parsed.
    Returns:
        - ParseResult: The result of parsing the C code."""
    parser = CParser()
    try:
        result = parser.parse(content, file_path)
    except Exception as e:
        # Wrap internal parser errors in LanguageParserError
        raise LanguageParserError(
            message=f"Failed to parse C file: {e}",
            file_path=file_path,
            original_exception=e,
        ) from e
    return result


class CParser(BaseParser):
    """CParser is a specialized parser for C-like source files, inheriting from BaseParser, designed to identify and process code symbols such as functions, structs, unions, enums, typedefs, and preprocessor defines.
    Parameters:
        - content (str): The content of the source file as a string.
        - file_path (str): The file path of the source file being parsed.
    Processing Logic:
        - Defines patterns for capturing declarations using regular expressions.
        - Ignores lines that are comments or empty when parsing.
        - Identifies block boundaries for code symbols like functions and structs.
        - Logs missing pattern matches for specific declarations like structs and functions."""

    def _setup_patterns(self):
        """
        We define capturing groups: 'name' for declarations.
        """
        # Basic patterns for function, struct, union, enum, typedef, define
        storage = r"(?:static|extern)?\s*"
        inline = r"(?:inline)?\s*"
        type_pattern = r"(?:[a-zA-Z_][\w*\s]+)+"

        self.patterns = {
            "function": re.compile(
                rf"^[^#/]*{storage}{inline}"
                rf"{type_pattern}\s+"
                rf"(?P<name>[a-zA-Z_]\w*)\s*\([^;{{]*"
            ),
            "struct": re.compile(r"^[^#/]*struct\s+(?P<name>[a-zA-Z_]\w*)"),
            "union": re.compile(r"^[^#/]*union\s+(?P<name>[a-zA-Z_]\w*)"),
            "enum": re.compile(r"^[^#/]*enum\s+(?P<name>[a-zA-Z_]\w*)"),
            "typedef": re.compile(
                r"^[^#/]*typedef\s+"
                r"(?:struct|union|enum)?\s*"
                r"(?:[a-zA-Z_][\w*\s]+)*"
                r"(?:\(\s*\*\s*)?"
                r"(?P<name>[a-zA-Z_]\w*)"
                r"(?:\s*\))?"
                r"\s*(?:\([^)]*\))?\s*;"
            ),
            "define": re.compile(r"^[^#/]*#define\s+(?P<name>[A-Z_][A-Z0-9_]*)"),
        }

        # For braces
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse the content of a C-like source file and return a structured parse result.
        Parameters:
            - content (str): The content of the source file as a string.
            - file_path (str): The file path of the source file being parsed.
        Returns:
            - ParseResult: A structured result containing the file path, language, original content, and parsed declarations as a list of code symbols.
        """
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        line_count = len(lines)
        i = 0

        while i < line_count:
            line = lines[i].strip()
            if not line or line.startswith("//"):
                i += 1
                continue

            # Attempt matches
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    # We find potential block ends
                    block_end = i
                    if kind in ["function", "struct", "union", "enum"]:
                        block_end = self._find_block_end(lines, i)

                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=block_end,
                        modifiers=set(),
                    )
                    symbols.append(symbol)
                    i = block_end  # skip to block_end
                    break
            else:
                if "struct" in line:
                    logger.info("No matching pattern found for struct declaration")
                elif "function" in line:
                    logger.info("No matching pattern found for function declaration")
                elif "enum" in line:
                    logger.info("No matching pattern found for enum declaration")
            i += 1

        # Convert CodeSymbol list to Declaration list
        declarations = []
        for symbol in symbols:
            declarations.extend(self._flatten_symbol(symbol))

        return ParseResult(
            file_path=file_path, language="c", content=content, declarations=declarations
        )

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """
        Naive approach: if we see '{', we try to find matching '}'.
        If not found, return start.
        """
        line = lines[start]
        if "{" not in line:
            return start
        brace_count = line.count("{") - line.count("}")
        if brace_count <= 0:
            return start

        for i in range(start + 1, len(lines)):
            l2 = lines[i]
            # skip line comments
            if l2.strip().startswith("//"):
                continue
            brace_count += l2.count("{") - l2.count("}")
            if brace_count <= 0:
                return i
        return len(lines) - 1
