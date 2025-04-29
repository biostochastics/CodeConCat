"""R code parser for CodeConcat."""

import logging
import re
from typing import List, Set, Tuple

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError
from .base_parser import ParserInterface

logger = logging.getLogger(__name__)


class RParser(ParserInterface):
    """
    A regex-based R parser implementing ParserInterface. It attempts to capture:
      - Functions (including various assignment operators and nested definitions)
      - Classes (S3, S4, R6, Reference)
      - Methods (S3, S4, R6, $-notation, dot-notation)
      - Package imports (library/require)
      - Roxygen2 modifiers
    Then it scans block contents recursively for nested definitions.
    """

    def __init__(self):
        self._setup_patterns()
        self.current_file_path = "<unknown>"

    def _setup_patterns(self):
        """
        Compile all regex patterns needed.
        """
        qualified_name = r"[a-zA-Z_.][a-zA-Z0-9_.]*(?:\$[a-zA-Z_][a-zA-Z0-9_.]*)?"

        self.import_pattern = re.compile(
            r"^\s*(?:library|require)\s*\(\s*([a-zA-Z_][a-zA-Z0-9_.]*)[^)]*\)"
        )

        self.roxygen_pattern = re.compile(r"^\s*#'(.*)")

        self.function_pattern = re.compile(
            rf"""
            ^\s*
            (?:
               # left-assign forms:  name <- function(...)
               #                     name = function(...)
               #                     name <<- function(...)
               #                     name := function(...)
               (?P<fname1>{qualified_name})\s*(?:<<?-|=|:=)\s*function\s*\(
               |
               # right-assign forms: function(...) -> name
               #                     function(...) ->> name
               function\s*\([^)]*\)\s*(?:->|->>)\s*(?P<fname2>{qualified_name})
            )
            """,
            re.VERBOSE,
        )

        self.s4_method_pattern = re.compile(
            r"""
            ^\s*
            (?:
                # S3/object dot-notation:  "print.myclass <- function(...)" or "summary.myclass -> function(...)"
                (?P<dot_name>{qualified_name}\.[a-zA-Z_]\w*)
                \s*(?:<<?-|=|->|->>|:=)
                \s*function\s*\(
                |
                # R6/object dollar-notation:  "Employee$get_salary <- function(...)"
                (?P<dollar_obj>{qualified_name})\$(?P<dollar_method>[a-zA-Z_]\w*)
                \s*(?:<<?-|=|->|->>|:=)
                \s*function\s*\(
                |
                # S4 method: setMethod("myMethod", "MyS4Class", function(...))
                setMethod\(\s*["'](?P<s4_name>[^"']+)["']
            )
            """,
            re.VERBOSE,
        )

        self.class_pattern = re.compile(
            rf"""
            ^\s*
            (?:
                # setClass("MyS4Class", ...)
                # setRefClass("Employee", ...)
                # R6Class("MyClass", ...)
                (?:setClass|setRefClass|R6Class)\(\s*["'](?P<cname1>{qualified_name})["']
                |
                # MyClass <- R6Class("MyClass", ...)
                # MyClass = R6Class("MyClass", ...)
                # MyClass <<- R6Class("MyClass", ...)
                # MyClass := R6Class("MyClass", ...)
                (?P<cname2>{qualified_name})\s*(?:<<?-|=|:=)\s*(?:R6Class|setRefClass|setClass)\(
                |
                # R6Class(...) -> MyClass
                # R6Class(...) ->> MyClass
                (?:R6Class|setRefClass|setClass)\([^)]*\)\s*(?:->|->>)\s*(?P<cname3>{qualified_name})
            )
            """,
            re.VERBOSE,
        )

    def parse(self, content: str, file_path: str) -> ParseResult:
        """
        Main parse entry:
          1) Preprocess: Merge multiline assignments
          2) Scan for imports (library/require)
          3) Parse top-level blocks for declarations
        Returns a ParseResult object.
        """
        self.current_file_path = file_path
        logger.debug(f"Starting RParser.parse (Regex) for file: {file_path}")
        declarations: List[Declaration] = []
        imports: Set[str] = set()

        try:
            lines = self._merge_multiline_assignments(content.split('\n'), also_for_classes=True)

            for line in lines:
                import_match = self.import_pattern.match(line.strip())
                if import_match:
                    imports.add(import_match.group(1))

            parsed_symbols = self._parse_block(lines, 0, len(lines))
            for symbol in parsed_symbols:
                declarations.append(Declaration(
                    kind=symbol.type,
                    name=symbol.name,
                    start_line=symbol.start_idx,
                    end_line=symbol.end_idx,
                    docstring=symbol.docstring,
                    modifiers=symbol.modifiers
                ))

            logger.debug(
                f"Finished RParser.parse (Regex) for file: {file_path}. Found {len(declarations)} declarations, {len(imports)} imports."
            )

            return ParseResult(
                file_path=file_path,
                language="r",
                content=content,
                declarations=declarations,
                imports=sorted(list(imports)),
                engine_used="regex",
                token_stats=None,
                security_issues=[]
            )

        except Exception as e:
            logger.error(f"Error parsing R file {file_path} with Regex: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse R file ({type(e).__name__}) using Regex: {e}",
                file_path=file_path,
                original_exception=e,
            )

    class TempCodeSymbol:
        def __init__(self, type, name, start_idx, end_idx, docstring, modifiers):
            self.type = type
            self.name = name
            self.start_idx = start_idx
            self.end_idx = end_idx
            self.docstring = docstring if docstring else ""
            self.modifiers = modifiers if modifiers else set()

    def _parse_block(
        self, lines: List[str], start_idx: int, end_idx: int
    ) -> List[TempCodeSymbol]:
        """
        Parse lines from start_idx to end_idx (exclusive).
        Return a list of TempCodeSymbol objects.
        """
        symbols: List[RParser.TempCodeSymbol] = []
        i = start_idx
        current_docstring_lines = []

        while i < end_idx:
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("#'"):
                current_docstring_lines.append(stripped[3:])
                i += 1
                continue

            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            s4_method_match = self.s4_method_pattern.match(line)
            if s4_method_match:
                method_name = None
                if s4_method_match.group("dot_name"):
                    method_name = s4_method_match.group("dot_name")
                elif s4_method_match.group("dollar_obj") and s4_method_match.group("dollar_method"):
                    method_name = (
                        f"{s4_method_match.group('dollar_obj')}${s4_method_match.group('dollar_method')}"
                    )
                else:
                    method_name = s4_method_match.group("s4_name")

                start_block, end_block = self._find_function_block(lines, i)

                symbols.append(
                    RParser.TempCodeSymbol(
                        type="method",
                        name=method_name,
                        start_idx=i,
                        end_idx=end_block,
                        docstring="\n".join(current_docstring_lines),
                        modifiers=set()
                    )
                )

                nested_symbols = self._parse_block(lines, start_block + 1, end_block)
                symbols.extend(nested_symbols)
                i = end_block + 1
                current_docstring_lines = []
                continue

            func_match = self.function_pattern.match(line)
            if func_match:
                func_name = func_match.group("fname1") or func_match.group("fname2")
                start_block, end_block = self._find_function_block(lines, i)

                symbol_type = "function"
                if self._function_defines_s3(lines, start_block, end_block, func_name):
                    symbol_type = "class"

                symbols.append(
                    RParser.TempCodeSymbol(
                        type=symbol_type,
                        name=func_name,
                        start_idx=i,
                        end_idx=end_block,
                        docstring="\n".join(current_docstring_lines),
                        modifiers=set()
                    )
                )

                nested_symbols = self._parse_block(lines, start_block + 1, end_block)
                symbols.extend(nested_symbols)
                i = end_block + 1
                current_docstring_lines = []
                continue

            class_match = self.class_pattern.match(line)
            if class_match:
                class_name = (
                    class_match.group("cname1") or class_match.group("cname2") or class_match.group("cname3") or ""
                )
                class_start, class_end = self._find_matching_parenthesis_block(lines, i)

                symbols.append(
                    RParser.TempCodeSymbol(
                        type="class",
                        name=class_name,
                        start_idx=i,
                        end_idx=class_end,
                        docstring="\n".join(current_docstring_lines),
                        modifiers=set()
                    )
                )

                if "R6Class" in line:
                    methods = self._parse_r6_methods(lines, class_start + 1, class_end, class_name)
                    symbols.extend(methods)
                elif "setRefClass" in line:
                    methods = self._parse_refclass_methods(lines, class_start + 1, class_end, class_name)
                    symbols.extend(methods)

                nested_symbols = self._parse_block(lines, class_start + 1, class_end)
                symbols.extend(nested_symbols)
                i = class_end + 1
                current_docstring_lines = []
                continue

            i += 1

        return symbols

    def _merge_multiline_assignments(self, raw_lines: List[str], also_for_classes: bool = False) -> List[str]:
        """
        Fix for cases like:
          complex_func <- # comment
             function(x) { ... }
        We'll merge such lines so the regex sees them on a single line.

        If also_for_classes=True, we also merge if the line ends with an assignment operator
        and the next line starts with R6Class(, setRefClass(, or setClass(.
        """
        merged = []
        i = 0
        n = len(raw_lines)

        while i < n:
            line = raw_lines[i]
            strip_line = line.strip()
            if re.search(r"(?:<<?-|=|->|->>|:=)\s*(?:#.*)?$", strip_line):
                j = i + 1
                comment_lines = []
                while j < n and (
                    not raw_lines[j].strip() or raw_lines[j].strip().startswith("#")
                ):
                    comment_lines.append(raw_lines[j])
                    j += 1
                if j < n:
                    next_strip = raw_lines[j].lstrip()
                    if next_strip.startswith("function"):
                        base_line = re.sub(r"#.*$", "", line).rstrip()
                        new_line = (
                            base_line
                            + " "
                            + " ".join(line.strip() for line in comment_lines)
                            + " "
                            + raw_lines[j].lstrip()
                        )
                        merged.append(new_line)
                        i = j + 1
                        continue
                    if also_for_classes:
                        if any(
                            x in next_strip
                            for x in ["R6Class(", "setRefClass(", "setClass("]
                        ):
                            base_line = re.sub(r"#.*$", "", line).rstrip()
                            new_line = (
                                base_line
                                + " "
                                + " ".join(line.strip() for line in comment_lines)
                                + " "
                                + raw_lines[j].lstrip()
                            )
                            merged.append(new_line)
                            i = j + 1
                            continue
            merged.append(line)
            i += 1
        return merged

    def _find_function_block(self, lines: List[str], start_idx: int) -> Tuple[int, int]:
        """
        Return (start_line, end_line) for a function (or method) definition starting at start_idx.
        We'll count braces to find the end of the function body. If no brace on that line,
        treat it as a single-line function definition (like "func <- function(x) x").
        """
        line = lines[start_idx]
        if "{" not in line:
            return start_idx, start_idx

        brace_count = line.count("{") - line.count("}")
        end_idx = start_idx
        j = start_idx
        while j < len(lines):
            if j > start_idx:
                brace_count += lines[j].count("{") - lines[j].count("}")
            if brace_count <= 0 and j > start_idx:
                end_idx = j
                break
            j += 1
        if j == len(lines):
            end_idx = len(lines) - 1
        return start_idx, end_idx

    def _function_defines_s3(
        self, lines: List[str], start_idx: int, end_idx: int, fname: str
    ) -> bool:
        """
        Check if between start_idx and end_idx there's 'class(...) <- "fname"'
        or something that sets 'class(...)' to the same name, indicating an S3 constructor.
        """
        pattern = re.compile(
            rf'class\s*\(\s*[^\)]*\)\s*(?:<<?-|=)\s*["\']{re.escape(fname)}["\']'
        )
        for idx in range(start_idx, min(end_idx + 1, len(lines))):
            if pattern.search(lines[idx]):
                return True
        return False

    def _find_matching_parenthesis_block(
        self, lines: List[str], start_idx: int
    ) -> Tuple[int, int]:
        """
        For code like MyClass <- R6Class("MyClass", public=list(...)),
        we only track parentheses '(' and ')' -- not braces -- so we don't get confused by
        function bodies inside the class definition. Return (start_line, end_line).
        """
        line = lines[start_idx]
        open_parens = line.count("(")
        close_parens = line.count(")")
        paren_diff = open_parens - close_parens

        if paren_diff <= 0:
            return start_idx, start_idx

        j = start_idx
        while j < len(lines) and paren_diff > 0:
            j += 1
            if j < len(lines):
                open_parens = lines[j].count("(")
                close_parens = lines[j].count(")")
                paren_diff += open_parens - close_parens

        return (start_idx, min(j, len(lines) - 1))

    def _parse_r6_methods(
        self, lines: List[str], start_idx: int, end_idx: int, class_name: str
    ) -> List[TempCodeSymbol]:
        """Parse methods defined within an R6 class block.

        Identifies methods defined as `methodName = function(...) { ... }`
        within the `public` or `private` lists of an R6Class definition.

        Args:
            lines: The list of all lines in the file.
            start_idx: The starting line index of the R6 class block.
            end_idx: The ending line index of the R6 class block.
            class_name: The name of the R6 class.

        Returns:
            A list of TempCodeSymbol objects, where each object represents a
            found method. The name will be formatted as 'class_name.methodName'.
            Fields like 'value = 0' are ignored.
        """
        methods = []
        block = lines[start_idx : end_idx + 1]
        combined = "\n".join(block)

        method_pattern = re.compile(
            r"([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{", re.MULTILINE
        )

        for match in method_pattern.finditer(combined):
            method_name = match.group(1)
            if method_name not in ["fields", "methods"]:  
                full_name = f"{class_name}.{method_name}"
                start_line = start_idx + combined[: match.start()].count("\n")
                end_line = start_idx + combined[: match.end()].count("\n")
                methods.append(
                    RParser.TempCodeSymbol(
                        type="method",
                        name=full_name,
                        start_idx=start_line,
                        end_idx=end_line,
                        docstring="",
                        modifiers=set()
                    )
                )
        return methods

    def _parse_refclass_methods(
        self, lines: List[str], start_idx: int, end_idx: int, class_name: str
    ) -> List[TempCodeSymbol]:
        """
        For setRefClass("Employee", fields=list(...), methods=list(...)), parse methodName = function(...).
        We'll produce "Employee.methodName".
        """
        methods = []
        block = lines[start_idx : end_idx + 1]
        combined = "\n".join(block)

        method_pattern = re.compile(
            r"([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{", re.MULTILINE
        )

        for match in method_pattern.finditer(combined):
            method_name = match.group(1)
            if method_name not in ["fields", "methods"]:  
                full_name = f"{class_name}.{method_name}"
                start_line = start_idx + combined[: match.start()].count("\n")
                end_line = start_idx + combined[: match.end()].count("\n")
                methods.append(
                    RParser.TempCodeSymbol(
                        type="method",
                        name=full_name,
                        start_idx=start_line,
                        end_idx=end_line,
                        docstring="",
                        modifiers=set()
                    )
                )
        return methods

    def _find_function_start_line(
        self, lines: List[str], start_line: int, func_name: str
    ) -> int:
        """
        Find the line number where the function definition starts
        """
        for line_num, line_content in enumerate(lines[start_line:], start=start_line):
            if re.match(rf"\s*{func_name}\s*<-\s*function\b", line_content):
                return line_num
        return -1

    def _find_class_start_line(
        self, lines: List[str], start_line: int, class_name: str
    ) -> int:
        """
        Find the line number where the class definition starts
        """
        for line_num, line_content in enumerate(lines[start_line:], start=start_line):
            if re.match(
                rf"\s*setClass\s*\(\s*['\"]?{class_name}['\"]?\b", line_content
            ):
                return line_num
        return -1

    def _print_no_matching_pattern_found(self):
        logger.info(
            "No matching pattern found in R code"
        )  
