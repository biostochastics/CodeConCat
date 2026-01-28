# file: codeconcat/parser/language_parsers/enhanced_julia_parser.py

"""Enhanced Julia parser for CodeConcat.

This module provides a Julia parser that uses improved regex patterns
and handling of nested declarations for better parsing results.
"""

import logging
import re

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser

logger = logging.getLogger(__name__)


class EnhancedJuliaParser(EnhancedBaseParser):
    """Julia language parser using improved regex patterns and nested structure detection."""

    def __init__(self):
        """Initialize the enhanced Julia parser."""
        super().__init__()
        self.language = "julia"
        self._setup_julia_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns for Julia."""
        super()._setup_standard_patterns()

        # Julia specific comment patterns
        self.line_comment = "#"
        self.block_comment_start = "#="
        self.block_comment_end = "=#"

        # Initialize patterns dict (will be populated in _setup_julia_patterns)
        self.patterns = {}

        # Initialize recognized Julia modifiers
        self.modifiers = {
            "abstract",
            "baremodule",
            "begin",
            "const",
            "export",
            "global",
            "local",
            "macro",
            "mutable",
            "primitive",
            "quote",
            "using",
        }

    def _setup_julia_patterns(self):
        """Setup Julia-specific patterns."""

        # Function pattern (both standard and compact syntax)
        self.patterns["function"] = re.compile(
            r"^\s*(?:function\s+)?(?P<n>[\w.!]+)\s*\([^)]*\)\s*(?:where\s+\{[^}]*\}\s*)?(?::|=|$)",
            re.MULTILINE,
        )

        # Struct pattern
        self.patterns["struct"] = re.compile(
            r"^\s*(?:mutable\s+)?struct\s+(?P<n>[\w]+)(?:\s*\{[^}]*\})?(?:\s*<:\s*[\w.]+)?",
            re.MULTILINE,
        )

        # Module pattern
        self.patterns["module"] = re.compile(r"^\s*(?:bare)?module\s+(?P<n>[\w.]+)", re.MULTILINE)

        # Type pattern
        self.patterns["type"] = re.compile(
            r"^\s*(?:abstract|primitive)\s+type\s+(?P<n>[\w]+)(?:\s*<:\s*[\w.]+)?", re.MULTILINE
        )

        # Macro pattern
        self.patterns["macro"] = re.compile(r"^\s*macro\s+(?P<n>[\w!]+)\s*\([^)]*\)", re.MULTILINE)

        # Compact function assignment (treated as inline function)
        self.patterns["inline_function"] = re.compile(
            r"^\s*(?P<n>[\w.!]+)\s*\([^)]*\)\s*(?:where\s+\{[^}]*\}\s*)?=(?![=>])", re.MULTILINE
        )

        # Import/using pattern
        self.patterns["import"] = re.compile(r"^\s*(?:import|using)\s+(.*?)(?::|$)", re.MULTILINE)

    def _count_nested_declarations(self, declarations):
        """Count the total number of declarations including all nested ones."""
        total = len(declarations)
        for decl in declarations:
            if decl.children:
                total += self._count_nested_declarations(decl.children)
        return total

    def _calculate_max_nesting_depth(self, declarations, current_depth=1):
        """Calculate the maximum nesting depth in the declaration tree."""
        if not declarations:
            return current_depth - 1

        max_depth = current_depth
        for decl in declarations:
            if decl.children:
                child_depth = self._calculate_max_nesting_depth(decl.children, current_depth + 1)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse Julia code and extract declarations, imports, etc.

        Args:
            content: Source code content
            file_path: Path to the file (used for debugging)

        Returns:
            ParseResult: Structured parsing results
        """
        try:
            logger.debug(f"Starting EnhancedJuliaParser.parse for file: {file_path}")

            lines = content.split("\n")
            declarations: list[Declaration] = []
            imports: list[str] = []
            errors: list[str] = []

            # Process the entire file content
            self._process_block(lines, 0, len(lines) - 1, declarations, imports, errors, None)

            # Remove duplicate imports
            imports = list(set(imports))

            # Count nested declarations and calculate max depth
            total_declarations = self._count_nested_declarations(declarations)
            max_depth = self._calculate_max_nesting_depth(declarations)

            logger.debug(
                f"Finished parsing {file_path}: found {len(declarations)} top-level declarations, "
                f"{total_declarations} total declarations (max depth: {max_depth}), "
                f"{len(imports)} unique imports."
            )

            return ParseResult(
                declarations=declarations,
                imports=imports,
                engine_used="regex",
            )

        except Exception as e:
            logger.error(f"Error parsing Julia file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse Julia file ({type(e).__name__}): {e}"

            # Return partially parsed content with error
            return ParseResult(
                declarations=[],
                imports=[],
                error=error_msg,
                engine_used="regex",
            )

    def _process_block(
        self,
        lines: list[str],
        start: int,
        end: int,
        declarations: list[Declaration],
        imports: list[str],
        errors: list[str],
        parent_decl: Declaration | None = None,
    ) -> None:
        """Process a block of Julia code for declarations and imports.

        This is a recursive method that processes blocks of code, including nested blocks.

        Args:
            lines: All lines from the file
            start: Starting line index of the block
            end: Ending line index of the block
            declarations: List to collect declarations
            imports: List to collect imports
            errors: List to collect errors
            parent_decl: Parent declaration, if this is a nested block
        """
        i = start

        logger.debug(f"Processing Julia block from lines {start + 1}-{end + 1}")

        try:
            while i <= end:
                if i >= len(lines):  # Safety check
                    break

                line = lines[i].strip()

                # Skip empty lines and comments
                if not line or (self.line_comment and line.startswith(self.line_comment)):
                    i += 1
                    continue

                # Skip block comments
                if self.block_comment_start and line.startswith(self.block_comment_start):
                    while (
                        i <= end
                        and self.block_comment_end
                        and self.block_comment_end not in lines[i]
                    ):
                        i += 1
                    i += 1
                    continue

                # Process imports
                if self._process_imports(line, imports):
                    i += 1
                    continue

                # Try each pattern
                found_match = False
                for kind, pattern in self.patterns.items():
                    if kind == "import":  # Already handled separately
                        continue

                    match = pattern.match(line)
                    if match:
                        found_match = True
                        # Extract name
                        try:
                            name = match.group("n")
                            if not name:
                                i += 1
                                continue
                        except (IndexError, KeyError):
                            i += 1
                            continue

                        start_line = i + 1  # 1-indexed
                        block_end = i
                        docstring_text: str | None = ""

                        # Extract modifiers
                        modifiers = self._extract_modifiers(line)

                        # Find end line for block structures
                        if kind in ["module", "struct", "function", "macro", "type"]:
                            logger.debug(
                                f"Found {kind} '{name}' at line {start_line}, finding block end..."
                            )
                            block_end = self._find_julia_block_end(lines, i)
                            logger.debug(f"Found end of {kind} '{name}' at line {block_end + 1}")

                            # Extract docstring
                            docstring_text = self.extract_docstring(lines, i, block_end) or ""

                        end_line = block_end + 1  # 1-indexed

                        # Normalize kind
                        normalized_kind = "function" if kind == "inline_function" else kind

                        # Create declaration
                        declaration = Declaration(
                            kind=normalized_kind,
                            name=name,
                            start_line=start_line,
                            end_line=end_line,
                            docstring=docstring_text or "",
                            modifiers=modifiers,
                            children=[],  # Will add children for nested declarations
                        )

                        # Add to parent or top-level declarations
                        if parent_decl is not None:
                            parent_decl.children.append(declaration)
                            logger.debug(
                                f"Added nested declaration to parent {parent_decl.name}: {normalized_kind} {name}"
                            )
                        else:
                            declarations.append(declaration)
                            logger.debug(f"Added top-level declaration: {normalized_kind} {name}")

                        # Process nested blocks for all declaration types that can contain nested code
                        if block_end > i:
                            # Find the content within the block (skip the current line with declaration)
                            inner_start = i + 1
                            inner_end = block_end - 1  # Skip the 'end' line

                            # Only process if there's content to process
                            if inner_end >= inner_start:
                                logger.debug(
                                    f"Processing nested declarations within {normalized_kind} {name} (lines {inner_start + 1}-{inner_end + 1})"
                                )
                                # Recursively process the block for nested declarations
                                self._process_block(
                                    lines=lines,
                                    start=inner_start,
                                    end=inner_end,
                                    declarations=declaration.children,  # Pass the parent's children list directly
                                    imports=imports,
                                    errors=errors,
                                    parent_decl=declaration,
                                )

                        # Move past the block
                        i = block_end + 1
                        break

                if not found_match:
                    # No pattern matched
                    i += 1

            logger.debug(
                f"Finished processing block: Found {len(declarations)} declarations, "
                + (
                    f"{self._count_nested_declarations(declarations)} nested declarations"
                    if declarations
                    else "0 nested declarations"
                )
            )
        except Exception as e:
            logger.error(f"Error processing Julia block: {str(e)}", exc_info=True)
            errors.append(f"Error processing block: {str(e)}")

    def _find_julia_block_end(self, lines: list[str], start: int) -> int:
        """
        Find the end of a Julia code block.

        Julia blocks end with the 'end' keyword, but need to track nesting
        to find the correct end of a given block.

        Args:
            lines: List of code lines.
            start: Start line index.

        Returns:
            Line index of the end of the block.
        """
        j = start + 1
        nesting_level = 1
        block_starters = [
            "module",
            "struct",
            "function",
            "macro",
            "type",
            "begin",
            "for",
            "while",
            "if",
            "let",
            "try",
            "do",
        ]

        # Track string state to avoid matching keywords inside strings
        in_string = False
        string_delim = ""

        while j < len(lines):
            curr_line = lines[j]
            processed_line = curr_line

            # Skip comments
            if self.line_comment and processed_line.strip().startswith(self.line_comment):
                j += 1
                continue

            # Handle block comments
            if self.block_comment_start and processed_line.strip().startswith(
                self.block_comment_start
            ):
                while (
                    j < len(lines)
                    and self.block_comment_end
                    and self.block_comment_end not in lines[j]
                ):
                    j += 1
                j += 1
                continue

            # Simple processing to ignore strings
            # This is a simplified approach that doesn't handle all string edge cases
            # but works for most common code patterns
            tmp_line = ""
            i = 0
            while i < len(processed_line):
                # Skip string content
                if processed_line[i : i + 3] == '"""' and not in_string:
                    in_string = True
                    string_delim = '"""'
                    i += 3
                    continue
                elif processed_line[i : i + 3] == '"""' and in_string and string_delim == '"""':
                    in_string = False
                    string_delim = ""
                    i += 3
                    continue
                elif processed_line[i : i + 1] == '"' and not in_string:
                    in_string = True
                    string_delim = '"'
                    i += 1
                    continue
                elif processed_line[i : i + 1] == '"' and in_string and string_delim == '"':
                    in_string = False
                    string_delim = ""
                    i += 1
                    continue

                # Only add to processed line if not in a string
                if not in_string:
                    tmp_line += processed_line[i]
                i += 1

            processed_line = tmp_line

            # Check for block start keywords
            for word in block_starters:
                if re.search(rf"\b{word}\b", processed_line):
                    nesting_level += 1
                    logger.debug(
                        f"Found nested block start at line {j + 1}, nesting level: {nesting_level}"
                    )

            # Check for 'end' keyword
            if re.search(r"\bend\b", processed_line):
                nesting_level -= 1
                logger.debug(f"Found 'end' at line {j + 1}, nesting level: {nesting_level}")
                if nesting_level == 0:
                    return j

            j += 1

        # Default to the end of the file if no matching 'end' is found
        logger.warning(f"No matching 'end' found for block starting at line {start + 1}")
        return len(lines) - 1

    def _process_imports(self, line: str, imports: list[str]) -> bool:
        """
        Process Julia import statements and add them to the imports list.

        Args:
            line: Line of code to process.
            imports: List to add imports to.

        Returns:
            True if line was an import statement, False otherwise.
        """
        # Check for 'using' and 'import' statements
        using_match = re.match(r"^\s*using\s+(.+?)(?::|$)", line)
        import_match = re.match(r"^\s*import\s+(.+?)(?::|$)", line)

        match = using_match or import_match
        if match:
            modules = match.group(1).split(",")
            for module_str in modules:
                # Parse the module path
                module_path = module_str.strip()

                # Handle 'using Module: Symbol1, Symbol2' syntax
                if ":" in line and module_path:
                    module_path = module_path.split(":")[0].strip()

                # Handle 'using Module.Submodule' syntax
                base_module = module_path.split(".")[0].strip()
                if base_module and base_module not in imports:
                    imports.append(base_module)
                    logger.debug(f"Found import: {base_module}")
            return True

        return False

    def _extract_modifiers(self, line: str) -> set[str]:
        """
        Extract modifiers from a declaration line.

        Args:
            line: Line containing a declaration.

        Returns:
            Set of modifiers found in the line.
        """
        found_modifiers = set()
        for mod in self.modifiers:
            # Use word boundaries to match whole words only
            if re.search(rf"\b{re.escape(mod)}\b", line):
                found_modifiers.add(mod)
        return found_modifiers

    def extract_docstring(self, lines: list[str], start: int, end: int) -> str | None:
        """
        Extract Julia docstring from a block.

        Julia docstrings appear as triple-quoted strings at the start of a block.

        Args:
            lines: List of code lines.
            start: Start line index of the block.
            end: End line index of the block.

        Returns:
            Extracted docstring text, or empty string if none found.
        """
        # Check for docstring in the lines following the declaration
        j = start + 1  # Skip the declaration line
        while j <= end and j < len(lines) and not lines[j].strip():
            j += 1  # Skip empty lines

        if j <= end and j < len(lines):
            line = lines[j].strip()

            # Check for triple-quoted docstring
            if line.startswith('"""'):
                # Extract docstring content
                docstring_lines = []

                # Handle single-line docstring
                if line.endswith('"""') and len(line) > 6:
                    return line[3:-3].strip()

                # Handle multi-line docstring
                docstring_lines.append(line[3:])  # First line without opening quotes

                # Find closing triple quotes
                k = j + 1
                while k <= end and k < len(lines):
                    line = lines[k]
                    if '"""' in line:
                        # Found closing quotes
                        idx = line.find('"""')
                        docstring_lines.append(line[:idx])  # Add text before closing quotes
                        return "\n".join(docstring_lines).strip()

                    docstring_lines.append(line)
                    k += 1

        return ""

    def get_capabilities(self) -> dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_modules": True,
            "can_parse_structs": True,
            "can_parse_imports": True,
            "can_extract_docstrings": True,
            "can_handle_nested_declarations": True,
        }
