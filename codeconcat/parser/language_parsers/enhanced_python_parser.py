# file: codeconcat/parser/language_parsers/enhanced_python_parser.py

"""Enhanced Python code parser for CodeConcat.

This module provides a Python parser that uses the EnhancedBaseParser and
pattern_library to provide more robust parsing with better error handling
and more consistent behavior across language parsers.
"""

import logging
import re
from typing import Dict, List, Optional

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser
from codeconcat.parser.language_parsers.pattern_library import (
    ClassPatterns,
    FunctionPatterns,
    ImportPatterns,
)

logger = logging.getLogger(__name__)


class EnhancedPythonParser(EnhancedBaseParser):
    """Python language parser using improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced Python parser."""
        super().__init__()
        self.language = "python"
        self._setup_python_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns for Python."""
        super()._setup_standard_patterns()

        # Set comment patterns
        self.line_comment = "#"
        self.block_comment_start = '"""'
        self.block_comment_end = '"""'

        # Python uses indentation rather than braces
        self.block_start = ":"
        self.block_end = ""  # Use indentation

        # Initialize patterns dict (will be populated in _setup_python_patterns)
        self.patterns = {}

        # Initialize recognized modifiers
        self.modifiers = {
            "@classmethod",
            "@staticmethod",
            "@property",
            "@abstractmethod",
            "async",
        }

    def _setup_python_patterns(self):
        """Setup Python-specific patterns."""
        # Use patterns from pattern_library where possible
        self.patterns["class"] = ClassPatterns.PYTHON
        self.patterns["function"] = FunctionPatterns.PYTHON

        # Add Python-specific patterns
        self.patterns["constant"] = re.compile(
            r"^\s*(?P<n>[A-Z][A-Z0-9_\u0080-\uffff]*)\s*"  # Constant name
            r"(?:\s*[^=\s]+)?"  # Optional type annotation
            r"\s*=\s*[^=]",  # Assignment but not comparison
            re.UNICODE | re.MULTILINE,
        )

        self.patterns["variable"] = re.compile(
            r"^\s*(?P<n>[a-z_\u0080-\uffff][\w\u0080-\uffff_]*)\s*"  # Variable name
            r"(?:\s*[^=\s]+)?"  # Optional type annotation
            r"\s*=\s*[^=]",  # Assignment but not comparison
            re.UNICODE | re.MULTILINE,
        )

        # Import patterns
        self.patterns["import"] = ImportPatterns.PYTHON["import"]
        self.patterns["from_import"] = ImportPatterns.PYTHON["from_import"]

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse Python code and return a ParseResult object."""
        try:
            logger.debug(f"Starting EnhancedPythonParser.parse for file: {file_path}")

            declarations: list[Declaration] = []
            imports: list[str] = []
            errors: list[str] = []

            lines = content.split("\n")

            # First pass: extract imports for the entire file
            for _i, line in enumerate(lines):
                line = line.strip()
                self._process_imports(line, imports)

            # Second pass: process declarations with nested structure
            self._process_block(
                lines=lines,
                start=0,
                end=len(lines) - 1,
                declarations=declarations,
                imports=imports,
                errors=errors,
            )

            imports = list(set(imports))  # Remove duplicates

            # Count nested declarations (for logging)
            total_declarations = self._count_total_declarations(declarations)
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
            logger.error(f"Error parsing Python file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse Python file ({type(e).__name__}): {e}"
            errors.append(error_msg)

            # Return partially parsed content with error
            return ParseResult(
                declarations=[],
                imports=[],
                error=error_msg,
                engine_used="regex",
            )

    def _process_block(
        self,
        lines: List[str],
        start: int,
        end: int,
        declarations: List[Declaration],
        imports: List[str],
        errors: List[str],
        parent_declaration: Optional[Declaration] = None,
    ):
        """
        Process a block of code and extract declarations.

        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index.
            declarations: List to add declarations to.
            imports: List to add imports to.
            errors: List to add errors to.
            parent_declaration: Parent declaration if processing a nested block.
        """
        i = start

        # Track the current indentation level for this block
        current_indent = self._get_indent_level(lines[i]) if i < len(lines) else 0

        logger.debug(
            f"Processing Python block at lines {start + 1}-{end + 1} (indent level: {current_indent})"
        )

        while i <= end:
            if i >= len(lines):  # Safety check
                break

            line = lines[i].strip()
            raw_line = lines[i] if i < len(lines) else ""
            line_indent = self._get_indent_level(raw_line)

            # Skip empty lines and simple comments
            if not line or line.startswith("#"):
                i += 1
                continue

            # If indentation is less than the block's indentation, we've exited the block
            if line_indent < current_indent and i > start:
                logger.debug(f"Exiting block at line {i + 1} due to decreased indentation")
                break

            # Process imports
            if self._process_imports(line, imports):
                i += 1
                continue

            # Collect decorators
            decorators: list[str] = []
            while line.startswith("@"):
                decorator = line
                j = i + 1
                while j < len(lines) and "(" in decorator and ")" not in decorator:
                    decorator += " " + lines[j].strip()
                    j += 1
                decorators.append(decorator)
                i = j if j > i else i + 1
                if i >= len(lines):
                    break
                line = lines[i].strip()
                raw_line = lines[i] if i < len(lines) else ""

            # Try each declaration pattern
            declaration_found = False
            for kind, pattern in self.patterns.items():
                # Skip import patterns here (handled separately)
                if kind in ["import", "from_import"]:
                    continue

                match = pattern.match(line)
                if match:
                    # Extract name - handle different group names in patterns
                    name = None
                    for group_name in ["name", "n"]:
                        try:
                            name = match.group(group_name)
                            if name:
                                break
                        except IndexError:
                            continue

                    if not name:
                        continue

                    declaration_found = True
                    start_line = i
                    end_line = i
                    docstring_text = ""

                    logger.debug(f"Found potential {kind} declaration: {name} at line {i + 1}")

                    # Handle block definitions (class, function)
                    if ":" in line:
                        # Calculate the expected indentation of the block body
                        current_line_indent = self._get_indent_level(raw_line)
                        (current_line_indent + 4)  # Python usually uses 4 spaces

                        # Find the end of the block by looking for decreased indentation
                        end_line = i
                        j = i + 1
                        while j <= end and j < len(lines):
                            next_line = lines[j]
                            next_content = next_line.strip()

                            # Skip empty lines and comments when determining block end
                            if not next_content or next_content.startswith("#"):
                                j += 1
                                continue

                            next_indent = self._get_indent_level(next_line)

                            # If indentation decreases to or below current line's level, block ended
                            if next_indent <= current_line_indent:
                                break

                            # Otherwise, this line is part of the block
                            end_line = j
                            j += 1

                        # Extract docstring (if present at start of block)
                        docstring_text = self.extract_docstring(lines, i + 1, end_line) or ""

                        logger.debug(
                            f"Found block for {kind} {name} from lines {start_line + 1} to {end_line + 1}"
                        )

                    # Create declaration
                    declaration = Declaration(
                        kind=kind,
                        name=name,
                        start_line=start_line + 1,  # 1-indexed
                        end_line=end_line + 1,  # 1-indexed
                        docstring=docstring_text,
                        modifiers={d for d in decorators if any(m in d for m in self.modifiers)},
                        children=[],
                    )

                    # Add to parent or top-level declarations
                    if parent_declaration:
                        parent_declaration.children.append(declaration)
                        logger.debug(
                            f"Added nested declaration to parent {parent_declaration.name}: {kind} {name}"
                        )
                    else:
                        declarations.append(declaration)
                        logger.debug(f"Added top-level declaration: {kind} {name}")

                    # Process nested declarations within this block (class or function)
                    if kind in ["class", "function"] and ":" in line and end_line > i:
                        # Process the block body recursively
                        self._process_block(
                            lines=lines,
                            start=i + 1,  # Start after declaration line
                            end=end_line,  # End at the block's end line
                            declarations=[],  # Empty list since we're adding to declaration.children
                            imports=imports,
                            errors=errors,
                            parent_declaration=declaration,  # Pass current declaration as parent
                        )

                    # Move past the processed block
                    i = end_line + 1
                    break

            if not declaration_found:
                # No declaration pattern matched this line
                i += 1

    def _process_imports(self, line: str, imports: List[str]) -> bool:
        """
        Process import statements and add them to the imports list.

        Args:
            line: Line of code to process.
            imports: List to add imports to.

        Returns:
            True if line was an import statement, False otherwise.
        """
        # Handle "import x" statements
        if line.startswith("import "):
            match = self.patterns["import"].match(line)
            if match:
                module_name = match.group("module").strip()
                for name in module_name.split(","):
                    name = name.strip()
                    # Handle "import x as y" by keeping only the original module name
                    if " as " in name:
                        name = name.split(" as ")[0].strip()
                    imports.append(name)
                return True

        # Handle "from x import y" statements
        if line.startswith("from "):
            match = self.patterns["from_import"].match(line)
            if match:
                module_name = match.group("source").strip()
                imports.append(module_name)

                # Optional: Also extract specific imported items
                import_names = match.group("imports").split(",")
                if import_names:
                    for name in import_names:
                        module_name = name.strip().split(" as ")[0]
                        if module_name and module_name != "*":
                            imports.append(module_name.strip())
                return True

        return False

    def extract_docstring(self, lines: List[str], start: int, end: int) -> Optional[str]:
        """
        Extract Python docstring from a block of code.

        Args:
            lines: List of code lines.
            start: Start line index of the block (after the class/function definition).
            end: End line index of the block.

        Returns:
            Extracted docstring text, or empty string if none found.
        """
        # Check for docstring at the start of the block
        if start <= end and start < len(lines):
            # Skip empty lines before docstring
            j = start
            while j <= end and j < len(lines) and not lines[j].strip():
                j += 1

            if j <= end and j < len(lines):
                line = lines[j].strip()

                # Triple-quoted docstring
                if line.startswith('"""') or line.startswith("'''"):
                    quote_type = line[:3]
                    docstring_lines = []

                    # Single-line docstring
                    if line.endswith(quote_type) and len(line) > 3:
                        docstring = line[3:-3].strip()
                        logger.debug(f"Found single-line docstring at line {j + 1}")
                        return docstring

                    # Multi-line docstring
                    docstring_lines.append(line[3:])  # First line without opening quotes
                    k = j + 1
                    while k <= end and k < len(lines):
                        current_line = lines[k]
                        if quote_type in current_line:
                            # Found closing quotes
                            idx = current_line.find(quote_type)
                            docstring_lines.append(
                                current_line[:idx]
                            )  # Add text before closing quotes
                            docstring = "\n".join(docstring_lines).strip()
                            logger.debug(f"Found multi-line docstring from lines {j + 1}-{k + 1}")
                            return docstring
                        docstring_lines.append(current_line)
                        k += 1

                    # If we reached here, the docstring wasn't properly closed
                    logger.warning(f"Unclosed docstring starting at line {j + 1}")

        return ""

    def _count_total_declarations(self, declarations: List[Declaration]) -> int:
        """
        Count the total number of declarations including all nested ones.

        Args:
            declarations: List of top-level declarations.

        Returns:
            Total count of all declarations including nested ones.
        """
        total = len(declarations)
        for decl in declarations:
            if decl.children:
                total += self._count_total_declarations(decl.children)
        return total

    def _calculate_max_nesting_depth(
        self, declarations: List[Declaration], current_depth: int = 1
    ) -> int:
        """
        Calculate the maximum nesting depth in the declaration tree.

        Args:
            declarations: List of declarations to check.
            current_depth: Current depth in the tree.

        Returns:
            Maximum nesting depth found.
        """
        if not declarations:
            return current_depth - 1

        max_depth = current_depth
        for decl in declarations:
            if decl.children:
                child_depth = self._calculate_max_nesting_depth(decl.children, current_depth + 1)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _get_indent_level(self, line: str) -> int:
        """
        Calculate the indentation level of a line.

        Args:
            line: Line of code.

        Returns:
            Number of spaces or equivalent tab spaces at the beginning of the line.
        """
        # Count leading whitespace, with tabs counting as multiple spaces
        indent = 0
        for char in line:
            if char == " ":
                indent += 1
            elif char == "\t":
                # Tabs usually count as multiple spaces
                indent += 4  # Common convention is 4 spaces per tab
            else:
                break
        return indent

    def _extract_python_decorators(self, lines: List[str], i: int) -> List[str]:
        """
        Extract Python decorators preceding a class or function declaration.

        Args:
            lines: List of code lines.
            i: Current line index (pointing to a class or function definition).

        Returns:
            List of decorator strings.
        """
        decorators: list[str] = []
        j = i - 1

        while j >= 0:
            line = lines[j].strip()
            if not line.startswith("@"):
                # Stop if we hit a non-decorator line
                break
            decorators.insert(0, line)
            j -= 1

        logger.debug(f"Found {len(decorators)} decorators for declaration at line {i + 1}")
        return decorators

    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_classes": True,
            "can_parse_imports": True,
            "can_extract_docstrings": True,
            "can_handle_decorators": True,
        }
