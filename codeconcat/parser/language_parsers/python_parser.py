"""Python code parser for CodeConcat."""

import logging
import re

# Moved imports back to top
from codeconcat.base_types import Declaration, ParseResult
from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class PythonParser(BaseParser):
    """Python language parser using regex-based pattern matching.

    This parser identifies Python declarations including classes, functions,
    constants, and variables. It extracts docstrings and recognizes common
    Python decorators.
    """

    def __init__(self):
        """Initialize the Python parser with regex patterns for Python syntax.

        Sets up patterns for:
        - Class definitions with optional base classes
        - Function definitions with decorators and type hints
        - Constants (ALL_CAPS naming convention)
        - Variables with type annotations

        Also configures Python-specific comment delimiters and block markers.
        """
        super().__init__()
        self.patterns = {
            "class": re.compile(
                r"^(?:@[-￿.]+(?:\([^)]*\))?\s+)*"  # Optional decorators
                r"class\s+(?P<n>[^\W\d][\w-￿_]*)"  # Class name
                r"(?:\s*\([^)]*\))?"  # Optional parent class
                r"\s*:",  # Class definition end
                re.UNICODE | re.MULTILINE,
            ),
            "function": re.compile(
                r"^(?:@[-￿.]+(?:\([^)]*\))?\s+)*"  # Optional decorators
                r"(?:async\s+)?def\s+(?P<n>[^\W\d][\w-￿_]*)"  # Function name
                r"(?:\s*\([^)]*?\))?"  # Function parameters (non-greedy)
                r"\s*(?:->[^:]+)?"  # Optional return type
                r"\s*:",  # Function end
                re.MULTILINE | re.DOTALL | re.VERBOSE | re.UNICODE,
            ),
            "constant": re.compile(
                r"^(?P<n>[A-Z][A-Z0-9_\u0080-￿]*)\s*"  # Constant name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]",  # Assignment but not comparison
                re.UNICODE | re.MULTILINE,
            ),
            "variable": re.compile(
                r"^(?P<n>[a-z_\u0080-\uFFFF][\w\u0080-\uFFFF_]*)\s*"  # Variable name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]",  # Assignment but not comparison
                re.UNICODE | re.MULTILINE,
            ),
        }
        self.block_start = ":"
        self.block_end = ""
        self.line_comment = "#"
        self.block_comment_start = '"""'
        self.block_comment_end = '"""'

        # Our recognized modifiers (for demonstration)
        self.modifiers = {
            "@classmethod",
            "@staticmethod",
            "@property",
            "@abstractmethod",
        }

    # Update signature to match ParserInterface
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse Python code and return a ParseResult object."""
        # Add error handling from the old parse_python function
        try:
            # Use file_path argument instead of self.current_file_path
            logger.debug(f"Starting PythonParser.parse for file: {file_path}")
            declarations = []
            imports = []
            lines = content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Skip empty lines and simple comments
                if not line or line.startswith("#"):
                    i += 1
                    continue

                # Handle 'import module' or 'import module1, module2'
                if line.startswith("import "):
                    parts = line[len("import ") :].split(",")
                    for part in parts:
                        module_name = part.strip().split(" as ")[0].split(".")[0]
                        if module_name:
                            imports.append(module_name.strip())
                    i += 1
                    continue

                # Handle 'from package import module' or 'from . import module'
                if line.startswith("from "):
                    parts = line.split(" import ")
                    if len(parts) > 0:
                        from_part = parts[0][len("from ") :].strip().split(".")[0]
                        if from_part:
                            imports.append(from_part.strip("."))

                        if len(parts) > 1:
                            import_names = parts[1].replace("(", "").replace(")", "").split(",")
                            for name in import_names:
                                module_name = name.strip().split(" as ")[0]
                                if module_name and module_name != "*":
                                    imports.append(module_name.strip())
                    i += 1
                    continue

                # Collect decorators
                decorators = []
                while line.startswith("@"):
                    decorator = line
                    j = i + 1
                    while j < len(lines) and "(" in decorator and ")" not in decorator:
                        decorator += " " + lines[j].strip()
                        j += 1
                    decorators.append(decorator)
                    i = j if j > i else i + 1
                    if i >= len(lines):
                        break
                    line = lines[i].strip()

                # Try each pattern
                for kind, pattern in self.patterns.items():
                    logger.debug(f"Executing {kind}_pattern.finditer...")
                    matches = list(pattern.finditer(line))  # Materialize iterator
                    logger.debug(
                        f"Finished {kind}_pattern.finditer. Found {len(matches)} potential matches."
                    )
                    for match in matches:
                        name = match.group("n")
                        if not name:
                            continue

                        end_line = i
                        docstring = ""
                        if ":" in line:
                            base_indent = len(lines[i]) - len(line)
                            j = i + 1

                            while j < len(lines):
                                logger.debug(
                                    f"[PyParse Loop 1] Checking line {j + 1} for docstring/block start..."
                                )
                                next_line = lines[j].strip()
                                if next_line and not next_line.startswith("#"):
                                    curr_indent = len(lines[j]) - len(lines[j].lstrip())
                                    if curr_indent > base_indent:
                                        if next_line.startswith('"""') or next_line.startswith("'"):
                                            logger.debug(
                                                f"[PyParse Loop 1] Found potential docstring start at line {j + 1}"
                                            )
                                            quote_char = next_line[0] * 3
                                            if (
                                                next_line.endswith(quote_char)
                                                and len(next_line) > 6
                                            ):
                                                docstring = next_line[3:-3].strip()
                                                logger.debug(
                                                    f"[PyParse Loop 1] Found single-line docstring at line {j + 1}"
                                                )
                                                j += 1
                                            else:
                                                doc_lines = [next_line[3:].strip()]
                                                k = j + 1
                                                while k < len(lines):
                                                    logger.debug(
                                                        f"[PyParse Loop 1.1] Checking line {k + 1} for docstring end..."
                                                    )
                                                    doc_line = lines[k].strip()
                                                    if doc_line.endswith(quote_char):
                                                        doc_lines.append(doc_line[:-3].strip())
                                                        logger.debug(
                                                            f"[PyParse Loop 1.1] Found docstring end at line {k + 1}"
                                                        )
                                                        j = k + 1
                                                        break
                                                    doc_lines.append(doc_line)
                                                    k += 1
                                                else:
                                                    logger.warning(
                                                        f"[PyParse Loop 1.1] Reached end of file while searching for docstring end starting near line {j + 1} in {file_path}"
                                                    )
                                                    j = k
                                                docstring = "\n".join(doc_lines).strip()
                                        logger.debug(
                                            f"[PyParse Loop 1] Finished docstring search at line {j + 1}"
                                        )
                                        break
                                else:
                                    logger.debug(
                                        f"[PyParse Loop 1] Skipping empty/comment line {j + 1}"
                                    )

                                j += 1
                            else:
                                logger.debug(
                                    f"[PyParse Loop 1] Reached end of file while searching for docstring/block start near line {i + 1} in {file_path}"
                                )

                            block_lines = []
                            start_j = j
                            logger.debug(
                                f"[PyParse Loop 2] Starting block search from line {start_j + 1}"
                            )
                            while j < len(lines):
                                logger.debug(
                                    f"[PyParse Loop 2] Checking line {j + 1} for block end..."
                                )
                                curr_line_full = lines[j]
                                curr_line_stripped = curr_line_full.strip()
                                if curr_line_stripped and not curr_line_stripped.startswith("#"):
                                    curr_indent = len(curr_line_full) - len(curr_line_full.lstrip())
                                    if curr_indent <= base_indent:
                                        logger.debug(
                                            f"[PyParse Loop 2] Found block end at line {j + 1} (indent <= base)"
                                        )
                                        end_line = j - 1
                                        break
                                block_lines.append(curr_line_full)

                                if j > start_j + 1000:
                                    logger.warning(
                                        f"Python parser stopped searching for block end after 1000 lines in {file_path} starting near line {i + 1}. Potential issue."
                                    )
                                    end_line = j
                                    break
                                j += 1
                            else:
                                logger.debug(
                                    f"[PyParse Loop 2] Reached end of file while searching for block end near line {start_j + 1} in {file_path}"
                                )
                                end_line = j - 1

                            # Recursive call needs file_path argument now
                            # TODO: Decide if recursive parsing is the right approach here. It might be complex.
                            # For now, let's skip the recursive call and focus on top-level declarations.
                            # nested_declarations = self.parse("\n".join(block_lines), file_path)
                            # for decl in nested_declarations.declarations: # Access declarations from ParseResult
                            #     decl.start_line += i + 1
                            #     decl.end_line += i + 1
                            #     declarations.append(decl)
                            # Need to handle nested imports too if recursion is used.
                            # Simplification: Don't parse nested blocks recursively for now.

                        elif "=" in line:
                            end_line = i

                        declaration = Declaration(
                            kind=kind,
                            name=name,
                            start_line=i + 1,  # Convert to 1-based line numbering
                            end_line=end_line + 1,  # Convert to 1-based line numbering
                            docstring=docstring,
                            modifiers={d for d in decorators if d in self.modifiers},
                        )
                        declarations.append(declaration)
                        logger.debug(f"Found declaration: {kind} {name}")
                        i = end_line + 1
                        break
                else:
                    i += 1

            imports = list(set(imports))  # Remove duplicates
            logger.debug(
                f"Finished PythonParser.parse for file: {file_path}. Found {len(declarations)} declarations, {len(imports)} unique imports."
            )
            # Correctly initialize ParseResult with valid fields
            return ParseResult(
                declarations=declarations,
                imports=imports,
                engine_used="regex",  # Specify engine used
                parser_quality="full",
                # ast_root, error are None by default
            )
        except Exception as e:
            # Wrap internal parser errors in LanguageParserError
            # Re-raise error with context
            logger.error(f"Error parsing Python file {file_path}: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse Python file ({type(e).__name__}): {e}",
                file_path=file_path,
                original_exception=e,
            ) from e

    def _find_end_of_block(self, lines: list[str], start_line: int) -> int:
        """Helper to find the end line of a Python code block based on indentation."""
        raise NotImplementedError("This method is not implemented in base parser")
