"""Swift language parser for CodeConCat."""

import logging
import re
from typing import List, Set

from ...base_types import Declaration, ParseResult, ParserInterface
from ...errors import LanguageParserError

logger = logging.getLogger(__name__)


class SwiftParser(ParserInterface):
    """Regex-based Swift parser implementing ParserInterface."""

    def __init__(self):
        """Initialize the Swift parser with regex patterns."""
        # Import patterns for Swift
        self.import_pattern = re.compile(r"^\s*import\s+(\S+)", re.MULTILINE)

        # Typealias and associatedtype patterns
        self.typealias_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate)\s+)*"
            r"typealias\s+([A-Z]\w*)\s*=",
            re.MULTILINE,
        )

        # Subscript patterns
        self.subscript_pattern = re.compile(
            r"^\s*(?:(?:public|private|internal|fileprivate|static)\s+)*"
            r"subscript\s*\([^)]*\)",
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
            imports: Set[str] = set()
            lines = content.split("\n")

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
                    start_line = content[: match.start()].count("\n") + 1

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
                    start_line = content[: match.start()].count("\n") + 1

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
                    start_line = content[: match.start()].count("\n") + 1
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
                start_line = content[: match.start()].count("\n") + 1
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
                    start_line = content[: match.start()].count("\n") + 1

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
                    start_line = content[: match.start()].count("\n") + 1
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
                start_line = content[: match.start()].count("\n") + 1
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
                start_line = content[: match.start()].count("\n") + 1

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

                if f"main_{name}" not in found_declarations:
                    found_declarations.add(f"main_{name}")
                    start_line = content[: match.start()].count("\n") + 1
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

        Simple heuristic: count braces to find matching closing brace.
        """
        content_after = content[start_pos:]
        lines_after = content_after.split("\n")

        brace_count = 0
        found_opening = False

        for i, line in enumerate(lines_after):
            # Count braces, ignoring those in strings/comments
            clean_line = self._remove_strings_and_comments(line)

            if "{" in clean_line:
                found_opening = True
                brace_count += clean_line.count("{")
            if "}" in clean_line:
                brace_count -= clean_line.count("}")

            if found_opening and brace_count == 0:
                return start_line + i

        # If no closing brace found, return start_line + 1
        return start_line + 1

    def _remove_strings_and_comments(self, line: str) -> str:
        """Remove string literals and comments from a line for brace counting."""
        # Remove single-line comments
        if "//" in line:
            line = line[: line.index("//")]

        # Remove string literals (simple approach)
        # This is not perfect but good enough for brace counting
        line = re.sub(r'"[^"]*"', "", line)
        line = re.sub(r"'[^']*'", "", line)

        return line

    def _extract_docstring(self, lines: List[str], decl_line_idx: int) -> str:
        """Extract documentation comments above a declaration.

        Swift uses /// for single-line doc comments and /** */ for multi-line.
        """
        if decl_line_idx < 0:
            return ""

        doc_lines: List[str] = []
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
