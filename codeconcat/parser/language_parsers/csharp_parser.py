"""C# code parser for CodeConcat."""

import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


def parse_csharp_code(file_path: str, content: str) -> Optional[ParsedFileData]:
    """Parse C# code and return declarations."""
    parser = CSharpParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="csharp",
        content=content,
        declarations=declarations
    )


class CSharpParser(BaseParser):
    """Parser for C# code."""

    def __init__(self):
        """Initialize the parser."""
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """Set up C#-specific patterns."""
        modifiers = r"(?:public|private|protected|internal)?\s*"
        class_modifiers = r"(?:static|abstract|sealed)?\s*"
        method_modifiers = r"(?:static|virtual|abstract|override)?\s*"
        type_pattern = r"(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+"

        self.patterns = {
            "class": re.compile(
                r"^\s*" + modifiers + class_modifiers +  # Access and class modifiers
                r"class\s+" +  # class keyword
                r"(?P<class_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Class name
            ),
            "interface": re.compile(
                r"^\s*" + modifiers +  # Access modifiers
                r"interface\s+" +  # interface keyword
                r"(?P<interface_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Interface name
            ),
            "method": re.compile(
                r"^\s*" + modifiers + method_modifiers +  # Access and method modifiers
                r"(?:async\s+)?" +  # Optional async
                type_pattern +  # Return type
                r"(?P<method_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)"  # Method name and args
            ),
            "property": re.compile(
                r"^\s*" + modifiers + method_modifiers +  # Access and property modifiers
                type_pattern +  # Property type
                r"(?P<property_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*{\s*(?:get|set)"  # Property name
            ),
            "enum": re.compile(
                r"^\s*" + modifiers +  # Access modifiers
                r"enum\s+" +  # enum keyword
                r"(?P<enum_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Enum name
            ),
            "struct": re.compile(
                r"^\s*" + modifiers +  # Access modifiers
                r"struct\s+" +  # struct keyword
                r"(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Struct name
            ),
            "delegate": re.compile(
                r"^\s*" + modifiers +  # Access modifiers
                r"delegate\s+" +  # delegate keyword
                type_pattern +  # Return type
                r"(?P<delegate_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\("  # Delegate name
            ),
            "event": re.compile(
                r"^\s*" + modifiers +  # Access modifiers
                r"event\s+" +  # event keyword
                type_pattern +  # Event type
                r"(?P<event_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Event name
            ),
            "namespace": re.compile(
                r"^\s*namespace\s+" +  # namespace keyword
                r"(?P<namespace_name>[a-zA-Z_][a-zA-Z0-9_.]*)"  # Namespace name
            ),
        }

    def _extract_name(self, match: re.Match, kind: str, line: str) -> Optional[str]:
        """Extract name from regex match."""
        if kind == "class":
            return match.group("class_name")
        elif kind == "interface":
            return match.group("interface_name")
        elif kind == "method":
            return match.group("method_name")
        elif kind == "property":
            return match.group("property_name")
        elif kind == "enum":
            return match.group("enum_name")
        elif kind == "struct":
            return match.group("struct_name")
        elif kind == "delegate":
            return match.group("delegate_name")
        elif kind == "event":
            return match.group("event_name")
        elif kind == "namespace":
            return match.group("namespace_name")
        return None

    def parse(self, content: str) -> List[Declaration]:
        """Parse C# code to identify classes, methods, properties, and other constructs."""
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        i = 0

        in_block = False
        block_start = 0
        block_name = ""
        block_kind = ""
        brace_count = 0
        in_comment = False
        in_attribute = False

        while i < len(lines):
            line = lines[i].strip()

            # Handle multi-line comments
            if "/*" in line:
                in_comment = True
            if "*/" in line:
                in_comment = False
                i += 1
                continue
            if in_comment or line.strip().startswith("//"):
                i += 1
                continue

            # Handle attributes
            if line.strip().startswith("["):
                in_attribute = True
            if in_attribute:
                if "]" in line:
                    in_attribute = False
                i += 1
                continue

            # Track braces and blocks
            if not in_block:
                for kind, pattern in self.patterns.items():
                    match = pattern.match(line)
                    if match:
                        block_name = self._extract_name(match, kind, line)
                        if not block_name:
                            continue

                        block_start = i
                        block_kind = kind
                        in_block = True
                        brace_count = line.count("{") - line.count("}")

                        # Handle one-line definitions
                        if ";" in line:
                            symbols.append(
                                CodeSymbol(
                                    name=block_name,
                                    kind=kind,
                                    start_line=i,
                                    end_line=i,
                                    modifiers=set(),
                                    parent=None,
                                )
                            )
                            in_block = False
                            break
                        elif brace_count == 0:
                            # Look ahead for opening brace or semicolon
                            j = i + 1
                            while j < len(lines) and not in_block:
                                next_line = lines[j].strip()
                                if next_line and not next_line.startswith("//"):
                                    if "{" in next_line:
                                        in_block = True
                                        brace_count = 1
                                    elif ";" in next_line:
                                        symbols.append(
                                            CodeSymbol(
                                                name=block_name,
                                                kind=kind,
                                                start_line=i,
                                                end_line=j,
                                                modifiers=set(),
                                                parent=None,
                                            )
                                        )
                                        in_block = False
                                        i = j
                                        break
                                j += 1
                            break
            else:
                brace_count += line.count("{") - line.count("}")

            # Check if block ends
            if in_block and brace_count == 0 and ("}" in line or ";" in line):
                symbols.append(
                    CodeSymbol(
                        name=block_name,
                        kind=block_kind,
                        start_line=block_start,
                        end_line=i,
                        modifiers=set(),
                        parent=None,
                    )
                )
                in_block = False

            i += 1

        # Process declarations
        processed_declarations = []
        seen_names = set()
        
        # First pass: add all declarations
        for symbol in symbols:
            if symbol.name not in seen_names:
                processed_declarations.append(
                    Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
                )
                seen_names.add(symbol.name)

        return processed_declarations
