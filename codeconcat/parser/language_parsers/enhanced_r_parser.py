# file: codeconcat/parser/language_parsers/enhanced_r_parser.py

"""
Enhanced R parser for CodeConcat.

This module provides an improved R parser using the EnhancedBaseParser
with R-specific patterns and functionality.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser
from codeconcat.parser.language_parsers.pattern_library import (
    CommentPatterns,
    create_pattern_with_modifiers
)

logger = logging.getLogger(__name__)


class EnhancedRParser(EnhancedBaseParser):
    """R language parser using improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced R parser."""
        super().__init__()
        self.language = "r"
        self._setup_r_patterns()
    
    def _setup_standard_patterns(self):
        """Setup standard patterns for R."""
        super()._setup_standard_patterns()
        
        # R specific comment pattern (R only has line comments)
        self.line_comment = "#"
        
        # R uses braces for blocks, but also supports expression-style functions
        self.block_start = "{"
        self.block_end = "}"
        
        # Initialize patterns dict (will be populated in _setup_r_patterns)
        self.patterns = {}
        
        # Initialize recognized R keywords
        self.modifiers = {
            "function", "if", "else", "for", "in", "while", "repeat",
            "next", "break", "return", "local", 
            "library", "require", "source", "import"
        }
    
    def _setup_r_patterns(self):
        """Setup R-specific patterns."""
        # Function declarations with assignment (most common form)
        self.patterns["function_assign"] = re.compile(
            r"^\s*(?P<name>[a-zA-Z0-9_.]+)\s*(?:<-|=)\s*function\s*\(",
            re.MULTILINE
        )
        
        # Function declarations with explicit return (less common)
        self.patterns["function_return"] = re.compile(
            r"^\s*return\s*\(\s*function\s*\(\s*\)\s*\{",
            re.MULTILINE
        )
        
        # S4 method definitions
        self.patterns["s4_method"] = re.compile(
            r"^\s*setMethod\s*\(\s*(?:['\"](?P<name>[^'\"]+)['\"]|f\s*=\s*['\"]([^'\"]+)['\"])",
            re.MULTILINE
        )
        
        # S4 class definitions
        self.patterns["s4_class"] = re.compile(
            r"^\s*setClass\s*\(\s*(?:['\"](?P<name>[^'\"]+)['\"]|Class\s*=\s*['\"]([^'\"]+)['\"])",
            re.MULTILINE
        )
        
        # S3 class method
        self.patterns["s3_method"] = re.compile(
            r"^\s*(?P<name>[a-zA-Z0-9_.]+)\.(?P<class>[a-zA-Z0-9_.]+)\s*(?:<-|=)\s*function",
            re.MULTILINE
        )
        
        # Package imports
        self.patterns["library"] = re.compile(
            r"^\s*(?:library|require)\s*\(\s*(?P<name>[a-zA-Z0-9._]+|['\"][a-zA-Z0-9._]+['\"])",
            re.MULTILINE
        )
        
        # Source includes
        self.patterns["source"] = re.compile(
            r"^\s*source\s*\(\s*['\"](?P<path>[^'\"]+)['\"]",
            re.MULTILINE
        )
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse R code and return a ParseResult object."""
        try:
            logger.debug(f"Starting EnhancedRParser.parse for file: {file_path}")
            
            declarations = []
            imports = []
            errors = []
            
            lines = content.split("\n")
            
            # Process the entire file content recursively
            self._process_block(lines, 0, len(lines) - 1, declarations, imports, errors)
            
            # Remove duplicates from imports
            imports = list(set(imports))
            
            logger.debug(
                f"Finished EnhancedRParser.parse for file: {file_path}. "
                f"Found {len(declarations)} declarations, {len(imports)} unique imports."
            )
            
            return ParseResult(
                declarations=declarations,
                imports=imports,
                engine_used="regex",
            )
            
        except Exception as e:
            logger.error(f"Error parsing R file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse R file ({type(e).__name__}): {e}"
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
        parent_declaration: Optional[Declaration] = None
    ) -> int:
        """
        Process an R code block and extract declarations and imports.
        
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
        
        while i <= end:
            if i >= len(lines):  # Safety check
                break
                
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Skip commented lines
            if line.startswith("#"):
                # Skip non-roxygen comments
                if not line.startswith("#'"):
                    i += 1
                    continue
                    
            # Check for imports
            if self._process_imports(line, imports):
                i += 1
                continue
            
            # Check each pattern for declarations
            for kind, pattern in self.patterns.items():
                if kind in ["library", "source"]:
                    continue  # Skip import patterns here
                    
                match = pattern.match(line)
                if match:
                    # Extract name - handle different group names in patterns
                    name = None
                    for group_name in ["name", "n"]:
                        try:
                            name = match.group(group_name)
                            if name:
                                break
                        except (IndexError, KeyError):
                            continue
                    
                    if not name:
                        # For S3/S4 methods, construct name from method + class
                        if kind in ["s3_method", "s4_method"] and "class" in match.groupdict():
                            method = match.group("method") if "method" in match.groupdict() else ""
                            class_name = match.group("class")
                            if method and class_name:
                                name = f"{method}.{class_name}"
                            elif class_name:
                                name = class_name
                        
                    if not name:
                        i += 1
                        continue
                    
                    # Normalize kinds for consistent categorization
                    if kind in ["function_assign", "function_return"]:
                        normalized_kind = "function"
                    elif kind in ["s3_method", "s4_method"]:
                        normalized_kind = "method"
                    elif kind in ["s4_class"]:
                        normalized_kind = "class"
                    else:
                        normalized_kind = kind
                    
                    start_line = i
                    end_line = i
                    docstring_text = ""
                    
                    # Get docstring if available (roxygen2 comments)
                    docstring_text = self._extract_roxygen_docstring(lines, i)
                    
                    # Check for block definition with braces
                    if "{" in line:
                        # Find the matching closing brace
                        end_line = self._find_block_end_improved(
                            lines, i, open_char="{", close_char="}"
                        )
                    elif "function(" in line or "function (" in line:
                        # Function with possible open brace on next line
                        j = i
                        while j < len(lines) and "{" not in lines[j] and ")" not in lines[j]:
                            j += 1
                        
                        if j < len(lines) and "{" in lines[j]:
                            end_line = self._find_block_end_improved(
                                lines, j, open_char="{", close_char="}"
                            )
                    
                    # Extract modifiers (like function, local, etc.)
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
                    
                    # Process nested blocks (only for functions and blocks with braces)
                    if end_line > start_line:
                        nested_declarations = []  # Create new list for children
                        # Recursively process the block for nested declarations
                        self._process_block(
                            lines, start_line + 1, end_line - 1, 
                            nested_declarations, imports, errors, declaration
                        )
                        declaration.children = nested_declarations  # Assign children
                    
                    # Move past the block
                    i = end_line + 1
                    break
            else:
                # No pattern matched, move to next line
                i += 1
                
        return i
    
    def _process_imports(self, line: str, imports: List[str]) -> bool:
        """
        Process R imports (library/require) and add them to the imports list.
        
        Args:
            line: Line of code to process.
            imports: List to add imports to.
            
        Returns:
            True if line was a library/require/source statement, False otherwise.
        """
        # Check for library or require statements
        if line.startswith(("library(", "require(")):
            match = self.patterns["library"].match(line)
            if match:
                package_name = match.group("name")
                # Remove quotes if present
                if package_name.startswith(("'", '"')) and package_name.endswith(("'", '"')):
                    package_name = package_name[1:-1]
                imports.append(package_name)
                return True
                
        # Check for source statements
        if line.startswith("source("):
            match = self.patterns["source"].match(line)
            if match:
                path = match.group("path")
                # Extract filename from path as "imported" content
                if "/" in path:
                    filename = path.split("/")[-1]
                else:
                    filename = path
                if filename.endswith(".R") or filename.endswith(".r"):
                    filename = filename[:-2]
                imports.append(f"source:{filename}")
                return True
                
        return False
    
    def _extract_roxygen_docstring(self, lines: List[str], current_line: int) -> str:
        """
        Extract roxygen2 docstring comments (#') before a declaration.
        
        Args:
            lines: List of code lines.
            current_line: Line number of the declaration.
            
        Returns:
            Extracted docstring as a string.
        """
        if current_line <= 0:
            return ""
            
        # Look for roxygen comments before the current line
        doc_lines = []
        i = current_line - 1
        
        while i >= 0 and i >= current_line - 30:  # Look up to 30 lines back
            line = lines[i].strip()
            
            # Skip blank lines between doc comments and declaration
            if not line:
                i -= 1
                continue
                
            # Check for roxygen comments (#')
            if line.startswith("#'"):
                doc_lines.insert(0, line[2:].strip())
                i -= 1
            else:
                # Non-roxygen line found, stop looking
                break
                
        return "\n".join(doc_lines)
    
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
            if re.search(fr"\b{re.escape(mod)}\b", line):
                found_modifiers.add(mod)
        return found_modifiers
    
    def _is_declaration_line(self, line: str) -> bool:
        """
        Check if a line contains the start of a declaration.
        
        Args:
            line: Line to check.
            
        Returns:
            True if line contains a declaration, False otherwise.
        """
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return False
            
        # Check for patterns that indicate a new declaration
        for kind, pattern in self.patterns.items():
            if pattern.match(line):
                return True
                
        return False
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_classes": True,  # S3 and S4 classes
            "can_parse_methods": True,  # S3 and S4 methods
            "can_parse_imports": True,  # library, require, source
            "can_extract_docstrings": True,  # roxygen2
        }
