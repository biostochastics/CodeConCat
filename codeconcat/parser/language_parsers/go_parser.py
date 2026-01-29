# file: codeconcat/parser/language_parsers/go_parser.py
import logging
import re

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# Regex patterns for Go constructs
FUNC_PATTERN = re.compile(r"^func\s+(?:\(\s*\w+\s+\*?\w+\s*\)\s+)?(?P<name>[\w\d_]+)\s*\(.*\)")
TYPE_PATTERN = re.compile(r"^type\s+(?P<name>[\w\d_]+)\s+(?:struct|interface|\w+)")
VAR_CONST_PATTERN = re.compile(
    r"^(?:var|const)\s+(?:\((?P<multiline>.*?)\)|(?P<name_single>[\w\d_]+))",
    re.DOTALL | re.MULTILINE,
)
IMPORT_PATTERN = re.compile(
    r"^import\s+(?:\((?P<multiline_imports>.*?)\)|\"(?P<single_import>[^\"]+)\")",
    re.DOTALL | re.MULTILINE,
)
SINGLE_IMPORT_IN_MULTI_PATTERN = re.compile(r"\"([^\"]+)\"")
DOC_COMMENT_PATTERN = re.compile(r"^//\s*(?P<doc>.*)")
PACKAGE_PATTERN = re.compile(r"^package\s+(\w+)")


# Inherit from BaseParser
class GoParser(BaseParser):
    """Parses Go code using Regex."""

    # Update signature to match ParserInterface
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parses the given Go code content.

        Args:
            content: The Go code as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object containing declarations and imports.
        """
        declarations = []
        imports: set[str] = set()
        lines = content.split("\n")
        doc_buffer: list[str] = []

        try:
            logger.debug(f"Starting GoParser.parse (Regex) for file: {file_path}")
            for i, line in enumerate(lines):
                stripped_line = line.strip()

                if not stripped_line:
                    doc_buffer = []  # Reset doc buffer on empty lines
                    continue

                # Package
                package_match = PACKAGE_PATTERN.match(line)
                if package_match:
                    package_match.group(1)
                    doc_buffer = []
                    continue

                # Comment handling (simple doc comment association)
                doc_match = DOC_COMMENT_PATTERN.match(line)
                if doc_match:
                    # Allow multi-line doc comments by checking previous line
                    if i > 0 and DOC_COMMENT_PATTERN.match(lines[i - 1].strip()):
                        doc_buffer.append(doc_match.group("doc"))
                    else:
                        doc_buffer = [doc_match.group("doc")]
                    continue  # Don't process comment lines further
                elif stripped_line.startswith("//") or stripped_line.startswith("/*"):
                    doc_buffer = []  # Reset on non-doc comments
                    continue  # Skip regular comments

                # Imports
                import_match = IMPORT_PATTERN.match(line)
                if import_match:
                    if import_match.group("single_import"):
                        imports.add(import_match.group("single_import"))
                    elif import_match.group("multiline_imports"):
                        multi_imports = SINGLE_IMPORT_IN_MULTI_PATTERN.findall(
                            import_match.group("multiline_imports")
                        )
                        imports.update(multi_imports)
                    # Need to consume potential multi-line block
                    # Simplistic: assume it ends when ')' is found
                    # A more robust parser would track nesting
                    if "(" in line and ")" not in line:
                        pass  # Simple regex can't easily handle block end
                    doc_buffer = []  # Imports clear doc buffer
                    continue

                # Function declarations
                func_match = FUNC_PATTERN.match(line)
                if func_match:
                    name = func_match.group("name")
                    docstring = "\n".join(doc_buffer)
                    declarations.append(
                        Declaration(
                            kind="function",
                            name=name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )  # Placeholder end_line
                    doc_buffer = []
                    continue

                # Type declarations
                type_match = TYPE_PATTERN.match(line)
                if type_match:
                    name = type_match.group("name")
                    kind = "type"  # Could try to determine struct/interface if needed
                    docstring = "\n".join(doc_buffer)
                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )  # Placeholder end_line
                    doc_buffer = []
                    continue

                # Var/Const declarations (basic handling)
                var_match = VAR_CONST_PATTERN.match(line)
                if var_match:
                    if var_match.group("name_single"):
                        name = var_match.group("name_single")
                        kind = "variable" if line.startswith("var") else "constant"
                        docstring = "\n".join(doc_buffer)
                        declarations.append(
                            Declaration(
                                kind=kind,
                                name=name,
                                start_line=i,
                                end_line=i,
                                docstring=docstring,
                                modifiers=set(),
                            )
                        )
                    # TODO: Handle multiline var/const blocks - regex is tricky here
                    doc_buffer = []
                    continue

                # If line wasn't comment, import, or declaration, clear doc buffer
                doc_buffer = []

            logger.debug(
                f"Finished GoParser.parse (Regex) for file: {file_path}. Found {len(declarations)} declarations, {len(imports)} unique imports."
            )
            return ParseResult(
                file_path=file_path,
                language="go",
                content=content,
                declarations=declarations,
                imports=sorted(imports),
                engine_used="regex",
                token_stats=None,
                security_issues=[],
            )

        except Exception as e:
            logger.error(f"Error parsing Go file {file_path} with Regex: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse Go file ({type(e).__name__}) using Regex: {e}",
                file_path=file_path,
                original_exception=e,
            ) from e
