# file: codeconcat/parser/language_parsers/cpp_parser.py

import logging
import re

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError
from .base_parser import ParserInterface  # Import ParserInterface

logger = logging.getLogger(__name__)

# Regex patterns for C/C++ constructs
# Basic include pattern
INCLUDE_PATTERN = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]')
# Matches functions (simplistic: return_type name(...)) potentially with class scope
FUNCTION_PATTERN = re.compile(
    r"^\s*(?:(?:inline|static|virtual|explicit|friend)\s+)*"  # Optional keywords
    r"(?:(?:const|volatile)\s+)*"  # Optional qualifiers
    r"(?P<return_type>[\w<>:&*~]+(?:\s*<.*?>)?(?:\s*(?:const|volatile|&|\*|&&))?)"  # Return type (complex)
    r"\s+"
    r"(?:(?P<class_scope>[\w<>]+)::)?"  # Optional class scope
    r"(?P<name>[\w_~][\w\d_]*)"  # Function name (allow ~ for destructors)
    r"\s*\(.*\)"  # Parameters
    r"(?:\s*(?:const|volatile|override|final|noexcept))?"  # Optional suffix keywords
    r"\s*(?:;|\{|= default;|= delete;)?"  # End char
)
# Matches class, struct, union, enum definitions
CLASS_STRUCT_UNION_ENUM_PATTERN = re.compile(
    r"^\s*(?:template\s*<.*>\s*)?"  # Optional template
    r"(?P<kind>class|struct|union|enum(?:\s+class|\s+struct)?)"  # Kind
    r"(?:\s+:\s*(?:public|protected|private)\s+[\w<>:]+)?"  # Optional inheritance
    r"\s+(?P<name>[\w_][\w\d_]*)?"  # Optional name (e.g., anonymous enum/struct)
    r"\s*(?:final)?\s*(?:;|\{)"  # End char
)
# Matches namespace definition
NAMESPACE_PATTERN = re.compile(r"^\s*namespace\s+(?P<name>[\w_][\w\d_]*)?\s*\{?")
# Matches using namespace ...;
USING_NAMESPACE_PATTERN = re.compile(r"^\s*using\s+namespace\s+([\w:]+);")
# Matches typedef / using alias
TYPEDEF_USING_PATTERN = re.compile(
    r"^\s*(?:typedef\s+(?P<typedef_type>.+?)\s+(?P<typedef_name>[\w_][\w\d_]*)|"  # Typedef
    r"using\s+(?P<using_name>[\w_][\w\d_]*)\s*=\s*(?P<using_type>.+?))"  # Using alias
)
# Matches variable declarations (simplistic, might miss complex ones)
VARIABLE_PATTERN = re.compile(
    r"^\s*(?:(?:static|extern|const|volatile|mutable|constexpr)\s+)*"  # Keywords
    r"(?P<type>[\w<>:&*~]+(?:\s*<.*?>)?(?:\s*(?:const|volatile|&|\*|&&))?)"  # Type
    r"\s+"
    r"(?P<name>[\w_][\w\d_]*)"
    r"\s*(?:[;\[=])"  # Must end with ;, [ or =
)
# Matches Doxygen/Javadoc style comments
DOC_COMMENT_START_PATTERN = re.compile(r"^\s*/(?:\*\*|/\*!)<?")
DOC_COMMENT_LINE_PATTERN = re.compile(r"^\s*(?:\*|///|//!)?\s?(.*)")
DOC_COMMENT_END_PATTERN = re.compile(r"(.*)\*/")
LINE_DOC_COMMENT_PATTERN = re.compile(r"^\s*///<?(.*)")


# Remove old wrapper function
# def parse_cpp(file_path: str, content: str) -> ParseResult:
#     parser = CppParser()
#     try:
#         declarations, imports = parser.parse(content)
#         return ParseResult(
#             file_path=file_path,
#             language="cpp", # Assuming C++
#             content=content,
#             declarations=declarations,
#             imports=imports,
#             engine_used="regex",
#         )
#     except Exception as e:
#         raise LanguageParserError(
#             message=f"Failed to parse C/C++ file with Regex: {e}",
#             file_path=file_path,
#             original_exception=e,
#         )


