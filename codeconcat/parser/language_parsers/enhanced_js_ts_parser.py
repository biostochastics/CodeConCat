# file: codeconcat/parser/language_parsers/enhanced_js_ts_parser.py

"""
Enhanced JavaScript/TypeScript parser for CodeConcat.

This module provides an improved JS/TS parser using the EnhancedBaseParser
with specific patterns and functionality for JavaScript and TypeScript.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser
from codeconcat.parser.language_parsers.pattern_library import (
    ClassPatterns,
    CommentPatterns,
    FunctionPatterns,
    ImportPatterns
)

logger = logging.getLogger(__name__)


class EnhancedJSTypeScriptParser(EnhancedBaseParser):
    """JavaScript/TypeScript parser using improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced JS/TS parser."""
        super().__init__()
        self.language = "javascript"  # Default to JS, can be overridden for TS
        self._setup_js_ts_patterns()
    
    def _setup_standard_patterns(self):
        """Setup standard patterns for JavaScript/TypeScript."""
        super()._setup_standard_patterns()
        
        # JS/TS specific comment patterns
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"
        
        # JS/TS uses braces for blocks
        self.block_start = "{"
        self.block_end = "}"
        
        # Initialize patterns dict (will be populated in _setup_js_ts_patterns)
        self.patterns = {}
        
        # Initialize recognized JS/TS modifiers
        self.modifiers = {
            "static", "async", "export", "default", "const", "let", "var",
            "private", "protected", "public", "readonly", "abstract"
        }
    
    def _setup_js_ts_patterns(self):
        """Setup JavaScript/TypeScript specific patterns."""
        # Class pattern
        self.patterns["class"] = ClassPatterns.JS_TS
        
        # Function patterns (multiple types)
        self.patterns["function_declaration"] = FunctionPatterns.JS_TS["function_declaration"]
        self.patterns["method_declaration"] = FunctionPatterns.JS_TS["method_declaration"]
        self.patterns["arrow_function"] = FunctionPatterns.JS_TS["arrow_function"]
        
        # Import patterns
        self.patterns["import"] = ImportPatterns.JS_TS["import"]
        self.patterns["require"] = ImportPatterns.JS_TS["require"]
        
        # Interface pattern (TypeScript)
        self.patterns["interface"] = re.compile(
            r"^\s*(?:export\s+)?interface\s+(?P<name>[\w<>]+)(?:\s+extends\s+[\w\s,<>.]+)?\s*\{?",
            re.MULTILINE
        )
        
        # Type pattern (TypeScript)
        self.patterns["type"] = re.compile(
            r"^\s*(?:export\s+)?type\s+(?P<name>[\w<>]+)\s*=",
            re.MULTILINE
        )
        
        # Variable declarations
        self.patterns["variable"] = re.compile(
            r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>\w+)\s*(?:\s*\w+)?\s*=",
            re.MULTILINE
        )
        
        # Method definition pattern (within classes)
        self.patterns["method"] = re.compile(
            r"^\s*(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?(?P<name>[\w$]+)\s*\(",
            re.MULTILINE
        )
        
        # Object method/property pattern
        self.patterns["object_method"] = re.compile(
            r"^\s*(?P<name>[\w$]+)\s*:\s*function\s*\(",
            re.MULTILINE
        )
        
        # Anonymous function pattern - for nested function detection
        self.patterns["anon_function"] = re.compile(
            r"^\s*function\s*\(", 
            re.MULTILINE
        )
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse JavaScript/TypeScript code and return a ParseResult object."""
        try:
            logger.debug(f"Starting EnhancedJSTypeScriptParser.parse for file: {file_path}")
            
            # Determine if this is TypeScript based on file extension
            if file_path.lower().endswith((".ts", ".tsx")):
                self.language = "typescript"
                logger.debug(f"Detected TypeScript file: {file_path}")
            else:
                self.language = "javascript"
                logger.debug(f"Detected JavaScript file: {file_path}")
            
            declarations = []
            imports = []
            errors = []
            
            lines = content.split("\n")
            
            # First pass: extract imports for the entire file
            for i, line in enumerate(lines):
                line = line.strip()
                self._process_imports(line, imports)
            
            # Second pass: process declarations and nested blocks
            self._process_block(
                lines=lines,
                start=0,
                end=len(lines) - 1,
                declarations=declarations,
                imports=imports,
                errors=errors
            )
            
            # Remove duplicates from imports
            imports = list(set(imports))
            
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
            logger.error(f"Error parsing JS/TS file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse JS/TS file ({type(e).__name__}): {e}"
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
        Process a JS/TS code block and extract declarations and imports.
        
        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index (inclusive).
            declarations: List to add declarations to.
            imports: List to add imports to.
            errors: List to add errors to.
            parent_declaration: Parent declaration if processing a nested block.
            
        Returns:
            The line index to continue processing from.
        """
        i = start
        
        # Track the current brace level for the block
        brace_level = 0
        in_declaration = False
        current_declaration = None
        
        logger.debug(f"Processing JS/TS block at lines {start+1}-{end+1}")
        
        while i <= end:
            if i >= len(lines):
                break
                
            line = lines[i].strip()
            raw_line = lines[i]
            
            # Skip empty lines and single-line comments
            if not line or line.startswith("//"):
                i += 1
                continue
            
            # Skip block comments
            if line.startswith("/*"):
                if "*/" in line:
                    i += 1
                    continue
                # Find end of block comment
                while i <= end and "*/" not in lines[i]:
                    i += 1
                i += 1
                continue
            
            # Process declarations
            declaration_match = None
            declared_kind = None
            
            # Check for different declaration types in priority order
            # First check for class
            if not declaration_match:
                class_match = self.patterns["class"].match(line)
                if class_match:
                    declaration_match = class_match
                    declared_kind = "class"
            
            # Check for function declarations
            if not declaration_match:
                func_match = self.patterns["function_declaration"].match(line)
                if func_match:
                    declaration_match = func_match
                    declared_kind = "function"
                
            # Check for method declarations (when inside a class)
            if not declaration_match and parent_declaration and parent_declaration.kind == "class":
                method_match = self.patterns["method_declaration"].match(line)
                if method_match:
                    declaration_match = method_match
                    declared_kind = "method"
            
            # Check for arrow functions
            if not declaration_match:
                arrow_match = self.patterns["arrow_function"].match(line)
                if arrow_match:
                    declaration_match = arrow_match
                    declared_kind = "function"  # Normalize to function
            
            # Check for TypeScript interfaces
            if not declaration_match and self.language == "typescript":
                interface_match = self.patterns["interface"].match(line)
                if interface_match:
                    declaration_match = interface_match
                    declared_kind = "interface"
            
            # Check for TypeScript types
            if not declaration_match and self.language == "typescript":
                type_match = self.patterns["type"].match(line)
                if type_match:
                    declaration_match = type_match
                    declared_kind = "type"
            
            # Check for object methods
            if not declaration_match:
                obj_method_match = self.patterns["object_method"].match(line)
                if obj_method_match:
                    declaration_match = obj_method_match
                    declared_kind = "method"
            
            # Check for anonymous functions (for nested function tracking)
            if not declaration_match and "{" in line and "function" in line:
                anon_match = self.patterns["anon_function"].match(line)
                if anon_match:
                    # Generate a name for the anonymous function based on line number
                    func_name = f"anonymous_{i+1}"
                    declared_kind = "function"
                    
                    # Create a simulated match object for processing
                    class SimulatedMatch:
                        def group(self, name):
                            return func_name
                    
                    declaration_match = SimulatedMatch()
            
            # Process the declaration if found
            if declaration_match:
                # Get declaration name
                try:
                    name = declaration_match.group("name")
                except (IndexError, KeyError):
                    # Fallback for patterns that use other group names
                    try:
                        name = declaration_match.group("n")
                    except (IndexError, KeyError):
                        # Skip if we can't extract a name
                        i += 1
                        continue
                
                modifiers = self._extract_modifiers(line)
                docstring = self._extract_jsdoc(lines, i)
                
                # Normalize the declaration kind
                normalized_kind = self._normalize_declaration_kind(declared_kind)
                
                logger.debug(f"Found potential {normalized_kind} declaration: {name} at line {i+1}")
                
                # Find block boundaries
                start_line = i
                
                # Find the opening brace and track brace nesting level
                brace_in_line = "{" in line
                has_block = brace_in_line
                
                if has_block:
                    # Block starts on this line
                    open_braces = line.count("{")
                    close_braces = line.count("}")
                    brace_level = open_braces - close_braces
                    
                    if brace_level <= 0:
                        # Single-line block or no block
                        end_line = i
                        i += 1
                    else:
                        # Find matching closing brace
                        j = i + 1
                        local_brace_level = brace_level
                        
                        while j <= end and local_brace_level > 0:
                            j_line = lines[j]
                            local_brace_level += j_line.count("{") - j_line.count("}")
                            if local_brace_level <= 0:
                                break
                            j += 1
                        
                        end_line = min(j, end)
                        
                        # Create declaration
                        declaration = Declaration(
                            name=name,
                            kind=normalized_kind,
                            docstring=docstring,
                            modifiers=list(modifiers),
                            start_line=start_line + 1,  # 1-indexed
                            end_line=end_line + 1,      # 1-indexed
                            children=[]
                        )
                        
                        # Add to parent or declarations list
                        if parent_declaration:
                            parent_declaration.children.append(declaration)
                            logger.debug(f"Added nested declaration to parent {parent_declaration.name}: {normalized_kind} {name}")
                        else:
                            declarations.append(declaration)
                            logger.debug(f"Added top-level declaration: {normalized_kind} {name}")
                        
                        # Process nested declarations
                        if normalized_kind in ["class", "function", "method", "interface"] and end_line > start_line:
                            # Find the content within the block, excluding the braces
                            inner_start = i
                            if "{" in lines[i]:
                                # If the opening brace is on the same line, start content after it
                                inner_start += 1
                            
                            # Skip empty lines at the start
                            while inner_start < end_line and not lines[inner_start].strip():
                                inner_start += 1
                            
                            # Process the block body recursively
                            if inner_start < end_line:
                                # Process the nested block recursively
                                self._process_block(
                                    lines=lines,
                                    start=inner_start,
                                    end=end_line - 1,  # Exclude closing brace
                                    declarations=[],   # Use empty list since we're adding directly to children
                                    imports=imports,
                                    errors=errors,
                                    parent_declaration=declaration
                                )
                        
                        # Continue from after the end of this block
                        i = end_line + 1
                else:
                    # Look for block start on following lines
                    j = i + 1
                    while j <= end:
                        j_line = lines[j].strip()
                        if j_line.startswith("{"):
                            has_block = True
                            
                            # Find matching closing brace
                            open_braces = 1
                            j += 1
                            while j <= end and open_braces > 0:
                                j_line = lines[j]
                                open_braces += j_line.count("{") - j_line.count("}")
                                if open_braces <= 0:
                                    break
                                j += 1
                            
                            end_line = min(j, end)
                            
                            # Create declaration
                            declaration = Declaration(
                                name=name,
                                kind=normalized_kind,
                                docstring=docstring,
                                modifiers=list(modifiers),
                                start_line=start_line + 1,  # 1-indexed
                                end_line=end_line + 1,      # 1-indexed
                                children=[]
                            )
                            
                            # Add to parent or declarations list
                            if parent_declaration:
                                parent_declaration.children.append(declaration)
                                logger.debug(f"Added nested declaration to parent {parent_declaration.name}: {normalized_kind} {name}")
                            else:
                                declarations.append(declaration)
                                logger.debug(f"Added top-level declaration: {normalized_kind} {name}")
                            
                            # Process nested declarations
                            if normalized_kind in ["class", "function", "method", "interface"] and end_line > start_line:
                                # Process the nested block recursively
                                self._process_block(
                                    lines=lines,
                                    start=i + 1,  # Start after declaration line
                                    end=end_line - 1,  # End before closing brace
                                    declarations=[],   # Use empty list since we're adding to declaration.children
                                    imports=imports,
                                    errors=errors,
                                    parent_declaration=declaration
                                )
                            
                            # Continue from after the end of this block
                            i = end_line + 1
                            break
                        elif j_line and not j_line.startswith("//") and not j_line.startswith("/*"):
                            # Found non-empty, non-comment line that's not an opening brace
                            # This is probably not a block
                            break
                        j += 1
                    
                    if not has_block:
                        # No block found, just a declaration
                        declaration = Declaration(
                            name=name,
                            kind=normalized_kind,
                            docstring=docstring,
                            modifiers=list(modifiers),
                            start_line=start_line + 1,  # 1-indexed
                            end_line=start_line + 1,    # Same line
                            children=[]
                        )
                        
                        if parent_declaration:
                            parent_declaration.children.append(declaration)
                            logger.debug(f"Added nested declaration (no block) to parent {parent_declaration.name}: {normalized_kind} {name}")
                        else:
                            declarations.append(declaration)
                            logger.debug(f"Added declaration (no block): {normalized_kind} {name}")
                        
                        i += 1
            else:
                # No declaration found on this line
                i += 1
        
        return i
    
    def _normalize_declaration_kind(self, kind: str) -> str:
        """
        Normalize declaration kinds to a standard set.
        
        Args:
            kind: Original declaration kind.
            
        Returns:
            Normalized declaration kind.
        """
        # Map all function-like declarations to "function"
        if kind in ["function_declaration", "arrow_function"]:
            return "function"
        
        # Map all method-like declarations to "method"
        if kind in ["method_declaration", "object_method"]:
            return "method"
        
        return kind
    
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
    
    def _extract_jsdoc(self, lines: List[str], current_line: int) -> Optional[str]:
        """
        Extract JSDoc comments that precede a declaration.
        
        Args:
            lines: List of code lines.
            current_line: Line number of the declaration.
            
        Returns:
            Extracted JSDoc comment if found, None otherwise.
        """
        if current_line <= 0:
            return None
            
        # Look for a JSDoc block before the current line
        i = current_line - 1
        while i >= 0:
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i -= 1
                continue
            
            # Found a JSDoc block
            if line.startswith("/**"):
                comment_lines = []
                
                # Single-line JSDoc
                if line.endswith("*/"):
                    # Extract content between /** and */
                    content = line[3:-2].strip()
                    if content:
                        return content
                    return None
                
                # Multi-line JSDoc
                while i >= 0:
                    line = lines[i].strip()
                    if line.startswith("/**"):
                        # Found the start of the JSDoc
                        content = line[3:].strip()
                        if content:
                            comment_lines.insert(0, content)
                        break
                    
                    if line.endswith("*/"):
                        # End of block comment
                        content = line[:-2].strip()
                        if content:
                            comment_lines.insert(0, content)
                        i -= 1
                        continue
                    
                    # Middle of block comment
                    # Remove leading * if present
                    content = line[line.startswith("*") and 1 or 0:].strip()
                    if content:
                        comment_lines.insert(0, content)
                    i -= 1
                    
                if comment_lines:
                    return "\n".join(comment_lines)
                return None
                
            # If we hit a non-empty, non-comment line before finding a JSDoc block, there's no JSDoc
            if not line.startswith("//") and not line.startswith("/*") and not line.startswith("*"):
                return None
                
            i -= 1
            
        return None
    
    def _process_imports(self, line: str, imports: List[str]) -> bool:
        """
        Process JS/TS import statements and add them to the imports list.
        
        Args:
            line: Line of code to process.
            imports: List to add imports to.
            
        Returns:
            True if line was an import statement, False otherwise.
        """
        # Handle ES6 imports
        if line.startswith("import "):
            # Extract the module name from the string
            module_match = re.search(r"from\s+['\"]([^'\"]+)['\"]", line)
            if module_match:
                module_name = module_match.group(1)
                # Normalize module path to get the main package name
                if "/" in module_name:
                    parts = module_name.split("/")
                    # Handle scoped packages (starting with @)
                    if module_name.startswith("@"):
                        if len(parts) >= 2:
                            module_name = f"{parts[0]}/{parts[1]}"
                    else:
                        module_name = parts[0]
                
                if module_name and module_name not in imports:
                    imports.append(module_name)
                    logger.debug(f"Found ES6 import: {module_name}")
                return True
        
        # Handle CommonJS require
        if "require(" in line:
            # Extract the module name from the string
            module_match = re.search(r"require\s*\(['\"]([^'\"]+)['\"]", line)
            if module_match:
                module_name = module_match.group(1)
                # Get the base package name similar to ES6 imports
                if "/" in module_name:
                    parts = module_name.split("/")
                    if module_name.startswith("@"):
                        if len(parts) >= 2:
                            module_name = f"{parts[0]}/{parts[1]}"
                    else:
                        module_name = parts[0]
                
                if module_name and module_name not in imports:
                    imports.append(module_name)
                    logger.debug(f"Found CommonJS require: {module_name}")
                return True
        
        # Handle import statements for TypeScript (e.g. 'import type', 'import {type X}')
        if re.match(r'^\s*import\s+type\s', line) or 'import {' in line:
            module_match = re.search(r"from\s+['\"]([^'\"]+)['\"]", line)
            if module_match:
                module_name = module_match.group(1)
                if module_name and module_name not in imports:
                    imports.append(module_name)
                    logger.debug(f"Found TypeScript type import: {module_name}")
                return True
        
        return False
    
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
    
    def _calculate_max_nesting_depth(self, declarations: List[Declaration], current_depth: int = 1) -> int:
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
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_classes": True,
            "can_parse_imports": True,
            "can_extract_docstrings": True,
            "can_handle_arrow_functions": True,
            "can_handle_typescript": self.language == "typescript",
        }
