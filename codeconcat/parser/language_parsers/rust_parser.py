import logging
import re

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError
from .base_parser import ParserInterface

logger = logging.getLogger(__name__)

# Basic Regex patterns for Rust constructs
# Catches 'use some::path::Item;', 'use some::path::{Item1, Item2};', 'use some::path::*;' etc.
USE_PATTERN = re.compile(r"^\s*use\s+((?:\w+|\*)::)?([\w\*\{\},\s:]+);")
# Matches fn name(...), pub fn name(...), async fn name(...), const fn name(...)
FUNCTION_PATTERN = re.compile(
    r"^\s*(?:pub(?:\(\w+\))?\s+)?(?:async\s+)?(?:const\s+)?(?:unsafe\s+)?fn\s+(?P<name>[\w_][\w\d_]*)\s*(?:<.*>)?\s*\(.*\)"
    r"(?:\s*->\s*[\w\W]+)?\s*(?:where\s+[\w\W]+)?\s*\{?"
)
# Matches struct Name { ... }, pub struct Name<T> { ... }
STRUCT_PATTERN = re.compile(
    r"^\s*(?:pub(?:\(\w+\))?\s+)?struct\s+(?P<name>[\w_][\w\d_]*)\s*(?:<.*>)?\s*(?:where\s+[\w\W]+)?\s*(?:;|\{)"
)
# Matches enum Name { ... }, pub enum Name<T> { ... }
ENUM_PATTERN = re.compile(
    r"^\s*(?:pub(?:\(\w+\))?\s+)?enum\s+(?P<name>[\w_][\w\d_]*)\s*(?:<.*>)?\s*\{?"
)
# Matches trait Name { ... }, pub trait Name<T> { ... }, unsafe trait Name { ... }
TRAIT_PATTERN = re.compile(
    r"^\s*(?:pub(?:\(\w+\))?\s+)?(?:unsafe\s+)?trait\s+(?P<name>[\w_][\w\d_]*)\s*(?:<.*>)?\s*(?:where\s+[\w\W]+)?\s*\{?"
)
# Matches impl Name { ... }, impl<T> Trait for Name { ... }
IMPL_PATTERN = re.compile(
    r"^\s*(?:unsafe\s+)?impl(?:<.*>)?\s+(?:(?P<trait>[\w\:]+(?:<.*>)?)\s+for\s+)?(?P<type>[\w\:]+(?:<.*>)?)\s*(?:where\s+[\w\W]+)?\s*\{?"
)
# Matches mod name;, pub mod name;
MOD_PATTERN = re.compile(r"^\s*(?:pub(?:\(\w+\))?\s+)?mod\s+(?P<name>[\w_][\w\d_]*);?")

# Doc comment patterns
DOC_COMMENT_SLASH_PATTERN = re.compile(r"^\s*///(.*)")
DOC_COMMENT_BLOCK_INNER_PATTERN = re.compile(r"^\s*//!?(.*)")
DOC_COMMENT_BLOCK_OUTER_PATTERN = re.compile(r"^\s*/\*\*!?\s?(.*)")
DOC_COMMENT_BLOCK_END_PATTERN = re.compile(r"(.*)\*/")