# Inherit from ParserInterface
class CppParser(ParserInterface):
    """Parses C/C++ code using Regex."""

    # Update signature to match ParserInterface
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parses the given C/C++ code content.

        Args:
            content: The C/C++ code as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object containing declarations and imports.
        """
        declarations = []
        imports: set[str] = set()
        lines = content.split("\n")
        doc_buffer: list[str] = []
        in_block_comment = False
        in_doc_comment = False
        current_namespace_stack: list[str] = []
        current_class_stack: list[str] = []  # For nested classes/structs
        bracket_level = 0  # Basic brace tracking for scope

        try:
            logger.debug(f"Starting CppParser.parse (Regex) for file: {file_path}")
            for i, line in enumerate(lines):
                stripped_line = line.strip()

                # Track scope (simple brace counting)
                bracket_level += line.count("{")
                bracket_level -= line.count("}")
                if bracket_level < 0:
                    bracket_level = 0  # Avoid going negative

                # Handle Comments (Block and Line)
                if in_block_comment:
                    if "*/" in stripped_line:
                        in_block_comment = False
                        stripped_line = stripped_line.split("*/", 1)[1].strip()
                    else:
                        if in_doc_comment:
                            # Extract content from doc comment line
                            end_match = DOC_COMMENT_END_PATTERN.match(line.strip())
                            if end_match:
                                doc_buffer.append(
                                    DOC_COMMENT_LINE_PATTERN.sub("\1", end_match.group(1)).strip()
                                )
                                in_doc_comment = False
                            else:
                                doc_buffer.append(
                                    DOC_COMMENT_LINE_PATTERN.sub("\1", line.strip()).strip()
                                )
                        continue  # Skip the rest of the line if still in block comment

                if "/*" in stripped_line:
                    # Check for potential doc comments first
                    doc_start_match = DOC_COMMENT_START_PATTERN.match(stripped_line)
                    if doc_start_match:
                        in_block_comment = True
                        in_doc_comment = True
                        comment_content = stripped_line[doc_start_match.end() :]
                        if "*/" in comment_content:
                            in_block_comment = False
                            in_doc_comment = False
                            end_match = DOC_COMMENT_END_PATTERN.match(comment_content)
                            doc_buffer = (
                                [DOC_COMMENT_LINE_PATTERN.sub("\1", end_match.group(1)).strip()]
                                if end_match
                                else []
                            )
                        else:
                            doc_buffer = [
                                DOC_COMMENT_LINE_PATTERN.sub("\1", comment_content).strip()
                            ]  # Start buffer
                        continue
                    else:
                        # Regular block comment
                        if "*/" not in stripped_line:
                            in_block_comment = True
                        # Process part of line before comment if any
                        stripped_line = stripped_line.split("/*", 1)[0].strip()
                        # Block comments clear the doc buffer
                        doc_buffer = []

                # Handle single line comments (// and ///)
                if "//" in stripped_line:
                    line_doc_match = LINE_DOC_COMMENT_PATTERN.match(stripped_line)
                    if line_doc_match:
                        # Append line doc comment to buffer
                        doc_buffer.append(line_doc_match.group(1).strip())
                    else:
                        # Regular line comment clears doc buffer
                        doc_buffer = []
                    stripped_line = stripped_line.split("//", 1)[0].strip()

                # Skip empty lines after comment processing
                if not stripped_line:
                    # Don't clear doc buffer on empty lines, wait for declaration or code
                    continue

                # --- Parse Declarations and Imports --- #

                # Include
                include_match = INCLUDE_PATTERN.match(stripped_line)
                if include_match:
                    imports.add(include_match.group(1))
                    doc_buffer = []  # Includes clear buffer
                    continue

                # Using Namespace
                using_match = USING_NAMESPACE_PATTERN.match(stripped_line)
                if using_match:
                    # Could potentially treat 'using namespace' as an import?
                    # imports.add(f"namespace:{using_match.group(1)}")
                    doc_buffer = []
                    continue

                # Namespace definition
                namespace_match = NAMESPACE_PATTERN.match(stripped_line)
                if namespace_match:
                    name = namespace_match.group("name")
                    if name:  # Handle anonymous namespaces later if needed
                        # Note: Regex can't easily track nested namespaces perfectly
                        current_namespace_stack.append(name)
                        full_name = "::".join(current_namespace_stack)
                        docstring = "\n".join(filter(None, doc_buffer))
                        declarations.append(
                            Declaration(
                                kind="namespace",
                                name=full_name,
                                start_line=i,
                                end_line=i,
                                docstring=docstring,
                                modifiers=set(),
                            )
                        )  # Placeholder end_line
                        doc_buffer = []
                    continue

                # Class/Struct/Union/Enum
                csu_match = CLASS_STRUCT_UNION_ENUM_PATTERN.match(stripped_line)
                if csu_match:
                    kind = csu_match.group("kind")
                    name = csu_match.group("name")
                    if name:  # Skip anonymous structs/unions/enums for now
                        scope = current_namespace_stack + current_class_stack
                        full_name = "::".join(scope + [name])
                        docstring = "\n".join(filter(None, doc_buffer))
                        declarations.append(
                            Declaration(
                                kind=kind.replace(" ", "_"),
                                name=full_name,
                                start_line=i,
                                end_line=i,
                                docstring=docstring,
                                modifiers=set(),
                            )
                        )  # Placeholder end_line
                        doc_buffer = []
                        # Push onto class stack if it opens a scope
                        if stripped_line.endswith("{"):
                            current_class_stack.append(name)
                    continue

                # Function/Method
                func_match = FUNCTION_PATTERN.match(stripped_line)
                if func_match:
                    name = func_match.group("name")
                    class_scope = func_match.group("class_scope")
                    kind = "method" if class_scope or current_class_stack else "function"
                    # Use explicit class scope if present, otherwise use stack
                    if class_scope:
                        scope = current_namespace_stack + [class_scope]
                    else:
                        scope = current_namespace_stack + current_class_stack

                    # Handle constructors/destructors
                    if name.startswith("~"):
                        kind = "destructor"
                    elif current_class_stack and name == current_class_stack[-1]:
                        kind = "constructor"
                    elif class_scope and name == class_scope.split("<")[0]:
                        kind = "constructor"  # Basic template check

                    full_name = "::".join(scope + [name])
                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )  # Placeholder end_line
                    doc_buffer = []
                    continue

                # Typedef / Using Alias
                typedef_match = TYPEDEF_USING_PATTERN.match(stripped_line)
                if typedef_match:
                    if typedef_match.group("typedef_name"):
                        name = typedef_match.group("typedef_name")
                        kind = "typedef"
                    else:
                        name = typedef_match.group("using_name")
                        kind = "using_alias"

                    scope = current_namespace_stack + current_class_stack
                    full_name = "::".join(scope + [name])
                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    doc_buffer = []
                    continue

                # Variable (simplistic)
                # Place after function/class checks to avoid misinterpreting definitions
                var_match = VARIABLE_PATTERN.match(stripped_line)
                if var_match and not (stripped_line.endswith("{") or "(" in name):  # Basic checks
                    name = var_match.group("name")
                    scope = current_namespace_stack + current_class_stack
                    full_name = "::".join(scope + [name])
                    kind = "variable"
                    # Determine if global or member based on scope stack
                    if current_class_stack:
                        kind = "member_variable"
                    elif not current_namespace_stack and not current_class_stack:
                        kind = "global_variable"
                    else:
                        kind = "namespace_variable"

                    docstring = "\n".join(filter(None, doc_buffer))
                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=full_name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )
                    doc_buffer = []
                    continue

                # If the line contains code but wasn't a comment or known declaration, clear the doc buffer.
                if stripped_line:
                    doc_buffer = []
                    # Basic scope exit detection
                    if stripped_line.startswith("}"):
                        if (
                            current_class_stack
                            and bracket_level
                            < len(current_namespace_stack) + len(current_class_stack) - 1
                        ):  # Approximation
                            current_class_stack.pop()
                        elif (
                            current_namespace_stack
                            and bracket_level < len(current_namespace_stack) - 1
                        ):
                            current_namespace_stack.pop()

            logger.debug(
                f"Finished CppParser.parse (Regex) for file: {file_path}. Found {len(declarations)} declarations, {len(imports)} imports."
            )
            # TODO: Improve end_line detection using bracket_level or more robust scope tracking.
            return ParseResult(
                file_path=file_path,
                language="cpp",  # Or detect C vs C++ based on file_path?
                content=content,
                declarations=declarations,
                imports=sorted(imports),
                engine_used="regex",  # Set engine_used
                token_stats=None,
                security_issues=[],
            )

        except Exception as e:
            logger.error(f"Error parsing C/C++ file {file_path} with Regex: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse C/C++ file ({type(e).__name__}) using Regex: {e}",
                file_path=file_path,
                original_exception=e,
            ) from e
