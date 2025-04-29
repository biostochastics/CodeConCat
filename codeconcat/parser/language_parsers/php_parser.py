import re

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.base_parser import ParserInterface


class PhpParser(ParserInterface):
    """Parses PHP code using Regex."""

    def __init__(self):
        """Initialize PHP parser with regex patterns."""
        super().__init__()
        self.patterns = {
            "namespace": re.compile(r"^namespace\s+(?P<name>[\w\\]+)"),
            "class": re.compile(r"^(?:abstract\s+)?class\s+(?P<name>\w+)"),
            "interface": re.compile(r"^interface\s+(?P<name>\w+)"),
            "trait": re.compile(r"^trait\s+(?P<name>\w+)"),
            "function": re.compile(
                r"^(?:(?:public|private|protected|static|final|abstract)\s+)*"
                r"function\s+(?:&\s*)?(?P<name>\w+)\s*\("
            ),
            "arrow_function": re.compile(r"^\$(?P<name>\w+)\s*=\s*fn\s*\([^)]*\)\s*=>"),
            "property": re.compile(
                r"^(?:(?:public|private|protected|static|final|var)\s+)*" r"\$(?P<name>\w+)"
            ),
        }
        # Patterns for imports and includes
        self.use_pattern = re.compile(r"^use\s+([\w\\]+)(?:\s+as\s+\w+)?;")
        self.include_pattern = re.compile(
            r"^(require|include|require_once|include_once)\s*\(?\s*['\"]([^'\"]+)['\"]\s*\)?\s*;"
        )

        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse PHP code and return a ParseResult object."""
        declarations = []
        imports = []  # List to store imports/includes
        lines = content.split("\n")
        i = 0
        current_namespace = None

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith(self.line_comment):
                i += 1
                continue
            # Skip multi-line comments (basic check)
            if line.startswith(self.block_comment_start):
                while i < len(lines) and not lines[i].strip().endswith(self.block_comment_end):
                    i += 1
                i += 1  # Move past the closing comment line
                continue

            # Check for 'use' statements
            use_match = self.use_pattern.match(line)
            if use_match:
                imports.append(use_match.group(1))
                i += 1
                continue

            # Check for include/require statements
            include_match = self.include_pattern.match(line)
            if include_match:
                imports.append(include_match.group(2))  # Group 2 is the file path
                i += 1
                continue

            # Try each declaration pattern
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    if not name:
                        continue

                    # Handle namespaces
                    if kind == "namespace":
                        current_namespace = name
                        decl = Declaration(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=i + 1,
                            modifiers=set(),
                            docstring="",
                            children=[],
                        )
                        declarations.append(decl)
                        # Namespace declaration is usually single line
                        # i += 1 # Let the main loop increment i
                        break

                    # Add namespace prefix to name if in a namespace
                    # Only prefix certain types, not properties
                    namespaced_name = name
                    if current_namespace and kind in [
                        "class",
                        "interface",
                        "trait",
                        "function",
                    ]:
                        namespaced_name = f"{current_namespace}\\{name}"

                    # Convert arrow functions to regular functions for consistency
                    # Note: This changes the kind, might affect consumers
                    # if kind == "arrow_function":
                    #     kind = "function"

                    # Find end line (simple brace counting, fragile for complex cases)
                    end_line = i
                    if kind != "property" and ("{" in line or "=>" in line):
                        brace_count = line.count("{") - line.count("}")
                        if brace_count > 0:
                            j = i + 1
                            while j < len(lines):
                                curr_line = lines[j]
                                brace_count += curr_line.count("{")
                                brace_count -= curr_line.count("}")
                                if brace_count <= 0:
                                    end_line = j
                                    break
                                j += 1
                        elif kind == "arrow_function" and line.endswith(";"):
                            end_line = i  # Arrow functions are single line
                        # If no braces and not arrow func, assume single line (e.g., abstract method)
                        elif "{" not in line and kind != "arrow_function" and line.endswith(";"):
                            end_line = i
                    elif line.endswith(";"):  # Property or simple statement
                        end_line = i

                    # Create declaration
                    decl = Declaration(
                        kind=kind,
                        name=namespaced_name,  # Use potentially namespaced name
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(),  # Modifier extraction not implemented
                        docstring="",  # Docstring extraction not implemented
                        children=[],  # Child extraction not implemented
                    )

                    # Add to declarations (no nesting implemented here)
                    declarations.append(decl)

                    # Move past the processed block
                    i = end_line
                    break  # Found a match for this line

            # Increment line counter if no declaration was found or after processing
            i += 1

        return ParseResult(
            file_path=file_path,
            language="php",
            content=content,
            declarations=declarations,
            imports=imports,
            engine_used="regex",
        )
