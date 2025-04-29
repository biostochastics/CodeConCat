# file: codeconcat/parser/language_parsers/enhanced_php_parser.py

"""
Enhanced PHP parser for CodeConcat.

This module provides an improved PHP parser using the EnhancedBaseParser
with PHP-specific patterns and functionality.
"""

import logging
import re
from typing import Dict, List, Optional, Set

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser

logger = logging.getLogger(__name__)


class EnhancedPHPParser(EnhancedBaseParser):
    """PHP language parser using improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced PHP parser."""
        super().__init__()
        self.language = "php"
        self._setup_php_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns for PHP."""
        super()._setup_standard_patterns()

        # PHP specific comment patterns
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # PHP uses braces for blocks
        self.block_start = "{"
        self.block_end = "}"

        # Initialize patterns dict (will be populated in _setup_php_patterns)
        self.patterns = {}

        # Initialize recognized PHP modifiers
        self.modifiers = {
            "public",
            "private",
            "protected",
            "static",
            "final",
            "abstract",
            "function",
            "class",
            "interface",
            "trait",
            "namespace",
            "use",
            "require",
            "require_once",
            "include",
            "include_once",
            "const",
            "global",
            "var",
            "readonly",
            "fn",
            "async",
        }

    def _setup_php_patterns(self):
        """Setup PHP-specific patterns."""
        # Class declarations
        self.patterns["class"] = re.compile(
            r"^\s*(?:abstract\s+|final\s+)?class\s+(?P<name>\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{",
            re.MULTILINE,
        )

        # Interface declarations
        self.patterns["interface"] = re.compile(
            r"^\s*interface\s+(?P<name>\w+)(?:\s+extends\s+[\w,\s]+)?\s*\{", re.MULTILINE
        )

        # Trait declarations
        self.patterns["trait"] = re.compile(r"^\s*trait\s+(?P<name>\w+)\s*\{", re.MULTILINE)

        # Function declarations
        self.patterns["function"] = re.compile(
            r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+)*function\s+(?P<name>\w+)\s*\(",
            re.MULTILINE,
        )

        # Arrow function declarations (PHP 7.4+)
        self.patterns["arrow_function"] = re.compile(
            r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*fn\s+(?P<name>\w+)\s*\(",
            re.MULTILINE,
        )

        # Method declarations inside classes
        self.patterns["method"] = re.compile(
            r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+)*function\s+(?P<name>\w+)\s*\(",
            re.MULTILINE,
        )

        # Constant declarations
        self.patterns["const"] = re.compile(
            r"^\s*(?:const|define\s*\(\s*[\'\"](?P<name>\w+)[\'\"]\s*,)", re.MULTILINE
        )

        # Property declarations
        self.patterns["property"] = re.compile(
            r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|readonly\s+)*(?:var\s+)?\$(?P<name>\w+)",
            re.MULTILINE,
        )

        # Namespace declarations
        self.patterns["namespace"] = re.compile(r"^\s*namespace\s+(?P<name>[\w\\]+)", re.MULTILINE)

        # Import declarations (use statements)
        self.patterns["use"] = re.compile(
            r"^\s*use\s+(?P<path>[\w\\]+)(?:\s+as\s+(?P<alias>\w+))?", re.MULTILINE
        )

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse PHP code and return a ParseResult object."""
        try:
            logger.debug(f"Starting EnhancedPHPParser.parse for file: {file_path}")

            # Skip if no PHP tags found
            if not any("<?php" in line or "<?=" in line for line in content.split("\n")):
                return ParseResult(
                    file_path=file_path,
                    language=self.language,
                    symbols=[],
                    errors=["No PHP tags found in file"],
                    engine_used="regex",
                )

            declarations = []
            imports = []
            errors = []

            lines = content.split("\n")

            # Process the entire file content recursively
            self._process_block(lines, 0, len(lines) - 1, declarations, imports, errors)

            # Remove duplicates from imports
            imports = list(set(imports))

            logger.debug(
                f"Finished EnhancedPHPParser.parse for file: {file_path}. "
                f"Found {len(declarations)} declarations, {len(imports)} unique imports."
            )

            return ParseResult(
                file_path=file_path,
                language=self.language,
                declarations=declarations,
                imports=imports,
                engine_used="regex",
            )

        except Exception as e:
            logger.error(f"Error parsing PHP file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse PHP file ({type(e).__name__}): {e}"
            errors.append(error_msg)

            # Return partially parsed content with error
            return ParseResult(
                file_path=file_path,
                language=self.language,
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
    ) -> int:
        """
        Process a PHP code block and extract declarations and imports.

        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index (inclusive).
            declarations: List to add declarations to.
            imports: List to add imports to.
            errors: List to add errors to.
            parent_declaration: Parent declaration if processing a nested block.

        Returns:
            Next line index to process.
        """
        i = start
        in_php = False

        # Check if we're already in PHP code (look for PHP tag before this block)
        for j in range(0, start):
            if j < len(lines):
                if "<?php" in lines[j] or "<?=" in lines[j]:
                    in_php = True
                if "?>" in lines[j]:
                    in_php = False

        while i <= end:
            if i >= len(lines):  # Safety check
                break

            line = lines[i].strip()

            # Handle PHP opening/closing tags
            if "<?php" in line or "<?=" in line:
                in_php = True
                i += 1
                continue

            if "?>" in line:
                in_php = False
                i += 1
                continue

            # Only parse PHP code
            if not in_php:
                i += 1
                continue

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Skip single-line comments
            if line.startswith("//") or line.startswith("#"):
                i += 1
                continue

            # Skip block comments
            if line.startswith("/*"):
                while i < len(lines) and "*/" not in lines[i]:
                    i += 1
                i += 1  # Skip the closing comment line
                continue

            # Process imports (use statements)
            if self._process_imports(line, imports):
                i += 1
                continue

            # Try each pattern for declarations
            for kind, pattern in self.patterns.items():
                if kind in ["use"]:  # Already handled separately
                    continue

                match = pattern.match(line)
                if match:
                    # Extract name
                    name = match.group("name") if "name" in match.groupdict() else ""

                    if not name:
                        i += 1
                        continue

                    start_line = i
                    end_line = i
                    docstring_text = ""

                    # Extract PHPDoc comment if present
                    docstring_text = self._extract_phpdoc(lines, i)

                    # For declarations with blocks, find the end
                    block_types = ["class", "interface", "trait", "function", "method"]
                    if kind in block_types:
                        # Look for opening brace on current or next lines
                        has_block = False

                        # Check current line
                        if "{" in line:
                            has_block = True
                            end_line = self._find_block_end_improved(
                                lines, i, open_char="{", close_char="}"
                            )
                        else:
                            # Check next few lines
                            j = i + 1
                            while j < min(i + 5, len(lines)) and not has_block:
                                if "{" in lines[j]:
                                    has_block = True
                                    end_line = self._find_block_end_improved(
                                        lines, j, open_char="{", close_char="}"
                                    )
                                j += 1

                            # Abstract methods in interfaces/abstract classes don't have blocks
                            if (
                                not has_block
                                and ("abstract" in line or "interface" in line)
                                and ";" in line
                            ):
                                end_line = i
                    else:
                        # For simple declarations without blocks, find the next semicolon
                        j = i
                        while j < len(lines) and ";" not in lines[j]:
                            j += 1
                        end_line = j

                    # Normalize function types
                    if kind in ["arrow_function", "method"]:
                        normalized_kind = "function"
                    else:
                        normalized_kind = kind

                    # Extract modifiers
                    modifiers = self._extract_modifiers(line)

                    # Create declaration
                    declaration = Declaration(
                        kind=normalized_kind,
                        name=name,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=docstring_text,
                        modifiers=modifiers,
                    )

                    # Add declaration to parent or top-level list
                    if parent_declaration:
                        if parent_declaration.children is None:
                            parent_declaration.children = []
                        parent_declaration.children.append(declaration)
                        logger.debug(f"Found nested declaration: {normalized_kind} {name}")
                    else:
                        declarations.append(declaration)
                        logger.debug(f"Found declaration: {normalized_kind} {name}")

                    # Process nested blocks (only for container types)
                    if (
                        normalized_kind in ["class", "interface", "trait", "function"]
                        and end_line > start_line
                    ):
                        nested_declarations = []  # Create new list for children
                        # Recursively process the block for nested declarations
                        self._process_block(
                            lines,
                            start_line + 1,
                            end_line - 1,
                            nested_declarations,
                            imports,
                            errors,
                            declaration,
                        )
                        declaration.children = nested_declarations  # Assign children

                    # Move past the block
                    i = end_line + 1
                    break
            else:
                # No pattern matched
                i += 1

        return i

    def _process_imports(self, line: str, imports: List[str]) -> bool:
        """
        Process PHP use statements and add them to the imports list.

        Args:
            line: Line of code to process.
            imports: List to add imports to.

        Returns:
            True if line was a use statement, False otherwise.
        """
        if line.startswith("use "):
            match = self.patterns["use"].match(line)
            if match:
                # Extract the imported path
                path = match.group("path").strip()
                alias = match.group("alias") if "alias" in match.groupdict() else None

                # Handle namespace imports and class imports
                imported_name = path.split("\\")[-1] if "\\" in path else path
                if alias:
                    imports.append(alias)
                else:
                    imports.append(imported_name)

                return True

            # Handle group use statements: use Namespace\{ClassA, ClassB}
            if "{" in line and "}" in line:
                namespace_prefix = line[4 : line.find("{")].strip()
                items = line[line.find("{") + 1 : line.find("}")].split(",")

                for item in items:
                    item = item.strip()
                    if " as " in item:
                        _, alias = item.split(" as ")
                        imports.append(alias.strip())
                    else:
                        class_name = item.split("\\")[-1]
                        imports.append(class_name)

                return True

        return False

    def _extract_phpdoc(self, lines: List[str], current_line: int) -> str:
        """
        Extract PHPDoc comments before a declaration.

        Args:
            lines: List of code lines.
            current_line: Line number of the declaration.

        Returns:
            Extracted PHPDoc as a string.
        """
        if current_line <= 0:
            return ""

        # Look for PHPDoc comment before the current line
        i = current_line - 1

        # Skip blank lines between doc comments and declaration
        while i >= 0 and not lines[i].strip():
            i -= 1

        # Check if we have a PHPDoc comment block
        if i >= 0 and lines[i].strip().endswith("*/"):
            # Find start of the comment block
            end_line = i
            while i >= 0 and "/**" not in lines[i]:
                i -= 1

            if i >= 0 and "/**" in lines[i]:
                start_line = i

                # Extract the comment block
                doc_lines = []
                for j in range(start_line, end_line + 1):
                    line = lines[j].strip()
                    # Remove comment markers and asterisks
                    line = line.replace("/**", "").replace("*/", "")
                    if line.startswith("*"):
                        line = line[1:].strip()
                    doc_lines.append(line)

                return "\n".join(doc_lines).strip()

        return ""

    def _extract_modifiers(self, line: str) -> Set[str]:
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

    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_classes": True,
            "can_parse_interfaces": True,
            "can_parse_traits": True,
            "can_parse_constants": True,
            "can_parse_properties": True,
            "can_parse_namespaces": True,
            "can_parse_imports": True,
            "can_extract_docstrings": True,
        }
