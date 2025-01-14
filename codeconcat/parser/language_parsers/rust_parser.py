"""Rust code parser for CodeConcat."""
import re
from typing import List, Optional
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


def parse_rust(file_path: str, content: str) -> Optional[ParsedFileData]:
    """Parse Rust code and return declarations."""
    parser = RustParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="rust",
        content=content,
        declarations=declarations
    )


class RustParser(BaseParser):
    """Rust language parser."""

    def __init__(self):
        """Initialize the parser."""
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """Set up Rust-specific patterns."""
        # Common patterns
        name = r"[a-zA-Z_][a-zA-Z0-9_]*"
        # We allow somewhat lenient type names here to handle generics, lifetimes, etc.
        type_name = r"[a-zA-Z_][a-zA-Z0-9_<>:'\s,\(\)\[\]\+\-]*"
        visibility = r"(?:pub(?:\s*\([^)]*\))?\s+)?"

        # Base patterns
        self.patterns = {
            "struct": re.compile(
                rf"^[^/]*{visibility}struct\s+(?P<n>[A-Z][a-zA-Z0-9_]*)(?:<[^>]*>)?(?:\s*where\s+[^{{]+)?\s*(?:\{{|;|\()"
            ),
            "enum": re.compile(
                rf"^[^/]*{visibility}enum\s+(?P<n>[A-Z][a-zA-Z0-9_]*)(?:<[^>]*>)?(?:\s*where\s+[^{{]+)?\s*\{{"
            ),
            "trait": re.compile(
                rf"^[^/]*{visibility}trait\s+(?P<n>[A-Z][a-zA-Z0-9_]*)(?:<[^>]*>)?(?:\s*:\s*[^{{]+)?(?:\s*where\s+[^{{]+)?\s*\{{"
            ),
            "impl": re.compile(
                # Optional trait impl: trait_name for TypeName
                rf"^[^/]*impl\s+(?:<[^>]*>\s*)?(?:(?P<trait>[A-Z][a-zA-Z0-9_]*(?:<[^>]*>)?)\s+for\s+)?(?P<n>{type_name})(?:\s*where\s+[^{{]+)?\s*\{{"
            ),
            "function": re.compile(
                rf"^[^/]*{visibility}(?:async\s+)?(?:unsafe\s+)?(?:extern\s+[\"'][^\"']+[\"']\s+)?fn\s+(?P<n>[a-z_][a-zA-Z0-9_]*)(?:<[^>]*>)?\s*\([^)]*\)(?:\s*->\s*[^{{;]+)?(?:\s*where\s+[^{{]+)?\s*(?:\{{|;)"
            ),
            "type": re.compile(
                rf"^[^/]*{visibility}type\s+(?P<n>{name})(?:\s*<[^>]*>)?\s*="
            ),
            "constant": re.compile(
                rf"^[^/]*{visibility}const\s+(?P<n>{name})\s*:"
            ),
            "static": re.compile(
                rf"^[^/]*{visibility}static\s+(?:mut\s+)?(?P<n>{name})\s*:"
            ),
            "mod": re.compile(
                rf"^[^/]*{visibility}mod\s+(?P<n>{name})\s*(?:\{{|;)"
            ),
        }

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """Find the end of a block starting at the given line index in `lines`."""
        brace_count = 0
        in_string = False
        string_char = None
        in_comment = False
        line_count = len(lines)
        first_line = lines[start]

        # Quick check for one-line items (e.g. 'pub struct Foo;')
        # if there's no '{' or '(' in the line, we treat it as a single line
        if "{" not in first_line and "(" not in first_line:
            return start

        # Initialize brace_count from first line
        for char in first_line:
            if char == '"':
                if not in_string:
                    in_string = True
                    string_char = char
                elif string_char == char:
                    in_string = False
                    string_char = None
            elif not in_string:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1

        # If after scanning the first line we have no open braces, treat as single-line
        if brace_count == 0:
            return start

        # Otherwise, keep scanning subsequent lines until braces match
        for i in range(start + 1, line_count):
            line = lines[i]

            # We handle single-line comments quickly
            if line.strip().startswith("//"):
                continue

            # Handle multi-line comment boundaries
            j = 0
            while j < len(line):
                # Check for multi-line comment start/end
                if j < len(line) - 1:
                    pair = line[j : j + 2]
                    if pair == "/*" and not in_string:
                        in_comment = True
                        j += 2
                        continue
                    elif pair == "*/" and in_comment:
                        in_comment = False
                        j += 2
                        continue

                char = line[j]

                # String toggling
                if char == '"' and not in_comment:
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif string_char == char:
                        in_string = False
                        string_char = None
                elif not in_string and not in_comment:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            return i
                j += 1

        # Fallback: if we never found a matching brace, return start
        return start

    def parse(self, content: str) -> List[Declaration]:
        """Parse Rust code content."""
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        symbol_stack: List[CodeSymbol] = []

        brace_depth = 0

        # We hold onto doc-comments/attributes until we see a matching declaration
        current_doc_comments: List[str] = []
        current_attributes: List[str] = []

        def pop_symbols_up_to(depth: int, line_idx: int):
            """Pop symbols from stack up to given depth."""
            while symbol_stack and int(symbol_stack[-1].modifiers.get("_brace_depth", "0")) >= depth:
                top = symbol_stack.pop()
                top.end_line = line_idx
                symbols.append(top)

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip blank lines
            if not stripped:
                i += 1
                continue

            # Handle single-line doc comments
            if stripped.startswith("///") or stripped.startswith("//!"):
                current_doc_comments.append(stripped)
                i += 1
                continue

            # Handle multi-line doc comments (/** ... */)
            if stripped.startswith("/**"):
                current_doc_comments.append(stripped)
                # keep reading until '*/'
                while i + 1 < len(lines) and "*/" not in lines[i]:
                    i += 1
                    current_doc_comments.append(lines[i].strip())
                i += 1
                continue

            # Handle other single-line comments, ignore them
            if stripped.startswith("//"):
                i += 1
                continue

            # Handle attributes #[...]
            if stripped.startswith("#["):
                # Accumulate until the closing ']'
                attr_line = stripped
                while "]" not in attr_line and i + 1 < len(lines):
                    i += 1
                    attr_line += " " + lines[i].strip()
                current_attributes.append(attr_line)
                i += 1
                continue

            matched = False

            # Check if we have a closing brace
            if stripped.startswith("}"):
                brace_depth -= 1
                # Pop anything that was opened at deeper or same depth
                pop_symbols_up_to(brace_depth + 1, i + 1)
                i += 1
                continue

            # Otherwise, try to match known declarations
            for kind, pattern in self.patterns.items():
                m = pattern.match(stripped)
                if m:
                    matched = True
                    name = m.group("n")

                    # For impl, store `Trait for Type` if needed
                    if kind == "impl" and m.group("trait"):
                        name = f"{m.group('trait')} for {name}"

                    # Build modifiers
                    modifiers = {}
                    # Attach visibility (pub...), if present
                    if "pub" in stripped:
                        # e.g. pub or pub(crate)
                        vis_m = re.search(r"pub(?:\s*\([^)]*\))?", stripped)
                        if vis_m:
                            modifiers["pub"] = vis_m.group(0)

                    # Attach any attributes and docstrings we collected
                    for attr in current_attributes:
                        modifiers[attr] = attr
                    current_attributes.clear()

                    if current_doc_comments:
                        modifiers["_docstring"] = "\n".join(current_doc_comments)
                    current_doc_comments.clear()

                    # Find block end if it contains '{'
                    block_end = i
                    if "{" in stripped:
                        brace_depth += 1
                        modifiers["_brace_depth"] = str(brace_depth)
                        block_end = self._find_block_end(lines, i)

                        # Create and push the symbol
                        symbol = CodeSymbol(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=block_end + 1,
                            modifiers=modifiers,
                        )
                        symbol_stack.append(symbol)
                    else:
                        # If there's no block, or it's a one-liner
                        block_end = self._find_block_end(lines, i)
                        symbol = CodeSymbol(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=block_end + 1,
                            modifiers=modifiers,
                        )
                        symbols.append(symbol)

                    # Advance our main loop to the block end (or same line)
                    i = block_end
                    break

            if not matched:
                # If nothing matched, just move on
                i += 1

        # Pop any remaining symbols (e.g. unclosed blocks or file end)
        while symbol_stack:
            top = symbol_stack.pop()
            top.end_line = len(lines)
            symbols.append(top)

        # Convert to Declarations, filtering out internal modifiers
        declarations = []
        for sym in symbols:
            # Filter out internal modifiers like _brace_depth, _docstring
            public_mods = {}
            docstring = None
            for k, v in sym.modifiers.items():
                if k.startswith("_docstring"):
                    docstring = v
                elif not k.startswith("_"):
                    public_mods[k] = v

            declarations.append(
                Declaration(
                    kind=sym.kind,
                    name=sym.name,
                    start_line=sym.start_line,
                    end_line=sym.end_line,
                    modifiers=set(public_mods.values()),
                    docstring=docstring,
                )
            )

        return declarations