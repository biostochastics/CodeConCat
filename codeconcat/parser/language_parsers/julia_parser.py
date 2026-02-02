# file: codeconcat/parser/language_parsers/julia_parser.py

import re
from abc import ABC, abstractmethod

from codeconcat.base_types import Declaration, ParseResult


# Define a basic interface to match what the file_parser expects
class ParserInterface(ABC):
    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        pass


class JuliaParser(ParserInterface):
    """JuliaParser class is responsible for parsing Julia source code.

    Extracts module, struct, function, and macro declarations using regex patterns.
    Uses regex patterns to identify and extract different code declarations.
    Handles simple block detection for modules, structs, functions, and macros.
    Assumes top-level module declarations, with no support for nested modules.
    Returns a ParseResult containing declarations and import statements.
    """

    def __init__(self):
        """Initialize Julia parser with regex patterns."""
        self.patterns = {
            "module": re.compile(r"^module\s+(?P<name>\w+)"),
            "struct": re.compile(r"^(?:mutable\s+)?struct\s+(?P<name>\w+)"),
            "function": re.compile(r"^function\s+(?P<name>[\w.]+)|"),
            "macro": re.compile(r"^macro\s+(?P<name>\w+)"),
            "inline_function": re.compile(r"^(?P<name>\w+)\s*\([^)]*\)\s*="),
            "type": re.compile(r"^(?:abstract|primitive)\s+type\s+(?P<name>\w+)"),
        }
        self.import_pattern = re.compile(r"^\s*(?:using|import)\s+(.*)")
        self.line_comment = "#"
        self.block_comment_start = "#="
        self.block_comment_end = "=#"
        self.current_file_path: str = ""

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse Julia code and return a ParseResult object."""
        self.current_file_path = file_path
        declarations = []
        imports = []
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith(self.line_comment):
                i += 1
                continue

            # Check for imports first
            import_match = self.import_pattern.match(line)
            if import_match:
                imports.append(import_match.group(1).strip())
                i += 1
                continue

            # Try each declaration pattern
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    if not name:
                        continue

                    # Extract modifiers
                    modifiers: set[str] = set()
                    if kind == "struct" and "mutable" in line:
                        modifiers.add("mutable")
                    # A simple check for inline, might need refinement
                    if "@inline" in lines[i]:
                        modifiers.add("inline")

                    # Find end line (simple block detection, might be fragile)
                    end_line = i
                    if kind in ["module", "struct", "function", "macro", "type"]:
                        # Basic check for 'end' keyword
                        # This might fail for nested structures or complex code
                        j = i + 1
                        nesting_level = 1
                        while j < len(lines):
                            curr_line = lines[j].strip()
                            # Rough check for start/end keywords
                            if any(
                                curr_line.startswith(k)
                                for k in [
                                    "module",
                                    "struct",
                                    "function",
                                    "macro",
                                    "type",
                                    "begin",
                                    "for",
                                    "while",
                                    "if",
                                ]
                            ):
                                nesting_level += 1
                            if curr_line == "end":
                                nesting_level -= 1
                                if nesting_level == 0:
                                    end_line = j
                                    break
                            j += 1
                    # No specific end block for inline functions or types defined inline

                    # Create declaration
                    decl = Declaration(
                        kind="function" if kind == "inline_function" else kind,
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=modifiers,
                        docstring="",
                        children=[],
                    )

                    # Handle module declarations and nesting
                    if kind == "module":
                        # For simplicity, not handling nested modules here.
                        # Assuming top-level modules only for now.
                        declarations.append(decl)
                        # Skip the entire block. Set i to end_line for the next iteration.
                        i = end_line
                    else:
                        # Simple approach: add to top-level declarations.
                        # Proper nesting would require tracking the current scope.
                        declarations.append(decl)
                        # Skip the parsed block if it had an 'end' line
                        if end_line > i:
                            i = end_line

                    break  # Stop checking patterns for this line

            # Move to the next line if no declaration was found or after processing one
            i += 1

        return ParseResult(
            declarations=declarations,
            imports=imports,
            ast_root=None,  # No AST for regex parser
            error=None,  # No errors to report
            engine_used="regex",  # This is a regex parser
        )
