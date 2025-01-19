# file: codeconcat/parser/language_parsers/cpp_parser.py

import re
from typing import List, Optional

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


def parse_cpp_code(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = CppParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path, language="cpp", content=content, declarations=declarations
    )


# For backward compatibility
def parse_cpp(file_path: str, content: str) -> Optional[ParsedFileData]:
    return parse_cpp_code(file_path, content)


class CppParser(BaseParser):
    def __init__(self):
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """
        Define the main regex patterns for classes, structs, enums, functions,
        namespaces, typedefs, usings, and forward declarations.
        """

        identifier = r"[a-zA-Z_]\w*"
        qualified_id = rf"(?:{identifier}::)*{identifier}"

        # Class or struct with a brace => actual definition
        self.class_pattern = re.compile(
            r"""
            ^[^\#/]*?                    # skip if line starts with # or / (comment), handled later
            (?:template\s*<[^>]*>\s*)?   # optional template
            (?:class|struct)\s+
            (?P<name>[a-zA-Z_]\w*)       # capture the class/struct name
            (?:\s*:[^{]*)?              # optional inheritance, up to but not including brace
            \s*{                       # opening brace
            """,
            re.VERBOSE,
        )

        # Forward declaration of class/struct/union/enum without a brace => ends with semicolon
        self.forward_decl_pattern = re.compile(
            r"""
            ^[^\#/]*?
            (?:class|struct|union|enum)\s+
            (?P<name>[a-zA-Z_]\w*)\s*;
            """,
            re.VERBOSE,
        )

        # Enum definition (including "enum class Foo {" or "enum Foo : <type> {")
        self.enum_pattern = re.compile(
            r"""
            ^[^\#/]*?
            enum(?:\s+class)?\s+
            (?P<name>[a-zA-Z_]\w*)
            (?:\s*:\s+[^\s{]+)?         # optional base type
            \s*{                       # opening brace
            """,
            re.VERBOSE,
        )

        # Function pattern
        # Includes optional specs (static, virtual, inline, constexpr, explicit, friend)
        # Optional return types with nested templates, qualifiers, pointers, refs, etc.
        # Then a function name or operator..., then params, optional const/noexcept, then { or ;.
        self.function_pattern = re.compile(
            r"""
            ^[^\#/]*?                    # skip if line starts with # or / (comment), handled later
            (?:template\s*<[^>]*>\s*)?   # optional template
            (?:virtual|static|inline|constexpr|explicit|friend\s+)?  # optional specifiers
            (?:"""
            + qualified_id
            + r"""(?:<[^>]+>)?[&*\s]+)*        # optional return type with nested templates
            (?P<name>                                      # function name capture
                ~?[a-zA-Z_]\w*                             # normal name or destructor ~Foo
                |operator\s*(?:[^\s\(]+|\(.*?\))          # operator overload
            )
            \s*\([^\){;]*\)                                # function params up to ) but not including brace or semicolon
            (?:\s*const)?                                   # optional const
            (?:\s*noexcept)?                                # optional noexcept
            (?:\s*=\s*(?:default|delete|0))?                # optional = default/delete/pure virtual
            \s*(?:{|;)                                    # must end with { or ;
            """,
            re.VERBOSE,
        )

        # Namespace pattern. Also handle "inline namespace" optionally
        self.namespace_pattern = re.compile(
            r"""
            ^[^\#/]*?
            (?:inline\s+)?         # optional inline
            namespace\s+
            (?P<name>[a-zA-Z_]\w*) # namespace name
            \s*{                  # opening brace
            """,
            re.VERBOSE,
        )

        # typedef pattern
        self.typedef_pattern = re.compile(
            r"""
            ^[^\#/]*?
            typedef\s+
            (?:[^;]+?                   # capture everything up to the identifier
              \s+                       # must have whitespace before identifier
              (?:\(\s*\*\s*)?          # optional function pointer
            )
            (?P<name>[a-zA-Z_]\w*)     # identifier
            (?:\s*\)[^;]*)?            # rest of function pointer if present
            \s*;                        # end with semicolon
            """,
            re.VERBOSE,
        )

        # using Foo = ...
        self.using_pattern = re.compile(
            r"""
            ^[^\#/]*?
            using\s+
            (?P<name>[a-zA-Z_]\w*)
            \s*=\s*[^;]+;
            """,
            re.VERBOSE,
        )

        self.patterns = {
            "class": self.class_pattern,
            "forward_decl": self.forward_decl_pattern,
            "enum": self.enum_pattern,
            "function": self.function_pattern,
            "namespace": self.namespace_pattern,
            "typedef": self.typedef_pattern,
            "using": self.using_pattern,
        }

        # Block delimiters, etc.
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        """
        Main parse method:
        1) Remove block comments.
        2) Split by lines.
        3) For each line, strip preprocessor lines (#...), line comments, etc.
        4) Match patterns in a loop and accumulate symbols.
        5) For anything with a block, find the end of the block with _find_block_end.
        6) Convert collected CodeSymbol objects -> Declaration objects.
        """
        # Remove block comments
        content_no_block = self._remove_block_comments(content)
        lines = content_no_block.split("\n")

        symbols: List[CodeSymbol] = []
        i = 0
        line_count = len(lines)

        while i < line_count:
            raw_line = lines[i]
            line_stripped = raw_line.strip()

            # Skip lines that are empty, pure comment, or preprocessor (#)
            if not line_stripped or line_stripped.startswith("//") or line_stripped.startswith("#"):
                i += 1
                continue

            # Also remove inline // comment if any
            comment_pos = raw_line.find("//")
            if comment_pos >= 0:
                raw_line = raw_line[:comment_pos]

            raw_line_stripped = raw_line.strip()
            if not raw_line_stripped:
                i += 1
                continue

            matched_something = False

            # Try each pattern in order
            for kind, pattern in self.patterns.items():
                match = pattern.match(raw_line_stripped)
                if match:
                    name = match.group("name")
                    block_end = i
                    # For these kinds, we do brace-based block scanning
                    if kind in ["class", "enum", "namespace", "function"]:
                        # If it ends with '{', find block end
                        if "{" in raw_line_stripped:
                            block_end = self._find_block_end(lines, i)
                        else:
                            # No brace => presumably forward-decl or prototypes
                            block_end = i

                    # forward_decl, typedef, using don't have braces
                    symbol = CodeSymbol(
                        kind=kind,
                        name=name,
                        start_line=i,
                        end_line=block_end,
                        modifiers=set(),
                    )
                    symbols.append(symbol)
                    i = block_end + 1
                    matched_something = True
                    break

            if not matched_something:
                i += 1

        # Convert symbols to Declaration objects
        declarations: List[Declaration] = []
        for sym in symbols:
            decl = Declaration(
                kind=sym.kind,
                name=sym.name,
                start_line=sym.start_line + 1,
                end_line=sym.end_line + 1,
                modifiers=sym.modifiers,
            )
            declarations.append(decl)

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
