"""JavaScript and TypeScript code parser for CodeConcat."""

import re
from typing import Dict, List, Pattern

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


class JstsParser(BaseParser):
    """JavaScript/TypeScript language parser."""

    def __init__(self, language: str = "javascript"):
        self.language = language  # Set language before calling super()
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """Set up JavaScript/TypeScript patterns."""
        # Common patterns for both JS and TS
        base_patterns = {
            "class": re.compile(
                r"^(?P<modifiers>(?:export\s+)?(?:default\s+)?)"  # Export/default modifiers
                r"class\s+(?P<class_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Class name
                r"(?:\s+extends\s+(?P<extends_name>[a-zA-Z_$][a-zA-Z0-9_$]*))?"  # Optional extends
                r"(?:\s+implements\s+(?P<implements_names>[a-zA-Z_$][a-zA-Z0-9_$]*(?:\s*,\s*[a-zA-Z_$][a-zA-Z0-9_$]*)*))?"  # Optional implements
            ),
            "function": re.compile(
                r"^(?P<modifiers>(?:export\s+)?(?:default\s+)?(?:async\s+)?)"  # Modifiers
                r"(?:function\s+)?(?P<function_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Function name
                r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
                r"(?:\s*:\s*(?P<return_type>[^{;]+))?"  # Optional return type (TS)
            ),
            "method": re.compile(
                r"^(?P<modifiers>(?:public|private|protected|static|readonly|async)\s+)*"  # Method modifiers
                r"(?P<method_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Method name
                r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
                r"(?:\s*:\s*(?P<return_type>[^{;]+))?"  # Optional return type (TS)
            ),
            "variable": re.compile(
                r"^(?P<modifiers>(?:export\s+)?(?:const|let|var)\s+)"  # Variable modifiers
                r"(?P<variable_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Variable name
                r"(?:\s*:\s*(?P<type_annotation>[^=;]+))?"  # Optional type annotation (TS)
                r"\s*=\s*"  # Assignment
            ),
            "interface": re.compile(
                r"^(?P<modifiers>(?:export\s+)?)"  # Export modifier
                r"interface\s+(?P<interface_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Interface name
                r"(?:\s+extends\s+(?P<extends_names>[a-zA-Z_$][a-zA-Z0-9_$]*(?:\s*,\s*[a-zA-Z_$][a-zA-Z0-9_$]*)*))?"  # Optional extends
            ),
            "type": re.compile(
                r"^(?P<modifiers>(?:export\s+)?)"  # Export modifier
                r"type\s+(?P<type_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Type name
                r"\s*=\s*(?P<type_value>.*)"  # Type assignment
            ),
        }

        # TypeScript-specific patterns
        if self.language == "typescript":
            base_patterns.update(
                {
                    "enum": re.compile(
                        r"^(?P<modifiers>(?:export\s+)?(?:const\s+)?)"  # Modifiers
                        r"enum\s+(?P<enum_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Enum name
                    ),
                    "decorator": re.compile(
                        r"^@(?P<decorator_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Decorator name
                        r"(?:\s*\((?P<parameters>[^)]*)\))?"  # Optional parameters
                    ),
                }
            )

        self.patterns = base_patterns
        self.modifiers = {
            "export",
            "default",
            "async",
            "static",
            "public",
            "private",
            "protected",
            "readonly",
            "abstract",
            "declare",
        }
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        """Parse JavaScript/TypeScript code content."""
        lines = content.split("\n")
        symbols = []
        brace_count = 0
        in_comment = False
        in_template = False
        pending_decorators = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Handle comments
            if line.startswith("//"):
                i += 1
                continue

            if "/*" in line and not in_template:
                in_comment = True
                if "*/" in line[line.index("/*") :]:
                    in_comment = False
                i += 1
                continue

            if in_comment:
                if "*/" in line:
                    in_comment = False
                i += 1
                continue

            # Handle template literals
            if "`" in line:
                in_template = not in_template

            if in_template:
                i += 1
                continue

            # Handle decorators (TypeScript)
            if self.language == "typescript" and line.startswith("@"):
                pending_decorators.append(line)
                i += 1
                continue

            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    try:
                        name = match.group(f"{kind}_name")
                        modifiers = set()
                        if "modifiers" in match.groupdict() and match.group("modifiers"):
                            modifiers = {m.strip() for m in match.group("modifiers").split()}
                        modifiers.update(pending_decorators)
                        pending_decorators = []

                        # Track braces for block scope
                        brace_count += line.count("{") - line.count("}")

                        symbol = CodeSymbol(
                            name=name,
                            kind=kind,
                            start_line=i,
                            end_line=i,
                            modifiers=modifiers,
                            parent=None,
                        )

                        # Find end of block
                        if "{" in line:
                            j = i + 1
                            while j < len(lines) and brace_count > 0:
                                brace_count += lines[j].count("{") - lines[j].count("}")
                                j += 1
                            symbol.end_line = j - 1
                            i = j - 1

                        symbols.append(symbol)
                        break
                    except IndexError:
                        # Skip if the name group doesn't exist
                        continue

            i += 1

        # Convert to Declarations for backward compatibility
        return [
            Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
            for symbol in symbols
        ]


def parse_javascript_or_typescript(
    file_path: str, content: str, language: str = "javascript"
) -> ParsedFileData:
    """Parse JavaScript or TypeScript code and return ParsedFileData."""
    parser = JstsParser(language)
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path, language=language, content=content, declarations=declarations
    )
