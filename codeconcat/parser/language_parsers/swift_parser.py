"""Swift language parser for CodeConCat."""

import bisect
import logging
import re

from ...base_types import Declaration, ParseResult, ParserInterface
from ...errors import LanguageParserError

logger = logging.getLogger(__name__)


class LineMapper:
    """Helper class for efficient line number computation using precomputed newline positions."""

    def __init__(self, content: str):
        """Initialize with content and precompute newline positions."""
        self.content_length = len(content)
        self.newline_positions = [
            -1
        ]  # Start with -1 for line 1 (position 0 is after imaginary newline at -1)
        for i, char in enumerate(content):
            if char == "\n":
                self.newline_positions.append(i)
        # Add the end position for easier computation
        self.newline_positions.append(self.content_length)

    def char_index_to_line(self, char_index: int) -> int:
        """Convert a character index to a 1-based line number in O(log N) time.

        Args:
            char_index: The 0-based character index in the content

        Returns:
            The 1-based line number

        Raises:
            ValueError: If char_index is negative or exceeds content length
        """
        # Validate char_index is within bounds
        if char_index < 0:
            raise ValueError(f"Character index cannot be negative: {char_index}")
        if self.content_length > 0 and char_index > self.content_length:
            raise ValueError(
                f"Character index {char_index} exceeds content length {self.content_length}"
            )

        # Count how many newlines are strictly before char_index
        # This matches the original logic: content[:char_index].count('\n') + 1
        # bisect_left finds the insertion point for char_index to maintain sorted order
        # Since newline_positions starts with -1, the result directly gives us the line number
        line_num = bisect.bisect_left(self.newline_positions[1:], char_index) + 1
        return line_num


