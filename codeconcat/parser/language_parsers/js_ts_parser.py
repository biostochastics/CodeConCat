"""JavaScript/TypeScript code parser for CodeConcat."""

import re
from typing import List, Optional, Set

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser


def parse_javascript_or_typescript(file_path: str, content: str, language: str = "javascript") -> Optional[ParsedFileData]:
    """Parse JavaScript or TypeScript code and return declarations."""
    parser = JstsParser(language)
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language=language,
        content=content,
        declarations=declarations
    )


class CodeSymbol:
    def __init__(
        self,
        name: str,
        kind: str,
        start_line: int,
        end_line: int,
        modifiers: Set[str],
        docstring: Optional[str],
        children: List["CodeSymbol"],
    ):
        self.name = name
        self.kind = kind
        self.start_line = start_line
        self.end_line = end_line
        self.modifiers = modifiers
        self.docstring = docstring
        self.children = children
        self.brace_depth = 0  # Current nesting depth at the time this symbol was "opened"


class JstsParser(BaseParser):
    """
    JavaScript/TypeScript language parser with improved brace-handling and 
    arrow-function detection. Supports classes, functions, methods, arrow functions, 
    interfaces, type aliases, enums, and basic decorators.
    """

    def __init__(self, language: str = "javascript"):
        self.language = language
        self.patterns = []
        super().__init__()

        # Set recognized modifiers
        self.recognized_modifiers = {
            "export",
            "default",
            "async",
            "public",
            "private",
            "protected",
            "static",
            "readonly",
            "abstract",
            "declare",
            "const",
        }

        # Comment markers
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # Context tracking
        self.in_class = False

        self._setup_patterns()

    def _setup_patterns(self) -> List[re.Pattern]:
        """Set up regex patterns for parsing JavaScript/TypeScript code."""
        return [
            # Function patterns
            re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(?P<symbol_name>\w+)\s*\("),
            re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(?P<symbol_name>\w+)\s*=\s*(?:async\s+)?function\s*\("),
            re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(?P<symbol_name>\w+)\s*=\s*(?:async\s+)?\(.*\)\s*=>"),
            
            # Method patterns (inside class)
            re.compile(r"^\s*(?:static\s+)?(?:async\s+)?(?P<symbol_name>\w+)\s*\("),
            
            # Class patterns
            re.compile(r"^(?:export\s+)?class\s+(?P<symbol_name>\w+)"),
            
            # Interface patterns (TypeScript)
            re.compile(r"^(?:export\s+)?interface\s+(?P<symbol_name>\w+)"),
            
            # Type alias patterns (TypeScript)
            re.compile(r"^(?:export\s+)?type\s+(?P<symbol_name>\w+)"),
            
            # Enum patterns (TypeScript)
            re.compile(r"^(?:export\s+)?enum\s+(?P<symbol_name>\w+)"),
        ]

    def parse(self, content: str) -> List[Declaration]:
        """Parse JavaScript/TypeScript code content."""
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        symbol_stack: List[CodeSymbol] = []
        current_doc_comments = []
        current_modifiers = set()
        brace_depth = 0
        self.in_class = False

        def pop_symbols_up_to(depth: int, line_idx: int):
            """Pop symbols from stack up to given depth."""
            while symbol_stack and symbol_stack[-1].brace_depth >= depth:
                symbol = symbol_stack.pop()
                symbol.end_line = line_idx
                if symbol_stack:
                    symbol_stack[-1].children.append(symbol)
                symbols.append(symbol)
                if symbol.kind == "class":
                    self.in_class = False

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Handle doc comments
            if line.startswith("/**"):
                current_doc_comments.append(line)
                while i + 1 < len(lines) and "*/" not in lines[i]:
                    i += 1
                    current_doc_comments.append(lines[i].strip())
                i += 1
                continue

            # Skip other comments
            if line.startswith("//") or line.startswith("/*"):
                i += 1
                continue

            # Handle decorators
            if line.startswith("@"):
                current_modifiers.add(line)
                i += 1
                continue

            # Count braces before pattern matching
            brace_depth += line.count("{") - line.count("}")

            # Try to match each pattern
            matched = False
            for pattern in self._setup_patterns():
                match = pattern.match(line)
                if match:
                    matched = True
                    name = match.group("symbol_name")
                    if not name:
                        continue

                    # Get modifiers from regex and current set
                    modifiers = set(current_modifiers)
                    if line.startswith("export"):
                        modifiers.add("export")
                    if line.startswith("async"):
                        modifiers.add("async")
                    if line.startswith("const"):
                        modifiers.add("const")
                    if line.startswith("let"):
                        modifiers.add("let")
                    if line.startswith("var"):
                        modifiers.add("var")
                    current_modifiers.clear()

                    # Get the kind based on pattern
                    kind = self._get_kind(pattern)

                    # Create symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i + 1,
                        end_line=0,  # Will be set when popped
                        modifiers=modifiers,
                        docstring="\n".join(current_doc_comments) if current_doc_comments else None,
                        children=[],
                    )
                    symbol.brace_depth = brace_depth
                    current_doc_comments.clear()

                    # Update class context
                    if kind == "class":
                        self.in_class = True

                    # Add to stack
                    symbol_stack.append(symbol)
                    break

            # Handle closing braces after pattern matching
            if "}" in line:
                pop_symbols_up_to(brace_depth + 1, i + 1)

            i += 1

        # Pop any remaining symbols
        pop_symbols_up_to(0, len(lines))

        # Convert symbols to declarations
        declarations = []
        for symbol in symbols:
            declarations.append(
                Declaration(
                    kind=symbol.kind,
                    name=symbol.name,
                    start_line=symbol.start_line,
                    end_line=symbol.end_line,
                    modifiers=symbol.modifiers,
                    docstring=symbol.docstring,
                )
            )
            # Also add child declarations
            for child in symbol.children:
                declarations.append(
                    Declaration(
                        kind=child.kind,
                        name=child.name,
                        start_line=child.start_line,
                        end_line=child.end_line,
                        modifiers=child.modifiers,
                        docstring=child.docstring,
                    )
                )

        return declarations

    def _get_kind(self, pattern: re.Pattern) -> str:
        """Get the kind of symbol based on the pattern that matched."""
        pattern_str = pattern.pattern
        if "function" in pattern_str or "=>" in pattern_str:
            return "function"
        elif "class" in pattern_str:
            return "class"
        elif "interface" in pattern_str:
            return "interface"
        elif "type" in pattern_str:
            return "type"
        elif "enum" in pattern_str:
            return "enum"
        elif self.in_class and r"^\s*(?:static\s+)?(?:async\s+)?(?P<symbol_name>\w+)\s*\(" in pattern_str:
            return "method"
        return "function"  # Default to function for any other patterns