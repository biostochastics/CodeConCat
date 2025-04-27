"""R code parser for CodeConcat."""

import re
from typing import List

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
from codeconcat.errors import LanguageParserError


def parse_r(file_path: str, content: str) -> ParseResult:
    parser = RParser()
    parser.current_file_path = file_path  # Set the file path
    try:
        # Call the updated parse method which returns ParseResult
        parse_result = parser.parse(content)
    except Exception as e:
        # Wrap internal parser errors in LanguageParserError
        raise LanguageParserError(
            message=f"Failed to parse R file: {e}",
            file_path=file_path,
            original_exception=e,
        )
    return parse_result


class RParser(BaseParser):
    """
    A regex-based R parser that attempts to capture:
      - Functions (including various assignment operators and nested definitions)
      - Classes (S3, S4, R6, Reference)
      - Methods (S3, S4, R6, $-notation, dot-notation)
      - Package imports (library/require)
      - Roxygen2 modifiers
    Then it scans block contents recursively for nested definitions.
    """

    def __init__(self):
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """
        Compile all regex patterns needed.
        We'll allow for all assignment operators: <-, <<-, =, ->, ->>, :=
        We'll handle S3, S4, R6, reference classes, plus roxygen modifiers.
        """

        # 'qualified_name' can include dots and $ for object methods,
        # e.g. Employee.get_info, Employee$set_salary, or MyPackage.someFunc
        qualified_name = r"[a-zA-Z_]\w*(?:[.$][a-zA-Z_]\w*)*"

        # Methods: S3 dot-notation (print.myclass), $-notation (Employee$get_salary),
        # or S4 setMethod("methodName", "ClassName", function(...))
        self.method_pattern = re.compile(
            rf"""
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

        # General functions with left/right assignment of function(...).
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

        # Classes: S4 setClass("Name"), setRefClass("Name"), R6Class("Name", ...),
        # or MyClass <- R6Class("MyClass", ...).
        self.class_pattern = re.compile(
            rf"""
            ^\s*
            (?:
                # setClass("MyS4Class", ...)
                # setRefClass("Employee", ...)
                # R6Class("MyClass", ...)
                (?:setClass|setRefClass|R6Class)\(\s*["'](?P<cname1>[a-zA-Z_]\w*)["']
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

        # Package imports: library(pkg), require(pkg)
        self.import_pattern = re.compile(
            r"^\s*(?:library|require)\s*\(\s*['\"]?([^'\"]+)['\"]?\s*\)"  # Fixed char class and require ')'
        )

        # R doesn't have an official block comment syntax, but from the base parser:
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "#"
        self.block_comment_start = "#["
        self.block_comment_end = "]#"

    def parse(self, content: str) -> ParseResult:
        """
        Main parse entry:
          1) Merge multiline function/class assignments
          2) Scan for imports (library/require)
          3) Parse top-level blocks for declarations
        """
        raw_lines = content.splitlines()
        # Merge lines like 'x <-', '  function(...)' or 'Cls <-', '  R6Class(...)'
        lines = self._merge_multiline_assignments(raw_lines, also_for_classes=True)

        imports = []
        # Scan for imports before parsing declarations
        for line in lines:
            match = self.import_pattern.match(line)
            if match:
                imports.append(match.group(1).strip())

        # Parse recursively to find declarations (functions, classes, methods)
        # _parse_block returns List[CodeSymbol], which is List[Declaration]
        declarations = self._parse_block(lines, 0, len(lines))

        return ParseResult(
            file_path=self.current_file_path,
            language="r",
            content=content,
            declarations=declarations,
            imports=imports,
        )

    def _parse_block(
        self, lines: List[str], start_idx: int, end_idx: int
    ) -> List[Declaration]:  # Return type is List[Declaration]
        """
        Parse lines from start_idx to end_idx (exclusive),
        capturing functions/methods/classes/packages, plus nested definitions.
        Return a list of CodeSymbol objects (with 0-based line indices).
        Recursively parse the contents of each function/class block to find nested items.
        """
        symbols: List[Declaration] = []
        i = start_idx

        # Roxygen2-based modifiers
        current_modifiers = set()
        in_roxygen = False

        while i < end_idx:
            line = lines[i]
            stripped = line.strip()

            # Roxygen
            if stripped.startswith("#'"):
                if not in_roxygen:
                    current_modifiers.clear()
                in_roxygen = True
                if "@" in stripped:
                    after_at = stripped.split("@", 1)[1].strip()
                    first_token = after_at.split()[0] if after_at else ""
                    if first_token:
                        current_modifiers.add(first_token)
                i += 1
                continue
            else:
                in_roxygen = False

            # Skip empty or normal comment lines
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            # 1) Try method pattern first
            mm = self.method_pattern.match(line)
            if mm:
                method_name = None
                if mm.group("dot_name"):
                    method_name = mm.group("dot_name")
                elif mm.group("dollar_obj") and mm.group("dollar_method"):
                    method_name = (
                        f"{mm.group('dollar_obj')}${mm.group('dollar_method')}"
                    )
                else:
                    # S4 setMethod("someMethod", ...)
                    method_name = mm.group("s4_name")

                start_blk, end_blk = self._find_function_block(lines, i)

                sym = Declaration(
                    name=method_name,
                    kind="method",
                    start_line=start_blk,
                    end_line=end_blk,
                    modifiers=current_modifiers.copy(),
                )
                symbols.append(sym)

                # Recursively parse inside the function body for nested items
                nested_lines = lines[start_blk + 1 : end_blk + 1]
                if end_blk >= start_blk:
                    nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
                    symbols.extend(nested_syms)

                current_modifiers.clear()
                i = end_blk + 1
                continue

            # 2) Try general function pattern
            fm = self.function_pattern.match(line)
            if fm:
                fname = fm.group("fname1") or fm.group("fname2")
                start_blk, end_blk = self._find_function_block(lines, i)

                sym = Declaration(
                    name=fname,
                    kind="function",
                    start_line=start_blk,
                    end_line=end_blk,
                    modifiers=current_modifiers.copy(),
                )
                symbols.append(sym)

                # Check if function body sets class(...) <- "fname" -> S3 constructor
                if self._function_defines_s3(lines, start_blk, end_blk, fname):
                    sym.kind = "class"

                # Recursively parse the function body for nested definitions
                nested_lines = lines[start_blk + 1 : end_blk + 1]
                if end_blk >= start_blk:
                    nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
                    symbols.extend(nested_syms)

                current_modifiers.clear()
                i = end_blk + 1
                continue

            # 3) Try class pattern (S4, ref, R6)
            cm = self.class_pattern.match(line)
            if cm:
                cname = (
                    cm.group("cname1") or cm.group("cname2") or cm.group("cname3") or ""
                )
                cls_start, cls_end = self._find_matching_parenthesis_block(lines, i)

                csym = Declaration(
                    name=cname,
                    kind="class",
                    start_line=i,
                    end_line=cls_end,
                    modifiers=current_modifiers.copy(),
                )
                symbols.append(csym)

                # If R6Class or setRefClass, parse methods from the entire block
                lowered_line = line.lower()
                if "r6class" in lowered_line:
                    methods = self._parse_r6_methods(
                        lines, i, cls_end, class_name=cname
                    )
                    symbols.extend(methods)
                elif "setrefclass" in lowered_line:
                    methods = self._parse_refclass_methods(
                        lines, i, cls_end, class_name=cname
                    )
                    symbols.extend(methods)

                # Also parse nested lines in case there are normal function definitions inside the class body
                nested_lines = lines[i + 1 : cls_end + 1]
                nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
                symbols.extend(nested_syms)

                current_modifiers.clear()
                i = cls_end + 1
                continue

            # 4) Try package
            pm = self.package_pattern.match(line)
            if pm:
                pkg_name = pm.group("pkg1") or pm.group("pkg2")
                psym = Declaration(
                    name=pkg_name,
                    kind="package",
                    start_line=i,
                    end_line=i,
                    modifiers=current_modifiers.copy(),
                )
                symbols.append(psym)
                current_modifiers.clear()
                i += 1
                continue

            # If none matched, move on
            current_modifiers.clear()
            i += 1

        return symbols

    def _merge_multiline_assignments(
        self, raw_lines: List[str], also_for_classes: bool = False
    ) -> List[str]:
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
            # If the line ends with an assignment operator (possibly with comment)
            if re.search(r"(?:<<?-|=|->|->>|:=)\s*(?:#.*)?$", strip_line):
                j = i + 1
                comment_lines = []
                # Skip blank or comment lines
                while j < n and (
                    not raw_lines[j].strip() or raw_lines[j].strip().startswith("#")
                ):
                    comment_lines.append(raw_lines[j])
                    j += 1
                if j < n:
                    next_strip = raw_lines[j].lstrip()
                    # Merge if next line starts with "function("
                    if next_strip.startswith("function"):
                        # Remove any trailing comment from the first line
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
                    # Or if next line has an R6/ref class syntax
                    if also_for_classes:
                        if any(
                            x in next_strip
                            for x in ["R6Class(", "setRefClass(", "setClass("]
                        ):
                            # Remove any trailing comment from the first line
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

    def _find_function_block(self, lines: List[str], start_idx: int) -> (int, int):
        """
        Return (start_line, end_line) for a function (or method) definition starting at start_idx.
        We'll count braces to find the end of the function body. If no brace on that line,
        treat it as a single-line function definition (like "func <- function(x) x").
        """
        line = lines[start_idx]
        # If there's no '{' in this line, it's a one-liner
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
    ) -> (int, int):
        """
        For code like MyClass <- R6Class("MyClass", public=list(...)),
        we only track parentheses '(' and ')' -- not braces -- so we don't get confused by
        function bodies inside the class definition. Return (start_line, end_line).
        """
        line = lines[start_idx]
        open_parens = line.count("(")
        close_parens = line.count(")")
        # We'll NOT track '{' / '}' here, because R6 methods can have braces in them.
        paren_diff = open_parens - close_parens

        # If there's no unmatched parenthesis, treat as single-line
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
    ) -> List[Declaration]:
        """Parse methods defined within an R6 class block.

        Identifies methods defined as `methodName = function(...) { ... }`
        within the `public` or `private` lists of an R6Class definition.

        Args:
            lines: The list of all lines in the file.
            start_idx: The starting line index of the R6 class block.
            end_idx: The ending line index of the R6 class block.
            class_name: The name of the R6 class.

        Returns:
            A list of Declaration objects, where each object represents a
            found method. The name will be formatted as 'class_name.methodName'.
            Fields like 'value = 0' are ignored.
        """
        methods = []
        block = lines[start_idx : end_idx + 1]
        combined = "\n".join(block)

        # Find all method declarations
        method_pattern = re.compile(
            r"([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{", re.MULTILINE
        )

        # Find all matches in the text
        for match in method_pattern.finditer(combined):
            method_name = match.group(1)
            if method_name not in ["fields", "methods"]:  # Exclude these special names
                full_name = f"{class_name}.{method_name}"
                start_line = start_idx + combined[: match.start()].count("\n")
                end_line = start_idx + combined[: match.end()].count("\n")
                methods.append(
                    Declaration(
                        name=full_name,
                        kind="method",
                        start_line=start_line,
                        end_line=end_line,
                        modifiers=set(),
                    )
                )
        return methods

    def _parse_refclass_methods(
        self, lines: List[str], start_idx: int, end_idx: int, class_name: str
    ) -> List[CodeSymbol]:
        """
        For setRefClass("Employee", fields=list(...), methods=list(...)), parse methodName = function(...).
        We'll produce "Employee.methodName".
        """
        methods = []
        block = lines[start_idx : end_idx + 1]
        combined = "\n".join(block)

        # Find all method declarations
        method_pattern = re.compile(
            r"([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{", re.MULTILINE
        )

        # Find all matches in the text
        for match in method_pattern.finditer(combined):
            method_name = match.group(1)
            if method_name not in ["fields", "methods"]:  # Exclude these special names
                full_name = f"{class_name}.{method_name}"
                start_line = start_idx + combined[: match.start()].count("\n")
                end_line = start_idx + combined[: match.end()].count("\n")
                methods.append(
                    CodeSymbol(
                        name=full_name,
                        kind="method",
                        start_line=start_line,
                        end_line=end_line,
                        modifiers=set(),
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
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            "No matching pattern found in R code"
        )  # Replace f-string with regular string

    def _merge_multiline_assignments(
        self, raw_lines: List[str], also_for_classes: bool = False
    ) -> List[str]:
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
            # If the line ends with an assignment operator (possibly with comment)
            if re.search(r"(?:<<?-|=|->|->>|:=)\s*(?:#.*)?$", strip_line):
                j = i + 1
                comment_lines = []
                # Skip blank or comment lines
                while j < n and (
                    not raw_lines[j].strip() or raw_lines[j].strip().startswith("#")
                ):
                    comment_lines.append(raw_lines[j])
                    j += 1
                if j < n:
                    next_strip = raw_lines[j].lstrip()
                    # Merge if next line starts with "function("
                    if next_strip.startswith("function"):
                        # Remove any trailing comment from the first line
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
                    # Or if next line has an R6/ref class syntax
                    if also_for_classes:
                        if any(
                            x in next_strip
                            for x in ["R6Class(", "setRefClass(", "setClass("]
                        ):
                            # Remove any trailing comment from the first line
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
