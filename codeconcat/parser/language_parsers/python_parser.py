"""Python code parser for CodeConcat."""

import re
from typing import List, Optional

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.base_parser import BaseParser


def parse_python(file_path: str, content: str) -> ParseResult:
    """Parse Python code and return ParseResult."""
    parser = PythonParser()
    declarations = parser.parse(content)
    return ParseResult(
        file_path=file_path,
        language="python",
        content=content,
        declarations=declarations,
    )


class PythonParser(BaseParser):
    """Python language parser."""

    def __init__(self):
        """Initialize Python parser with regex patterns."""
        super().__init__()
        # Allow any Unicode letter/number in identifiers
        name_pattern = r'[^\W\d][\w]*(?:_[\w]*)*'  # Simplified pattern that works with all Unicode
        self.patterns = {
            "class": re.compile(
                r"^(?:@[\w.]+(?:\([^)]*\))?\s+)*"  # Optional decorators
                r"class\s+(?P<n>" + name_pattern + r")"  # Class name
                r"(?:\s*\([^)]*\))?"  # Optional parent class
                r"\s*:",  # Class definition end
                re.UNICODE
            ),
            "function": re.compile(
                r"^(?:@[\w.]+(?:\([^)]*\))?\s+)*"  # Optional decorators
                r"(?:async\s+)?def\s+(?P<n>" + name_pattern + r")"  # Function name
                r"(?:\s*\([^)]*?\))?"  # Function parameters (non-greedy)
                r"\s*(?:->[^:]+)?"  # Optional return type
                r"\s*:",  # Function end
                re.MULTILINE | re.DOTALL | re.VERBOSE | re.UNICODE
            ),
            "constant": re.compile(
                r"^(?P<n>[A-Z][A-Z0-9_]*)\s*"  # Constant name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]",  # Assignment but not comparison
                re.UNICODE
            ),
            "variable": re.compile(
                r"^(?P<n>[a-z_][\w]*)\s*"  # Variable name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]",  # Assignment but not comparison
                re.UNICODE
            ),
        }
        self.block_start = ":"
        self.block_end = None
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

    def parse(self, content: str) -> List[Declaration]:
        """Parse Python code and return declarations."""
        declarations = []
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                i += 1
                continue

            # Collect decorators
            decorators = []
            while line.startswith("@"):
                # Handle multi-line decorators
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
                # Handle multi-line function definitions
                if kind == "function" or kind == "class":
                    # Join lines until we find a complete definition
                    test_content = line
                    j = i + 1
                    while j < len(lines) and not test_content.strip().endswith(":"):
                        test_content += "\n" + lines[j].strip()
                        j += 1
                else:
                    test_content = line

                match = pattern.match(test_content)
                if match:
                    name = match.group("n")
                    if not name:
                        continue

                    # Find end line and extract docstring
                    end_line = i
                    docstring = ""
                    if ":" in line:  # Block definition (function/class)
                        base_indent = len(lines[i]) - len(line)
                        j = i + 1
                        
                        # Look for docstring
                        while j < len(lines):
                            next_line = lines[j].strip()
                            if next_line and not next_line.startswith("#"):
                                curr_indent = len(lines[j]) - len(lines[j].lstrip())
                                if curr_indent > base_indent:
                                    if next_line.startswith('"""') or next_line.startswith("'''"):
                                        quote_char = next_line[0] * 3
                                        if next_line.endswith(quote_char) and len(next_line) > 6:
                                            # Single-line docstring
                                            docstring = next_line[3:-3].strip()
                                        else:
                                            # Multi-line docstring
                                            doc_lines = [next_line[3:].strip()]
                                            k = j + 1
                                            while k < len(lines):
                                                doc_line = lines[k].strip()
                                                if doc_line.endswith(quote_char):
                                                    doc_lines.append(doc_line[:-3].strip())
                                                    break
                                                doc_lines.append(doc_line)
                                                k += 1
                                            docstring = "\n".join(doc_lines).strip()
                                break
                            j += 1

                        # Find block end and parse nested declarations
                        block_lines = []
                        while j < len(lines):
                            curr_line = lines[j]
                            if curr_line.strip() and not curr_line.strip().startswith("#"):
                                curr_indent = len(curr_line) - len(curr_line.lstrip())
                                if curr_indent <= base_indent:
                                    end_line = j - 1
                                    break
                                elif curr_indent > base_indent:
                                    block_lines.append(curr_line[base_indent + 4:])  # Assume 4 spaces indentation
                            j += 1
                        if j == len(lines):
                            end_line = j - 1

                        # Parse nested declarations
                        if block_lines:
                            nested_declarations = self.parse("\n".join(block_lines))
                            for decl in nested_declarations:
                                decl.start_line += i + 1
                                decl.end_line += i + 1
                                declarations.append(decl)

                    elif "=" in line:
                        end_line = i

                    # Create declaration
                    decl = Declaration(
                        kind=kind,
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(decorators),
                        docstring=docstring,
                        children=[]
                    )
                    declarations.append(decl)
                    i = end_line
                    break
            i += 1

        return declarations