class SwiftParser(ParserInterface):
    """Regex-based Swift parser implementing ParserInterface."""

    def __init__(self):
        """Initialize the Swift parser with regex patterns."""
        # Import patterns for Swift
        self.import_pattern = re.compile(r"^\s*import\s+(\S+)", re.MULTILINE)

        # Typealias and associatedtype patterns
        self.typealias_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate)\s+)*" r"typealias\s+([A-Z]\w*)\s*=",
            re.MULTILINE,
        )

        # Subscript patterns
        self.subscript_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate|static)\s+)*" r"subscript\s*\([^)]*\)",
            re.MULTILINE,
        )

        # Class/Struct/Enum/Protocol/Actor/Extension patterns
        self.type_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate|open|final)\s+)*"
            r"(class|struct|enum|protocol|actor|extension)\s+"
            r"([A-Z]\w*(?:<[^>]+>)?)",
            re.MULTILINE,
        )

        # Function/Method patterns (including init, deinit, async/throws)
        self.func_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate|open|static|override|mutating|async|throws|rethrows|@\w+)\s+)*"
            r"(func|init|deinit)\s+([a-zA-Z_]\w*|\()?(?:<[^>]+>)?\s*\([^)]*\)",
            re.MULTILINE,
        )

        # Property patterns (var/let) - improved to handle property wrappers
        self.property_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate|open|static|lazy|weak|unowned|@\w+)\s+)*"
            r"(var|let)\s+([a-zA-Z_]\w*)\s*:",
            re.MULTILINE,
        )

        # Computed property patterns
        self.computed_property_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate|open|static)\s+)*"
            r"var\s+([a-zA-Z_]\w*)\s*:\s*[^{]+\s*\{",
            re.MULTILINE,
        )

        # SwiftUI View patterns
        self.swiftui_view_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate)\s+)*"
            r"struct\s+(\w+)\s*:\s*(?:\w+\s*,\s*)*View",
            re.MULTILINE,
        )

        # Protocol conformance patterns
        self.protocol_conformance_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate|open|final)\s+)*"
            r"(?:class|struct|enum|actor)\s+(\w+)\s*:\s*([^{]+)",
            re.MULTILINE,
        )

        # Operator declaration patterns
        self.operator_pattern = re.compile(
            r"^\s*(?:(?:prefix|infix|postfix)\s+)?operator\s+([^\s{]+)", re.MULTILINE
        )

        # @main attribute pattern (entry point)
        self.main_pattern = re.compile(
            r"^\s*@main\s*\n\s*(struct|class|enum)\s+(\w+)", re.MULTILINE
        )

    def parse(self, content: str, file_path: str = "") -> ParseResult:
        """Parse Swift source code to extract declarations and imports.

        Args:
            content: The Swift source code as a string
            file_path: Optional path to the file being parsed

        Returns:
            ParseResult containing declarations and imports
        """
        try:
            declarations = []
            imports: set[str] = set()
            lines = content.split("\n")

            # Precompute line number mapping for O(log N) lookups
            line_mapper = LineMapper(content)

            # Extract imports
            for match in self.import_pattern.finditer(content):
                imports.add(match.group(1))

            # Track what we've already found to avoid duplicates
            found_declarations = set()

            # Extract typealiases
            for match in self.typealias_pattern.finditer(content):
                name = match.group(1)
                if name not in found_declarations:
                    found_declarations.add(name)
                    start_line = line_mapper.char_index_to_line(match.start())

                    declarations.append(
                        Declaration(
                            kind="typealias",
                            name=name,
                            start_line=start_line,
                            end_line=start_line,
                            modifiers={"typealias"},
                            docstring=self._extract_docstring(lines, start_line - 1),
                        )
                    )

            # Extract type declarations (classes, structs, enums, protocols, actors, extensions)
            for match in self.type_pattern.finditer(content):
                kind = match.group(1)
                name = match.group(2)

                if name not in found_declarations:
                    found_declarations.add(name)
                    start_line = line_mapper.char_index_to_line(match.start())

                    # Find the end of the declaration (simple heuristic)
                    end_line = self._find_block_end(content, match.start(), start_line)

                    # Extract any documentation comments above the declaration
                    docstring = self._extract_docstring(lines, start_line - 1)

                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=start_line,
                            end_line=end_line,
                            modifiers={kind},
                            docstring=docstring,
                        )
                    )

            # Extract SwiftUI Views (special handling)
            for match in self.swiftui_view_pattern.finditer(content):
                name = match.group(1)
                if name not in found_declarations:
                    found_declarations.add(name)
                    start_line = line_mapper.char_index_to_line(match.start())
                    end_line = self._find_block_end(content, match.start(), start_line)
                    docstring = self._extract_docstring(lines, start_line - 1)

                    declarations.append(
                        Declaration(
                            kind="struct",
                            name=name,
                            start_line=start_line,
                            end_line=end_line,
                            modifiers={"struct", "View"},
                            docstring=docstring,
                        )
                    )

            # Extract functions and methods
            for match in self.func_pattern.finditer(content):
                func_type = match.group(1)  # 'func', 'init', or 'deinit'
                func_name = match.group(2) if match.group(2) else func_type

                # For init/deinit, the name is the type itself
                if func_type in ["init", "deinit"]:
                    func_name = func_type

                # Create unique identifier for deduplication
                start_line = line_mapper.char_index_to_line(match.start())
                func_id = f"{func_name}_{start_line}"

                if func_id not in found_declarations:
                    found_declarations.add(func_id)
                    end_line = self._find_block_end(content, match.start(), start_line)
                    docstring = self._extract_docstring(lines, start_line - 1)

                    kind_mapping = {
                        "func": "function",
                        "init": "initializer",
                        "deinit": "deinitializer",
                    }
                    declarations.append(
                        Declaration(
                            kind=kind_mapping.get(func_type, "function"),
                            name=func_name,
                            start_line=start_line,
                            end_line=end_line,
                            modifiers={kind_mapping.get(func_type, "function")},
                            docstring=docstring,
                            signature=match.group(0).strip(),
                        )
                    )

            # Extract properties
            for match in self.property_pattern.finditer(content):
                prop_type = match.group(1)  # 'var' or 'let'
                prop_name = match.group(2)

                prop_id = f"prop_{prop_name}"
                if prop_id not in found_declarations:
                    found_declarations.add(prop_id)
                    start_line = line_mapper.char_index_to_line(match.start())

                    declarations.append(
                        Declaration(
                            kind="property",
                            name=prop_name,
                            start_line=start_line,
                            end_line=start_line,  # Properties are usually single line
                            modifiers={"property", prop_type},
                            docstring="",
                        )
                    )

            # Extract computed properties
            for match in self.computed_property_pattern.finditer(content):
                prop_name = match.group(1)

                comp_prop_id = f"computed_{prop_name}"
                if comp_prop_id not in found_declarations:
                    found_declarations.add(comp_prop_id)
                    start_line = line_mapper.char_index_to_line(match.start())
                    end_line = self._find_block_end(content, match.start(), start_line)
                    docstring = self._extract_docstring(lines, start_line - 1)

                    declarations.append(
                        Declaration(
                            kind="computed_property",
                            name=prop_name,
                            start_line=start_line,
                            end_line=end_line,
                            modifiers={"property", "computed"},
                            docstring=docstring,
                        )
                    )

            # Extract subscripts
            for match in self.subscript_pattern.finditer(content):
                start_line = line_mapper.char_index_to_line(match.start())
                sub_id = f"subscript_{start_line}"

                if sub_id not in found_declarations:
                    found_declarations.add(sub_id)
                    end_line = self._find_block_end(content, match.start(), start_line)
                    docstring = self._extract_docstring(lines, start_line - 1)

                    declarations.append(
                        Declaration(
                            kind="subscript",
                            name="subscript",
                            start_line=start_line,
                            end_line=end_line,
                            modifiers={"subscript"},
                            docstring=docstring,
                            signature=match.group(0).strip(),
                        )
                    )

            # Extract operators
            for match in self.operator_pattern.finditer(content):
                op_name = match.group(1)
                start_line = line_mapper.char_index_to_line(match.start())

                declarations.append(
                    Declaration(
                        kind="operator",
                        name=op_name,
                        start_line=start_line,
                        end_line=start_line,
                        modifiers={"operator"},
                        docstring="",
                    )
                )

            # Extract @main entry points
            for match in self.main_pattern.finditer(content):
                kind = match.group(1)
                name = match.group(2)

                main_id = f"main_{name}"
                if main_id not in found_declarations:
                    found_declarations.add(main_id)
                    start_line = line_mapper.char_index_to_line(match.start())
                    end_line = self._find_block_end(content, match.start(), start_line)

                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=start_line,
                            end_line=end_line,
                            modifiers={kind, "main"},
                            docstring=self._extract_docstring(lines, start_line - 1),
                        )
                    )

            logger.debug(
                f"Parsed Swift file {file_path}: {len(declarations)} declarations, {len(imports)} imports"
            )

            return ParseResult(
                declarations=declarations,
                imports=sorted(imports),
                engine_used="regex",
                file_path=file_path,
                language="swift",
                content=content,
            )

        except Exception as e:
            logger.error(f"Error parsing Swift file {file_path}: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse Swift file: {e}",
                file_path=file_path,
                original_exception=e,
            ) from e

    def _find_block_end(self, content: str, start_pos: int, start_line: int) -> int:
        """Find the end line of a code block starting from a position.

        Simple heuristic: count braces to find matching closing brace,
        properly handling multi-line comments and strings.
        """
        content_after = content[start_pos:]

        # Remove all comments and strings from the content to get clean code
        clean_content = self._remove_all_strings_and_comments(content_after)
        lines_after = clean_content.split("\n")

        brace_count = 0
        found_opening = False

        for i, line in enumerate(lines_after):
            if "{" in line:
                found_opening = True
                brace_count += line.count("{")
            if "}" in line:
                brace_count -= line.count("}")

            if found_opening and brace_count == 0:
                return start_line + i

        # If no closing brace found, return start_line + 1
        return start_line + 1

    def _remove_all_strings_and_comments(self, content: str) -> str:
        """Remove all string literals and comments from content for accurate brace counting.

        This handles multi-line block comments properly by processing the entire content
        at once rather than line by line.
        """
        # Remove string literals first to avoid mis-identifying comment markers inside them
        # Handle double-quoted strings with escape sequences
        content = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', "", content)
        # Handle single-quoted strings (characters) with escape sequences
        content = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "", content)

        # Remove multi-line string literals (triple quotes)
        content = re.sub(r'"""[\s\S]*?"""', "", content)

        # Remove block comments (/* ... */) - using DOTALL flag to match across lines
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

        # Remove single-line comments (// ...) - match from // to end of line
        content = re.sub(r"//[^\n]*", "", content)

        return content

    def _remove_strings_and_comments(self, line: str) -> str:
        """Remove string literals and comments from a single line.

        Note: This method only handles single-line constructs. For proper handling
        of multi-line block comments, use _remove_all_strings_and_comments on the
        entire content instead.
        """
        # Remove string literals first to avoid mis-identifying '//' inside them as comments
        line_without_strings = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', "", line)
        line_without_strings = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "", line_without_strings)

        # Remove single-line block comments (/* ... */ on same line only)
        line_without_strings = re.sub(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", "", line_without_strings)

        # Remove single-line comments
        if "//" in line_without_strings:
            line_without_strings = line_without_strings.split("//", 1)[0]

        return line_without_strings

    def _extract_docstring(self, lines: list[str], decl_line_idx: int) -> str:
        """Extract documentation comments above a declaration.

        Swift uses /// for single-line doc comments and /** */ for multi-line.
        """
        if decl_line_idx < 0:
            return ""

        doc_lines: list[str] = []
        i = decl_line_idx

        # Look backwards for documentation comments
        while i >= 0:
            line = lines[i].strip()

            # Single-line doc comment
            if line.startswith("///"):
                doc_lines.insert(0, line[3:].strip())
                i -= 1
            # Multi-line doc comment end
            elif line.endswith("*/"):
                # Find the start of the multi-line comment
                for j in range(i, -1, -1):
                    if "/**" in lines[j]:
                        # Extract the multi-line comment
                        for k in range(j, i + 1):
                            comment_line = lines[k].strip()
                            if comment_line.startswith("/**"):
                                comment_line = comment_line[3:].strip()
                            elif comment_line.endswith("*/"):
                                comment_line = comment_line[:-2].strip()
                            elif comment_line.startswith("*"):
                                comment_line = comment_line[1:].strip()
                            if comment_line:
                                doc_lines.append(comment_line)
                        break
                break
            # Not a doc comment, stop looking
            elif line and not line.startswith("//"):
                break
            else:
                i -= 1

        return "\n".join(doc_lines)