class RustParser(ParserInterface):
    """Basic Regex based parser for Rust code."""

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parses Rust code using Regex to find declarations and imports."""
        declarations = []
        imports: set[str] = set()
        lines = content.split("\n")
        doc_buffer: list[str] = []
        in_block_comment = False
        in_doc_comment = False
        current_module_stack: list[str] = []  # Basic module tracking
        bracket_level = 0

        try:
            logger.debug(f"Starting RustParser.parse (Regex) for file: {file_path}")
            for i, line in enumerate(lines):
                stripped_line = line.strip()

                # Track scope (simple brace counting)
                bracket_level += line.count("{")
                bracket_level -= line.count("}")
                if bracket_level < 0:
                    bracket_level = 0

                # Handle block comments /* ... */ (including doc comments /** ... */)
                if in_block_comment:
                    if "*/" in stripped_line:
                        in_block_comment = False
                        end_match = DOC_COMMENT_BLOCK_END_PATTERN.match(line.strip())
                        if in_doc_comment and end_match and end_match.group(1).strip():
                            doc_buffer.append(end_match.group(1).strip().lstrip("*").strip())
                        stripped_line = stripped_line.split("*/", 1)[1].strip()
                        in_doc_comment = False  # Doc comment ends with */
                    else:
                        if in_doc_comment:
                            doc_buffer.append(line.strip().lstrip("*").strip())
                        continue  # Skip lines entirely within block comments

                if stripped_line.startswith("/*"):
                    block_doc_match = DOC_COMMENT_BLOCK_OUTER_PATTERN.match(line.strip())
                    if block_doc_match:
                        in_block_comment = True
                        in_doc_comment = True
                        comment_content = block_doc_match.group(1)
                        if comment_content.endswith("*/"):
                            in_block_comment = False
                            in_doc_comment = False
                            end_match = DOC_COMMENT_BLOCK_END_PATTERN.match(comment_content)
                            doc_buffer = (
                                [end_match.group(1).strip().lstrip("*").strip()]
                                if end_match
                                else []
                            )
                        else:
                            doc_buffer = [comment_content.strip()]  # Start buffer
                        continue
                    else:
                        # Regular block comment
                        if "*/" not in stripped_line:
                            in_block_comment = True
                        stripped_line = stripped_line.split("/*", 1)[0].strip()
                        doc_buffer = []  # Regular block comments clear buffer

                # Handle line comments (//, ///, //!)
                if stripped_line.startswith("//"):
                    doc_slash_match = DOC_COMMENT_SLASH_PATTERN.match(stripped_line)
                    doc_block_inner_match = DOC_COMMENT_BLOCK_INNER_PATTERN.match(stripped_line)
                    if doc_slash_match:
                        doc_buffer.append(doc_slash_match.group(1).strip())
                    elif doc_block_inner_match:
                        # Inner block comments are module/crate level, less common before items
                        # Treat similarly to outer for now, maybe refine later
                        doc_buffer.append(doc_block_inner_match.group(1).strip())
                    else:
                        doc_buffer = []  # Regular line comment clears buffer
                    stripped_line = ""  # The rest of the line is comment

                if not stripped_line:
                    # Don't clear doc buffer on empty lines
                    continue

                # --- Parse Declarations and Imports --- #

                # Use statements (Imports)
                use_match = USE_PATTERN.match(stripped_line)
                if use_match:
                    # Extract the full path used
                    import_path = use_match.group(2).strip()
                    # Basic handling for group imports
                    if "{" in import_path and "}" in import_path and use_match.group(1):
                        prefix = use_match.group(1)
                        items = re.findall(r"\b\w+\b", import_path)
                        for item in items:
                            imports.add(f"{prefix}{item}")
                    else:
                        imports.add(
                            use_match.group(1) + import_path if use_match.group(1) else import_path
                        )
                    doc_buffer = []  # Clear buffer after use statement
                    continue

                # Function
                func_match = FUNCTION_PATTERN.match(stripped_line)
                if func_match:
                    name = func_match.group("name")
                    scope = "::".join(current_module_stack)
                    full_name = f"{scope}::{name}" if scope else name
                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind="function",
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    doc_buffer = []
                    continue

                # Struct
                struct_match = STRUCT_PATTERN.match(stripped_line)
                if struct_match:
                    name = struct_match.group("name")
                    scope = "::".join(current_module_stack)
                    full_name = f"{scope}::{name}" if scope else name
                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind="struct",
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    doc_buffer = []
                    continue

                # Enum
                enum_match = ENUM_PATTERN.match(stripped_line)
                if enum_match:
                    name = enum_match.group("name")
                    scope = "::".join(current_module_stack)
                    full_name = f"{scope}::{name}" if scope else name
                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind="enum",
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    doc_buffer = []
                    continue

                # Trait
                trait_match = TRAIT_PATTERN.match(stripped_line)
                if trait_match:
                    name = trait_match.group("name")
                    scope = "::".join(current_module_stack)
                    full_name = f"{scope}::{name}" if scope else name
                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind="trait",
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    doc_buffer = []
                    continue

                # Impl block
                impl_match = IMPL_PATTERN.match(stripped_line)
                if impl_match:
                    impl_type = impl_match.group("type")
                    impl_trait = impl_match.group("trait")
                    scope = "::".join(current_module_stack)
                    # Name the impl block uniquely if possible
                    name = (
                        f"impl {impl_trait} for {impl_type}" if impl_trait else f"impl {impl_type}"
                    )
                    full_name = f"{scope}::{name}" if scope else name
                    docstring = "\n".join(filter(None, doc_buffer))
                    # Represent the whole block as one 'impl' declaration
                    declarations.append(
                        Declaration(
                            kind="implementation",
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    doc_buffer = []
                    continue

                # Module
                mod_match = MOD_PATTERN.match(stripped_line)
                if mod_match:
                    name = mod_match.group("name")
                    scope = "::".join(current_module_stack)
                    full_name = f"{scope}::{name}" if scope else name
                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind="module",
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    # Basic tracking - assumes mods don't close immediately
                    # if stripped_line.endswith('{'): current_module_stack.append(name)
                    doc_buffer = []
                    continue

                # If line contains code but wasn't handled, clear doc buffer
                if stripped_line:
                    doc_buffer = []
                    # Basic scope exit for modules - Needs better tracking
                    # if stripped_line == '}' and current_module_stack and bracket_level < len(current_module_stack) -1:
                    #     current_module_stack.pop()

            logger.debug(
                f"Finished RustParser.parse (Regex) for file: {file_path}. Found {len(declarations)} declarations, {len(imports)} imports."
            )
            # TODO: Improve end_line detection
            return ParseResult(
                file_path=file_path,
                language="rust",
                content=content,
                declarations=declarations,
                imports=sorted(imports),
                engine_used="regex",
                token_stats=None,
                security_issues=[],
            )

        except Exception as e:
            logger.error(f"Error parsing Rust file {file_path} with Regex: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse Rust file ({type(e).__name__}) using Regex: {e}",
                file_path=file_path,
                original_exception=e,
            ) from e
