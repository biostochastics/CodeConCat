"""Rust code parser for CodeConcat."""

import re
from typing import Dict, List, Pattern

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


class RustParser(BaseParser):
    """Rust language parser."""

    def _setup_patterns(self):
        """Set up Rust-specific patterns."""
        self.patterns = {
            "function": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?(?:async\s+)?)"  # Visibility and async
                r"fn\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Function name
                r"\s*(?:<[^>]*>)?"  # Optional generic parameters
                r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
                r"(?:\s*->\s*(?P<return_type>[^{;]+))?"  # Optional return type
            ),
            "struct": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
                r"struct\s+(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Struct name
                r"(?:\s*<[^>]*>)?"  # Optional generic parameters
            ),
            "enum": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
                r"enum\s+(?P<enum_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Enum name
                r"(?:\s*<[^>]*>)?"  # Optional generic parameters
            ),
            "trait": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?(?:unsafe\s+)?)"  # Visibility and safety
                r"trait\s+(?P<trait_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Trait name
                r"(?:\s*<[^>]*>)?"  # Optional generic parameters
                r"(?:\s*:\s*(?P<super_traits>[^{]+))?"  # Optional super traits
            ),
            "impl": re.compile(
                r"^(?P<modifiers>(?:unsafe\s+)?)"  # Safety
                r"impl(?:\s*<[^>]*>)?\s*"  # Optional generic parameters
                r"(?P<impl_trait>(?:[^{]+)\s+for\s+)?"  # Optional trait being implemented
                r"(?P<impl_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Type name
                r"(?:\s*<[^>]*>)?"  # Optional generic parameters
            ),
            "const": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
                r"const\s+(?P<const_name>[A-Z_][A-Z0-9_]*)"  # Constant name
                r"(?::\s*(?P<type>[^=]+))?"  # Type annotation
                r"\s*="  # Assignment
            ),
            "static": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
                r"static\s+(?:mut\s+)?"  # Mutability
                r"(?P<static_name>[A-Z_][A-Z0-9_]*)"  # Static name
                r"(?::\s*(?P<type>[^=]+))?"  # Type annotation
                r"\s*="  # Assignment
            ),
            "type": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
                r"type\s+(?P<type_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Type alias name
                r"(?:\s*<[^>]*>)?"  # Optional generic parameters
                r"(?:\s*=\s*(?P<type_value>[^;]+))?"  # Type value
            ),
            "macro": re.compile(
                r"^(?P<modifiers>(?:#\[macro_export\]\s*)?)"  # Export attribute
                r"macro_rules!\s+(?P<macro_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Macro name
            ),
            "module": re.compile(
                r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
                r"mod\s+(?P<module_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Module name
            ),
        }

        self.modifiers = {
            "pub",
            "async",
            "unsafe",
            "mut",
            "const",
            "static",
            "extern",
            "default",
            "#[macro_export]",
        }
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        """Parse Rust code content."""
        lines = content.split("\n")
        symbols = []
        brace_count = 0
        in_comment = False
        current_impl = None
        pending_attributes = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Handle attributes
            if line.startswith("#["):
                pending_attributes.append(line)
                i += 1
                continue

            # Handle comments
            if line.startswith("//"):
                i += 1
                continue

            if "/*" in line and not in_comment:
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

            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name_group = f"{kind}_name"
                    name = match.group(name_group)
                    modifiers = set()
                    if "modifiers" in match.groupdict() and match.group("modifiers"):
                        modifiers = {m.strip() for m in match.group("modifiers").split()}
                    modifiers.update(pending_attributes)
                    pending_attributes = []

                    # Create symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=i,
                        modifiers=modifiers,
                        parent=current_impl if kind == "function" else None,
                    )

                    # Handle block-level constructs
                    if "{" in line:
                        brace_count = line.count("{")
                        j = i + 1
                        while j < len(lines) and brace_count > 0:
                            line = lines[j].strip()
                            if not line.startswith("//"):
                                brace_count += line.count("{") - line.count("}")
                            j += 1
                        symbol.end_line = j - 1
                        i = j - 1

                        # Update current impl context
                        if kind == "impl":
                            current_impl = symbol

                    symbols.append(symbol)
                    break

            i += 1

        # Convert to Declarations for backward compatibility
        return [
            Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
            for symbol in symbols
        ]


def parse_rust_code(file_path: str, content: str) -> ParsedFileData:
    """Parse Rust code and return ParsedFileData."""
    parser = RustParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path, language="rust", content=content, declarations=declarations
    )
