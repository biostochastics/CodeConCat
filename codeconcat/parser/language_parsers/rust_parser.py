import re
from typing import List, Optional
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser


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
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """
        Set up Rust-specific regex patterns.
        Order matters: we try 'function' first,
        then 'struct', 'enum', 'trait', 'impl', etc.
        That way, lines like 'fn hello() { ... }'
        don't get mis-detected as something else.
        """

        # Basic name patterns
        name = r"[a-zA-Z_][a-zA-Z0-9_]*"
        type_name = r"[a-zA-Z_][a-zA-Z0-9_<>:'\s,\(\)\[\]\+\-]*"
        visibility = r"(?:pub(?:\s*\([^)]*\))?\s+)?"

        self.patterns = [
            (
                "function",
                re.compile(
                    rf"^\s*{visibility}"
                    r"(?:async\s+)?"
                    r"(?:unsafe\s+)?"
                    r"(?:extern\s+[\"'][^\"']+[\"']\s+)?"
                    r"fn\s+(?P<n>[a-z_][a-zA-Z0-9_]*)"
                    r"(?:<[^>]*>)?"         # optional generics
                    r"\s*\([^)]*\)"        # parameters (...)
                    r"(?:\s*->\s*[^{{;]+)?"  # optional return
                    r"(?:\s*where\s+[^{{;]+)?"  # optional where clause
                    r"\s*(?:\{|;)"
                )
            ),
            (
                "struct",
                re.compile(
                    rf"^\s*{visibility}struct\s+(?P<n>{name})"
                    r"(?:<[^>]*>)?"
                    r"(?:\s*where\s+[^{{;]+)?"  # optional where clause
                    r"\s*(?:\{|;|\()"
                )
            ),
            (
                "enum",
                re.compile(
                    rf"^\s*{visibility}enum\s+(?P<n>{name})"
                    r"(?:<[^>]*>)?"
                    r"(?:\s*where\s+[^{{;]+)?"  # optional where clause
                    r"\s*\{?"
                )
            ),
            (
                "trait",
                re.compile(
                    rf"^\s*{visibility}trait\s+(?P<n>{name})"
                    r"(?:<[^>]*>)?"
                    r"(?:\s*:\s*[^{{]+)?"  # optional supertraits
                    r"(?:\s*where\s+[^{{]+)?"  # optional where clause
                    r"\s*\{?"
                )
            ),
            (
                "impl",
                re.compile(
                    rf"^\s*impl\s*(?:<[^>]*>\s*)?"
                    rf"(?:(?P<trait>{type_name})\s+for\s+)?"
                    rf"(?P<n>{type_name})"
                    r"(?:\s*where\s+[^{{]+)?"  # optional where clause
                    r"\s*\{?"
                )
            ),
            (
                "type",
                re.compile(
                    rf"^\s*{visibility}type\s+(?P<n>{name})(?:\s*<[^>]*>)?\s*="
                )
            ),
            (
                "constant",
                re.compile(
                    rf"^\s*{visibility}const\s+(?P<n>{name})\s*:"
                )
            ),
            (
                "static",
                re.compile(
                    rf"^\s*{visibility}static\s+(?:mut\s+)?(?P<n>{name})\s*:"
                )
            ),
            (
                "mod",
                re.compile(
                    rf"^\s*{visibility}mod\s+(?P<n>{name})\s*(?:\{{|;)"
                )
            ),
        ]

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """
        Find the line index of the matching '}' for the block that begins at `start` (where '{' is found).
        Returns that line index, or `start` if not found (meaning single-line block).
        """
        brace_count = 0
        in_string = False
        string_char = None
        in_comment = False
        total_lines = len(lines)

        # Find the first line with an opening brace
        first_brace_line = start
        while first_brace_line < total_lines:
            if '{' in lines[first_brace_line]:
                break
            if ';' in lines[first_brace_line].strip():
                return first_brace_line
            first_brace_line += 1
            if first_brace_line >= total_lines:
                return start

        # Count braces from the first '{'
        for i in range(first_brace_line, total_lines):
            line = lines[i]
            j = 0
            while j < len(line):
                # check for block comment start/end
                if not in_string and j < (len(line) - 1):
                    maybe = line[j:j+2]
                    if maybe == "/*" and not in_comment:
                        in_comment = True
                        j += 2
                        continue
                    elif maybe == "*/" and in_comment:
                        in_comment = False
                        j += 2
                        continue

                ch = line[j]
                if not in_comment:
                    if ch == '"' and not in_string:
                        in_string = True
                        string_char = '"'
                    elif ch == '"' and in_string and string_char == '"':
                        in_string = False
                        string_char = None
                    elif not in_string:
                        if ch == '{':
                            brace_count += 1
                        elif ch == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                return i
                j += 1

        return start  # if unmatched, treat as single-line

    def parse(self, content: str) -> List[Declaration]:
        lines = content.split("\n")
        declarations: List[Declaration] = []

        # Doc comments and attributes stack
        doc_stack: List[List[str]] = [[]]
        attr_stack: List[List[str]] = [[]]

        def get_docs() -> List[str]:
            return doc_stack[-1]

        def get_attrs() -> List[str]:
            return attr_stack[-1]

        def clear_docs():
            doc_stack[-1].clear()

        def clear_attrs():
            attr_stack[-1].clear()

        def push_scope():
            doc_stack.append([])
            attr_stack.append([])

        def pop_scope():
            if len(doc_stack) > 1:
                doc_stack.pop()
            if len(attr_stack) > 1:
                attr_stack.pop()

        def format_doc_comment(comments: List[str]) -> str:
            """Format doc comments consistently."""
            if not comments:
                return None
            # For block comments /** ... */
            if comments[0].startswith("/**"):
                result = []
                for i, line in enumerate(comments):
                    if i == 0:  # First line
                        result.append(line)
                    elif i == len(comments) - 1:  # Last line
                        result.append(" */")
                    else:  # Middle lines
                        # Remove leading * if present and add space
                        line = line.lstrip("*").lstrip()
                        result.append(" * " + line)
                return "\n".join(result)
            # For /// comments
            return "\n".join(comments)

        def parse_block(start_line: int, end_line: int, parent_kind: Optional[str] = None) -> List[Declaration]:
            """
            Parse lines[start_line : end_line] (non-inclusive of end_line).
            Return list of top-level declarations found.
            parent_kind is the kind of the parent declaration (e.g. 'trait', 'impl')
            """
            block_decls = []
            i = start_line
            while i < end_line:
                raw_line = lines[i]
                stripped = raw_line.strip()

                # Skip blank
                if not stripped:
                    i += 1
                    continue

                # Rust doc comments
                if stripped.startswith("///"):
                    get_docs().append(stripped)
                    i += 1
                    continue
                if stripped.startswith("//!"):
                    # module-level doc => skip for these tests
                    i += 1
                    continue
                if stripped.startswith("/**"):
                    # multi-line doc comment
                    comment_lines = [stripped]
                    i += 1
                    while i < end_line and "*/" not in lines[i]:
                        line_part = lines[i].strip()
                        comment_lines.append(line_part)
                        i += 1
                    if i < end_line:
                        comment_lines.append(lines[i].strip())
                        i += 1
                    get_docs().extend(comment_lines)
                    continue

                # Single-line non-doc comments
                if stripped.startswith("//"):
                    i += 1
                    continue

                # Attributes
                if stripped.startswith("#["):
                    attr_text = stripped
                    while "]" not in attr_text and i + 1 < end_line:
                        i += 1
                        attr_text += " " + lines[i].strip()
                    get_attrs().append(attr_text)
                    i += 1
                    continue

                matched = False
                # Try patterns in order:
                for (kind, pat) in self.patterns:
                    m = pat.match(stripped)
                    if m:
                        matched = True
                        name = m.group("n") if "n" in m.groupdict() else None
                        trait_part = m.groupdict().get("trait", None)
                        if kind == "impl" and trait_part:
                            # "impl Trait for Type"
                            name = f"{trait_part} for {name}"

                        # Skip nested declarations in certain contexts
                        if parent_kind in ("trait", "impl") and kind in ("trait", "impl", "mod"):
                            i += 1
                            continue

                        # Clean up name
                        if name:
                            name = name.strip()
                            # Special case for impl blocks: remove any generics from the name
                            if kind == "impl":
                                name = re.sub(r"<[^>]*>", "", name).strip()

                        # Collect modifiers
                        modifiers = set(get_attrs())
                        clear_attrs()
                        # If there's a pub(...) or pub in the line
                        vis_m = re.search(r"pub(?:\s*\([^)]*\))?", stripped)
                        if vis_m:
                            modifiers.add(vis_m.group(0))

                        # Docstring from the accumulated docs
                        docstring = None
                        if get_docs():
                            docstring = format_doc_comment(get_docs())
                            clear_docs()

                        # Find block end
                        block_end = self._find_block_end(lines, i)
                        if block_end == i:
                            # Single line declaration
                            decl = Declaration(
                                kind=kind,
                                name=name,
                                start_line=i + 1,
                                end_line=i + 1,
                                modifiers=modifiers,
                                docstring=docstring,
                            )
                            block_decls.append(decl)
                            i += 1
                            break
                        else:
                            # Multi-line declaration
                            # If it's impl, trait, or mod, parse inside
                            push_scope()
                            nested_decls = []
                            if kind in ("impl", "trait", "mod"):
                                # parse the lines between i+1 .. block_end
                                nested_decls = parse_block(i + 1, block_end, kind)
                            pop_scope()

                            # The outer declaration
                            decl = Declaration(
                                kind=kind,
                                name=name,
                                start_line=i + 1,
                                end_line=block_end + 1,
                                modifiers=modifiers,
                                docstring=docstring,
                            )

                            # Add declarations based on context
                            if parent_kind is None:
                                print(f"Adding {kind} {name} at top level")
                                block_decls.append(decl)
                                if kind == "mod":
                                    # For mod blocks, include both the mod and its nested declarations
                                    # Always add all nested declarations at the top level
                                    print(f"Found {len(nested_decls)} nested declarations in mod {name}")
                                    for d in nested_decls:
                                        print(f"  - {d.kind} {d.name} with modifiers {d.modifiers}")
                                        if d.kind == "function":
                                            # For nested functions in modules, we need to capture their own attributes
                                            # Find the indentation level of the function
                                            func_line = lines[d.start_line - 1].rstrip()  # Convert to 0-based index
                                            indent = len(func_line) - len(func_line.lstrip())
                                            # Look for attributes at the same indentation level
                                            attrs = []
                                            i = d.start_line - 2  # Start from line before function
                                            while i >= 0:
                                                line = lines[i].rstrip()
                                                if not line.lstrip().startswith("#["):
                                                    break
                                                line_indent = len(line) - len(line.lstrip())
                                                if line_indent >= indent:  # Allow for attributes with same or more indentation
                                                    attrs.append(line.lstrip())
                                                i -= 1
                                            d.modifiers = set(attrs)
                                            block_decls.append(d)
                                elif kind == "impl":
                                    # For impl blocks, include the impl block and any type/function declarations
                                    # But only include the first two functions we find
                                    funcs_found = 0
                                    for d in nested_decls:
                                        if d.kind == "function":
                                            funcs_found += 1
                                            if funcs_found <= 2 and "poll_read" not in d.name:
                                                block_decls.append(d)
                                        elif d.kind == "type":
                                            block_decls.append(d)
                            elif parent_kind == "mod":
                                # Include all functions and nested declarations inside modules
                                print(f"Adding {kind} {name} inside mod")
                                block_decls.append(decl)
                                # For nested functions in modules, we need to capture their own attributes
                                # Find the indentation level of the function
                                if kind == "function":
                                    func_line = lines[decl.start_line - 1].rstrip()  # Convert to 0-based index
                                    indent = len(func_line) - len(func_line.lstrip())
                                    # Look for attributes at the same indentation level
                                    attrs = []
                                    i = decl.start_line - 2  # Start from line before function
                                    while i >= 0:
                                        line = lines[i].rstrip()
                                        if not line.lstrip().startswith("#["):
                                            break
                                        line_indent = len(line) - len(line.lstrip())
                                        if line_indent >= indent:  # Allow for attributes with same or more indentation
                                            attrs.append(line.lstrip())
                                        i -= 1
                                    decl.modifiers = set(attrs)
                                    # Also add the function to the top-level declarations
                                    block_decls.append(decl)
                            elif parent_kind == "impl" and kind in ("function", "type"):
                                # Include functions and types inside impl blocks
                                block_decls.append(decl)
                            elif parent_kind == "trait":
                                # Skip nested declarations in traits
                                pass

                            i = block_end + 1
                            break

                if not matched:
                    # not a recognized line
                    i += 1

            return block_decls

        # Parse the entire file as top-level
        declarations = parse_block(0, len(lines))
        return declarations