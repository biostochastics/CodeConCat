"""JavaScript/TypeScript code parser for CodeConcat."""

import re
from typing import List, Optional

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.base_parser import BaseParser


def parse_javascript_or_typescript(
    file_path: str, content: str, language: str = "javascript"
) -> ParseResult:
    """Parse JavaScript or TypeScript code and return ParseResult."""
    parser = JstsParser(file_path)
    try:
        return parser.parse(content)
    except Exception as e:
        # Wrap internal parser errors in LanguageParserError
        raise LanguageParserError(
            message=f"Failed to parse {language.capitalize()} file: {e}",
            file_path=file_path,
            original_exception=e,
        )


class CodeSymbol:
    def __init__(
        self,
        name: str,
        kind: str,
        start_line: int,
        end_line: int,
        modifiers: set,
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
        self.brace_depth = (
            0  # Current nesting depth at the time this symbol was "opened"
        )


class JstsParser(BaseParser):
    """
    JavaScript/TypeScript language parser with improved brace-handling and
    arrow-function detection. Supports classes, functions, methods, arrow functions,
    interfaces, type aliases, enums, and basic decorators.
    """

    def __init__(self, file_path: str):
        super().__init__(file_path=file_path)

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

        # Set up patterns
        patterns_str = [
            "^(?:export\\s+)?(?:async\\s+)?function\\s+\\*?(?P<symbol_name>[\\w\\$]+)\\s*\\(.*\\)\\s*\\{?",  # Function, async function, generator
            "^(?:export\\s+)?(?:async\\s+)?(?:const|let|var)\\s+(?P<symbol_name>[\\w\\$]+)\\s*=\\s*(?:async\\s+)?\\(.*\\)\\s*=>\\s*\\{?",  # Arrow function assigned to variable
            "^(?:export\\s+)?class\\s+(?P<symbol_name>[\\w\\$]+)(?:\\s+extends\\s+[\\w\\.]+)?(?:\\s+implements\\s+[\\w\\.\\s,]+)?\\s*\\{?",  # Class definition
            "^(?:export\\s+)?(?:abstract\\s+)?class\\s+(?P<symbol_name>[\\w\\$]+)(?:\\s+extends\\s+[\\w\\.]+)?(?:\\s+implements\\s+[\\w\\.\\s,]+)?\\s*\\{?",  # Abstract Class definition (TS)
            "^(?:export\\s+)?interface\\s+(?P<symbol_name>[\\w\\$]+)(?:\\s+extends\\s+[\\w\\.\\s,]+)?\\s*\\{?",  # Interface definition (TS)
            "^(?:export\\s+)?enum\\s+(?P<symbol_name>[\\w\\$]+)\\s*\\{?",  # Enum definition (TS)
            "^(?:export\\s+)?type\\s+(?P<symbol_name>[\\w\\$]+)\\s*=\\s*.*?",  # Type alias (TS)
            "^(?:export\\s+)?(?:const|let|var)\\s+(?P<symbol_name>[\\w\\$]+)\\s*[:=].*",  # Variable declaration
            # Method definitions within classes (more specific regex needed for accuracy)
            "^(?:public\\s+|private\\s+|protected\\s+|static\\s+|readonly\\s+|async\\s+)*\\*?(?P<symbol_name>[\\w\\$]+)\\s*\\(.*\\)\\s*[:{]?",  # Methods/Properties
        ]
        self.patterns = [re.compile(p) for p in patterns_str]

    def _get_kind(self, pattern: re.Pattern) -> str:
        """Get the kind of symbol based on the pattern that matched."""
        pattern_str = pattern.pattern
        # Check for arrow function first
        if "\\s*=\\s*(?:async\\s+)?\\([^)]*\\)\\s*=>" in pattern_str:
            return "arrow_function"
        elif "function\\s+" in pattern_str:
            return "function"
        elif "class\\s+" in pattern_str:
            return "class"
        elif "interface\\s+" in pattern_str:
            return "interface"
        elif "type\\s+" in pattern_str:
            return "type"
        elif "enum\\s+" in pattern_str:
            return "enum"
        elif (
            "^\\s*(?:static\\s+)?(?:async\\s+)?(?P<symbol_name>\\w+)\\s*\\("
            in pattern_str
        ):
            # If we're inside a class, it's a method. Otherwise, it's a function.
            if self.in_class:
                return "method"
            return "function"
        elif "(?:const|let|var)" in pattern_str and "=>" not in pattern_str:
            return "variable"
        else:
            return "unknown"  # Default to unknown for any other patterns

    def parse(self, content: str) -> ParseResult:
        """Parse JavaScript/TypeScript code content and return ParseResult."""
        lines = content.split("\n")
        symbols = []  # List to store all symbols
        symbol_stack = []  # Stack for tracking nested symbols
        current_doc_comments = []  # List to store current doc comments
        current_modifiers = set()  # Set to store current modifiers
        brace_depth = 0  # Counter for tracking brace depth
        self.in_class = False  # Initialize class context

        def pop_symbols_up_to(depth: int, line_idx: int):
            """Pop symbols from stack up to given depth."""
            while symbol_stack and symbol_stack[-1].brace_depth >= depth:
                symbol = symbol_stack.pop()
                symbol.end_line = line_idx
                if symbol_stack:
                    # Only add to children if we're popping a nested symbol
                    symbol_stack[-1].children.append(symbol)
                else:
                    # Only add to symbols list if it's a top-level symbol
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
            for pattern in self.patterns:  # Use stored patterns
                match = pattern.match(line)
                if match:
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
                        docstring=(
                            "\n".join(current_doc_comments)
                            if current_doc_comments
                            else None
                        ),
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

        def add_symbol_to_declarations(symbol: CodeSymbol):
            """Helper function to recursively add symbols and their children to declarations."""
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
            # Add child declarations recursively
            for child in symbol.children:
                add_symbol_to_declarations(child)

        # Process each top-level symbol
        for symbol in symbols:
            add_symbol_to_declarations(symbol)

        # Extract imports/requires
        imports = []
        import_pattern = re.compile(
            "^(?:import(?:(?:(?:[ \\n\\t]+(?:\\*\\s*as)?\\s*\\w*)|(?:[ \\n\\t]*\\{[^}]*\\}))(?:[ \\n\\t]+from)?))?[ \\n\\t]*(?:['\"])([^'\\\"]+)(?:['\"])"
        )
        require_pattern = re.compile(
            "(?:const|let|var)\\s+.*?=\\s*require\\(\\s*['\"]([^'\\\"]+)['\"]\\s*\\)"
        )

        for line in lines:
            line = line.strip()
            import_match = import_pattern.match(line)
            if import_match:
                imports.append(import_match.group(1))
            else:
                require_match = require_pattern.search(line)
                if require_match:
                    imports.append(require_match.group(1))

        return ParseResult(
            file_path=self.current_file_path,
            language="javascript",  # Or detect typescript?
            content=content,
            declarations=declarations,
            imports=list(set(imports)),  # Unique imports
            token_stats=None,
            security_issues=[],
        )
