# file: codeconcat/parser/language_parsers/enhanced_rust_parser.py

"""
Enhanced Rust parser for CodeConcat.

This module provides an improved Rust parser using the EnhancedBaseParser
with Rust-specific patterns and functionality, including improved handling
of nested declarations such as functions, closures, and trait implementations.
"""

import logging
import re
from typing import Dict, List, Optional

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser

logger = logging.getLogger(__name__)


class EnhancedRustParser(EnhancedBaseParser):
    """Rust language parser using improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced Rust parser."""
        super().__init__()
        self.language = "rust"
        self._setup_rust_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns for Rust."""
        super()._setup_standard_patterns()

        # Rust specific comment patterns
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # Rust uses braces for blocks
        self.block_start = "{"
        self.block_end = "}"

        # Initialize patterns dict (will be populated in _setup_rust_patterns)
        self.patterns = {}

        # Initialize recognized Rust modifiers (converted to a frozenset for faster lookups)
        self.modifiers = frozenset(
            {
                "pub",
                "fn",
                "struct",
                "enum",
                "trait",
                "impl",
                "const",
                "static",
                "unsafe",
                "extern",
                "async",
                "move",
                "mut",
                "ref",
                "crate",
                "self",
                "super",
                "dyn",
                "abstract",
                "final",
                "override",
                "macro_rules",
            }
        )

    def _setup_rust_patterns(self):
        """Setup Rust-specific patterns with improved recognition of nested declarations."""
        # Function declarations (improved to match nested functions and closures)
        self.patterns["function"] = re.compile(
            r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(?P<n>\w+)\s*(?:<[^>]*>)?\s*\(", re.MULTILINE
        )

        # Nested function declarations (for fn inside other blocks)
        self.patterns["nested_function"] = re.compile(
            r"^\s*fn\s+(?P<n>\w+)\s*(?:<[^>]*>)?\s*\(", re.MULTILINE
        )

        # Method declarations (in impl blocks)
        self.patterns["method"] = re.compile(
            r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(?P<n>\w+)\s*(?:<[^>]*>)?\s*\(&(?:mut\s+)?self",
            re.MULTILINE,
        )

        # Closure patterns (handle |args| {body} style closures)
        self.patterns["closure"] = re.compile(
            r"^\s*(?:let\s+)?(?P<n>\w+)\s*=\s*(?:move\s+)?\|[^\|]*\|\s*[{]?", re.MULTILINE
        )

        # Struct declarations
        self.patterns["struct"] = re.compile(
            r"^\s*(?:pub\s+)?struct\s+(?P<n>\w+)(?:<[^>]*>)?(?:\s*\{|\s*\([^)]*\);|\s*;)",
            re.MULTILINE,
        )

        # Enum declarations
        self.patterns["enum"] = re.compile(
            r"^\s*(?:pub\s+)?enum\s+(?P<n>\w+)(?:<[^>]*>)?\s*\{", re.MULTILINE
        )

        # Trait declarations
        self.patterns["trait"] = re.compile(
            r"^\s*(?:pub\s+)?trait\s+(?P<n>\w+)(?:<[^>]*>)?(?:\s*:\s*[^{]+)?\s*\{", re.MULTILINE
        )

        # Implementation blocks
        self.patterns["impl"] = re.compile(
            r"^\s*impl(?:<[^>]*>)?\s+(?!<)(?P<n>[^{<]+)(?:<[^>]*>)?\s*(?:for\s+[^{]+)?\s*\{",
            re.MULTILINE,
        )

        # Constant declarations
        self.patterns["const"] = re.compile(
            r"^\s*(?:pub\s+)?(?:const|static)\s+(?P<n>\w+)\s*:", re.MULTILINE
        )

        # Import declarations (use statements)
        self.patterns["use"] = re.compile(r"^\s*use\s+(?P<path>[^;]+);", re.MULTILINE)

        # Macro declarations
        self.patterns["macro"] = re.compile(r"^\s*macro_rules!\s+(?P<n>\w+)", re.MULTILINE)

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
        """Parse Rust code and return a ParseResult object."""
        try:
            logger.debug(f"Starting EnhancedRustParser.parse for file: {file_path}")

            declarations = []
            imports = []
            errors = []

            lines = content.split("\n")

            # Process the entire file content recursively
            self._process_block(lines, 0, len(lines) - 1, declarations, imports, errors)

            # Remove duplicates from imports
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
            logger.error(f"Error parsing Rust file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse Rust file ({type(e).__name__}): {e}"
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
        max_nesting_depth: int = 20,  # Add max nesting depth to prevent infinite recursion
        current_depth: int = 1,  # Track current nesting depth
    ) -> int:
        """
        Process a Rust code block and extract declarations and imports.

        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index (inclusive).
            declarations: List to add declarations to.
            imports: List to add imports to.
            errors: List to add errors to.
            parent_declaration: Parent declaration if processing a nested block.
            max_nesting_depth: Maximum allowed nesting depth to prevent infinite recursion.
            current_depth: Current nesting depth being processed.

        Returns:
            Next line index to process.
        """
        i = start

        # Safety check to prevent stack overflow from infinite recursion
        if current_depth > max_nesting_depth:
            logger.warning(
                f"Maximum nesting depth ({max_nesting_depth}) reached. Stopping further nested parsing."
            )
            return end

        logger.debug(f"Processing Rust block from lines {start+1}-{end+1} at depth {current_depth}")

        # Initialize line counter for safety
        line_counter = 0
        max_line_iterations = 10000  # Prevent infinite loops

        while i <= end and line_counter < max_line_iterations:
            line_counter += 1
            if i >= len(lines):  # Safety check
                break

            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Skip commented lines (but not docstring comments)
            if line.startswith("//") and not (line.startswith("///") or line.startswith("//!")):
                i += 1
                continue

            # Skip block comments
            if line.startswith("/*"):
                comment_counter = 0
                max_comment_iterations = 1000  # Prevent infinite loops
                while (
                    i < len(lines)
                    and "*/" not in lines[i]
                    and comment_counter < max_comment_iterations
                ):
                    comment_counter += 1
                    i += 1
                if i < len(lines):  # Check bounds before incrementing
                    i += 1  # Skip the closing comment line
                continue

            # Process imports
            if self._process_imports(line, imports):
                i += 1
                continue

            # Try each pattern for declarations
            found_match = False

            for kind, pattern in self.patterns.items():
                # Skip import patterns here (handled separately)
                if kind == "use":
                    continue

                match = pattern.match(line)
                if match:
                    found_match = True

                    # Extract name
                    name = None
                    try:
                        name = match.group("n")
                        if name:
                            name = name.strip()  # Ensure name is cleaned from whitespace
                    except (IndexError, KeyError):
                        if kind == "impl":
                            # For impl blocks, we need special handling
                            try:
                                impl_text = match.group(0)
                                # Extract what's between "impl" and "{"
                                parts = impl_text.split("{")
                                if len(parts) > 1:
                                    name_part = parts[0][4:].strip()  # Remove 'impl'
                                    # Remove generic parameters and 'for' clause if present
                                    if "for" in name_part:
                                        name_part = name_part.split("for")[0].strip()
                                    # Remove generic parameters
                                    if "<" in name_part and ">" in name_part:
                                        # This is a rough approximation; handling nested generics properly would need a parser
                                        name_part = re.sub(r"<[^>]+>", "", name_part)
                                    name = name_part.strip()
                            except Exception as e:
                                logger.debug(f"Error extracting impl name: {e}")

                    if not name:
                        i += 1
                        continue

                    start_line = i + 1  # 1-indexed
                    end_line = i + 1  # Default end line
                    end_line_idx = i  # Default end line index (0-based)
                    docstring_text = self._extract_rust_docstring(lines, i)

                    # Find the end of the block if necessary
                    block_found = False
                    requires_block_end_find = kind in [
                        "function",
                        "nested_function",
                        "method",
                        "struct",
                        "enum",
                        "trait",
                        "impl",
                        "macro",
                        "closure",
                    ]

                    if requires_block_end_find:
                        # Check if the declaration line indicates a block opening
                        has_block_opener = "{" in line[match.end() :] or (
                            i + 1 < len(lines) and lines[i + 1].strip().startswith("{")
                        )

                        if has_block_opener:
                            block_found = True
                            try:
                                # Use the improved function to find the block end index (0-based)
                                calculated_end_idx = self._find_block_end_improved(lines, i)
                                if calculated_end_idx != -1:
                                    end_line_idx = calculated_end_idx
                                    end_line = (
                                        end_line_idx + 1
                                    )  # Convert 0-indexed to 1-indexed for Declaration
                                else:
                                    # Log error if block end not found and estimate
                                    logger.warning(
                                        f"Could not find matching }} for {{ at line {i+1}. Declaration: {kind} {name}"
                                    )
                                    end_line_idx = min(i + 49, len(lines) - 1)  # Estimate index
                                    end_line = end_line_idx + 1
                            except Exception as e:
                                logger.error(
                                    f"Error finding block end for {kind} {name} at line {i+1}: {e}",
                                    exc_info=True,
                                )
                                end_line_idx = min(i + 9, len(lines) - 1)  # Fallback index
                                end_line = end_line_idx + 1
                        # Handle cases like 'struct Point;' or 'enum Option<T>;' which match pattern but don't have '{'
                        elif ";" in line:
                            end_line_idx = i
                            end_line = i + 1
                        # Add other conditions for non-block declarations if needed
                        # else: pass # Assumes single line if no '{' or ';'

                    # Fallback for simple declarations or those without detected blocks/semicolons
                    if not requires_block_end_find or (
                        requires_block_end_find and not block_found and ";" not in line
                    ):
                        end_line_idx = i
                        end_line = i + 1

                    # Safety check for end_line (ensure it's at least start_line)
                    if end_line < start_line:
                        logger.warning(
                            f"Corrected invalid end_line {end_line} for {kind} {name} at L{start_line}, setting end to {start_line}"
                        )
                        end_line = start_line
                        end_line_idx = start_line - 1  # Adjust index accordingly
                    # Safety check: ensure end_line_idx doesn't exceed bounds (can happen with estimates)
                    end_line_idx = min(end_line_idx, len(lines) - 1)
                    end_line = min(end_line, len(lines))

                    # Extract modifiers
                    modifiers = self._extract_modifiers(line)

                    # Normalize kinds
                    normalized_kind = kind
                    if kind == "nested_function":
                        normalized_kind = "function"

                    # Create declaration
                    declaration = Declaration(
                        kind=normalized_kind,
                        name=name,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=docstring_text,
                        modifiers=modifiers,
                        children=[],  # Initialize with empty list
                    )

                    # Add declaration to parent or top-level list
                    if parent_declaration:
                        parent_declaration.children.append(declaration)
                        logger.debug(
                            f"Added nested declaration to parent {parent_declaration.name}: {normalized_kind} {name}"
                        )
                    else:
                        declarations.append(declaration)
                        logger.debug(f"Added top-level declaration: {normalized_kind} {name}")

                    # Process nested declarations if it was a block and the range is valid
                    if block_found and end_line_idx > i:
                        nested_start_idx = i + 1  # Line index after the opening declaration line
                        nested_end_idx = (
                            end_line_idx - 1
                        )  # Line index before the closing brace line

                        # Ensure the calculated range for nested processing is valid
                        if nested_start_idx <= nested_end_idx:
                            logger.debug(
                                f"Processing nested declarations within {kind} {name} (lines {nested_start_idx+1}-{nested_end_idx+1})"
                            )
                            # RECURSIVE CALL - Pass the current declaration as the parent
                            self._process_block(
                                lines,
                                nested_start_idx,
                                nested_end_idx,
                                declarations,  # Pass same list, nested decls added via parent
                                imports,
                                errors,
                                parent_declaration=declaration,  # Pass current as parent
                                max_nesting_depth=max_nesting_depth,
                                current_depth=current_depth + 1,
                            )
                            logger.debug(
                                f"Nested processing completed for {kind} {name} at line {end_line}"
                            )
                        else:
                            logger.debug(
                                f"Skipping nested processing for {kind} {name} due to invalid range ({nested_start_idx+1}-{nested_end_idx+1})"
                            )

                    # Advance 'i' past the current declaration block (or single line)
                    i = end_line_idx + 1
                    continue  # Go to next iteration of the main loop

            if not found_match:
                # No pattern matched
                i += 1

        # Safety check for infinite loop
        if line_counter >= max_line_iterations:
            logger.warning(
                f"Possible infinite loop detected in _process_block at lines {start+1}-{end+1}"
            )
            return end

        # Return the next line index to process after the loop finishes
        return i

    def _find_block_end_improved(
        self,
        lines: List[str],
        start: int,
        open_char: str = "{",
        close_char: str = "}",
        max_lines: int = 1000,
    ) -> int:
        """
        Find the matching closing character for a block.

        Args:
            lines: List of code lines.
            start: Starting line index containing the opening character.
            open_char: Opening character of the block.
            close_char: Closing character of the block.
            max_lines: Maximum number of lines to search to prevent infinite loops.

        Returns:
            Line index of the closing character.
        """
        # Safety check for invalid input
        if start < 0 or start >= len(lines):
            logger.warning(f"Invalid start line index {start} for _find_block_end_improved")
            return start

        nesting_level = 0
        in_string = False
        in_char = False
        in_raw_string = False
        string_delimiter = None
        col_start = -1

        # Find the opening character on the start line
        for col, char in enumerate(lines[start]):
            if char == "r" and col + 1 < len(lines[start]) and lines[start][col + 1] == '"':
                # Raw string in Rust (r"...")
                in_raw_string = True
                col += 1  # Skip the next character (the quote)
                continue

            if char == open_char and not in_string and not in_char and not in_raw_string:
                nesting_level = 1
                col_start = col
                break

        # If opening character not found, return start line
        if nesting_level == 0 or col_start < 0:
            return start

        # Starting from the position after the opening character
        i = start
        col = col_start + 1 if i == start else 0

        # Add a safety limit to prevent infinite loops
        max_end_line = min(start + max_lines, len(lines))

        try:
            iterations = 0  # Track iterations to prevent infinite loops
            max_iterations = 10000  # Maximum iterations allowed

            while (
                i < max_end_line and nesting_level > 0 and iterations < max_iterations
            ):  # Only continue while nesting level > 0
                iterations += 1
                if i >= len(lines):
                    break

                line = lines[i]

                while col < len(line):
                    char = line[col]
                    prev_char = line[col - 1] if col > 0 else None

                    # Handle raw strings in Rust
                    if (
                        char == "r"
                        and col + 1 < len(line)
                        and line[col + 1] == '"'
                        and not in_string
                        and not in_char
                    ):
                        in_raw_string = True
                        col += 1  # Skip the quote character
                    elif in_raw_string and char == '"' and prev_char != "\\":
                        in_raw_string = False

                    # Handle regular string literals (only if not in raw string)
                    elif char == '"' and not in_char and not in_raw_string:
                        escaped = prev_char == "\\" and col > 0
                        if not escaped:
                            if not in_string:
                                in_string = True
                                string_delimiter = '"'
                            elif string_delimiter == '"':
                                in_string = False
                                string_delimiter = None

                    # Handle character literals (only if not in string or raw string)
                    elif char == "'" and not in_string and not in_raw_string:
                        escaped = prev_char == "\\" and col > 0
                        if not escaped:
                            if not in_char:
                                in_char = True
                            else:
                                in_char = False

                    # Skip line comments (only if not in any kind of string/char literal)
                    elif (
                        char == "/"
                        and col + 1 < len(line)
                        and line[col + 1] == "/"
                        and not in_string
                        and not in_char
                        and not in_raw_string
                    ):
                        # Found a line comment, skip to the end of this line
                        break

                    # Handle block comments
                    elif (
                        char == "/"
                        and col + 1 < len(line)
                        and line[col + 1] == "*"
                        and not in_string
                        and not in_char
                        and not in_raw_string
                    ):
                        # Skip until we find closing */
                        in_block_comment = True
                        col += 2  # Skip /*
                        block_comment_iterations = 0
                        max_block_comment_iterations = 1000

                        while (
                            i < max_end_line
                            and block_comment_iterations < max_block_comment_iterations
                        ):
                            block_comment_iterations += 1
                            while col < len(line):
                                if col > 0 and line[col - 1] == "*" and line[col] == "/":
                                    in_block_comment = False
                                    break
                                col += 1

                            if not in_block_comment:
                                break

                            i += 1
                            if i >= len(lines):
                                break
                            line = lines[i]
                            col = 0

                        # Safety check for block comments
                        if block_comment_iterations >= max_block_comment_iterations:
                            logger.warning("Possible infinite loop in block comment processing")
                            return min(start + 20, len(lines) - 1)

                        if not in_block_comment:
                            col += 1  # Move past the closing /
                            continue

                    # Handle nesting, but only if not in a string or character literal
                    elif not in_string and not in_char and not in_raw_string:
                        if char == open_char:
                            nesting_level += 1
                            logger.debug(
                                f"L{i+1}:{col+1} Found '{open_char}', nesting level -> {nesting_level}"
                            )
                        elif char == close_char:
                            nesting_level -= 1
                            logger.debug(
                                f"L{i+1}:{col+1} Found '{close_char}', nesting level -> {nesting_level}"
                            )
                            if nesting_level == 0:
                                logger.debug(
                                    f"L{i+1}:{col+1} Found final '{close_char}', returning line {i+1}"
                                )
                                return i

                    col += 1

                # Move to next line after processing all columns
                i += 1
                col = 0

            # Check if we hit the max iterations - possible infinite loop
            if iterations >= max_iterations:
                logger.warning(
                    f"Maximum iterations ({max_iterations}) reached in _find_block_end_improved"
                )
                return min(start + 30, len(lines) - 1)  # Return a safe value

        except Exception as e:
            logger.error(f"Error in _find_block_end_improved: {e}")
            return min(start + 10, len(lines) - 1)  # Return a safe value

        # If no matching closing character found after loop finishes, log a warning and return a reasonable end line
        logger.warning(
            f"Could not find matching {close_char} for {open_char} at line {start+1}. Returning a reasonable estimate."
        )
        return min(start + 50, len(lines) - 1)  # Return at most 50 lines after start

    def _process_imports(self, line: str, imports: List[str]) -> bool:
        """
        Process Rust use statements and add them to the imports list.

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

                # Handle nested paths like 'use std::{fs, io, path};'
                if "{" in path and "}" in path:
                    base_path = path.split("{")[0].strip()
                    nested_paths = path.split("{")[1].split("}")[0].strip()
                    for nested in nested_paths.split(","):
                        nested = nested.strip()
                        if nested:
                            # Extract base module name
                            if "::" in base_path:
                                module_name = base_path.split("::")[0]
                            else:
                                module_name = base_path
                            imports.append(module_name)
                else:
                    # Simple path like 'use std::fs;'
                    if "::" in path:
                        module_name = path.split("::")[0]
                    else:
                        module_name = path
                    imports.append(module_name)

                return True
        return False

    def _extract_rust_docstring(self, lines: List[str], current_line: int) -> str:
        """
        Extract Rust docstring comments (///, //!) before a declaration.

        Args:
            lines: List of code lines.
            current_line: Line number of the declaration.

        Returns:
            Extracted docstring as a string.
        """
        if current_line <= 0:
            return ""

        # Look for docstring comments before the current line
        doc_lines = []
        i = current_line - 1

        while i >= 0 and i >= current_line - 20:  # Look up to 20 lines back
            line = lines[i].strip()

            # Skip blank lines between doc comments and declaration
            if not line:
                i -= 1
                continue

            # Check for doc comments (/// or //!)
            if line.startswith("///") or line.startswith("//!"):
                prefix_len = 3
                doc_lines.insert(0, line[prefix_len:].strip())
                i -= 1
            else:
                # Non-doc-comment line found, stop looking
                break

        return "\n".join(doc_lines)

    def _extract_modifiers(self, line: str) -> List[str]:
        """
        Extract modifiers from a declaration line.

        Args:
            line: Line containing a declaration.

        Returns:
            List of modifiers found in the line.
        """
        # Split line into words and check each word directly instead of using regex
        # This is more efficient for large input
        words = set(re.findall(r"\b\w+\b", line))

        # Direct set intersection is much faster than individual regex searches
        return list(words.intersection(self.modifiers))

    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_classes": False,  # Rust has structs/enums/traits, not classes
            "can_parse_structs": True,
            "can_parse_enums": True,
            "can_parse_traits": True,
            "can_parse_imports": True,
            "can_extract_docstrings": True,
            "can_handle_macros": True,
            "can_handle_nested_declarations": True,
        }
