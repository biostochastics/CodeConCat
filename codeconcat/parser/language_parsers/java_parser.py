"""Java language parser for CodeConcat."""

from typing import List

from codeconcat.base_types import Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser


class JavaParser(BaseParser):
    """Java language parser."""

    def _setup_patterns(self):
        """Set up Java-specific patterns."""
        # Package pattern
        self.package_pattern = self._create_pattern(r"package\s+([\w.]+);")

        # Import pattern
        self.import_pattern = self._create_pattern(r"import\s+(?:static\s+)?([\w.*]+);")

        # Class pattern (including abstract, final, and visibility modifiers)
        self.class_pattern = self._create_pattern(
            r"(?:public\s+|protected\s+|private\s+)?"
            r"(?:abstract\s+|final\s+)?"
            r"(?:class|interface|enum)\s+"
            r"(\w+)"
            r"(?:\s+extends\s+\w+)?"
            r"(?:\s+implements\s+[\w,\s]+)?"
            r"\s*{"
        )

        # Method pattern (including constructors)
        self.method_pattern = self._create_pattern(
            r"(?:public\s+|protected\s+|private\s+)?"
            r"(?:static\s+|final\s+|abstract\s+|synchronized\s+)*"
            r"(?:<[\w\s,<>]+>\s+)?"  # Generic type parameters
            r"(?:[\w.<>[\],\s]+\s+)?"  # Return type (optional for constructors)
            r"(\w+)"  # Method name
            r"\s*\([^)]*\)"  # Parameters
            r"(?:\s+throws\s+[\w,\s]+)?"  # Throws clause
            r"\s*(?:{|;)"  # Body or abstract method
        )

        # Field pattern
        self.field_pattern = self._create_pattern(
            r"(?:public\s+|protected\s+|private\s+)?"
            r"(?:static\s+|final\s+|volatile\s+|transient\s+)*"
            r"[\w.<>[\],\s]+\s+"  # Type
            r"(\w+)"  # Field name
            r"(?:\s*=\s*[^;]+)?;"  # Optional initialization
        )

        # Annotation pattern
        self.annotation_pattern = self._create_pattern(r"@(\w+)(?:\s*\([^)]*\))?")

    def parse(self, content: str) -> List[Declaration]:
        """Parse Java code content."""
        lines = content.split("\n")
        symbols = []
        brace_count = 0
        in_comment = False
        current_package = None
        current_class = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Handle block comments
            if line.startswith("/*"):
                in_comment = True
                if "*/" in line[2:]:
                    in_comment = False
                i += 1
                continue
            if in_comment:
                if "*/" in line:
                    in_comment = False
                i += 1
                continue

            # Skip line comments
            if line.startswith("//"):
                i += 1
                continue

            # Track braces for scope
            brace_count += line.count("{") - line.count("}")

            # Check for package declaration
            if package_match := self.package_pattern.search(line):
                current_package = package_match.group(1)
                i += 1
                continue

            # Check for class/interface/enum declaration
            if class_match := self.class_pattern.search(line):
                class_name = class_match.group(1)
                qualified_name = (
                    f"{current_package}.{class_name}" if current_package else class_name
                )
                current_class = qualified_name
                symbols.append(
                    Declaration(kind="class", name=qualified_name, start_line=i, end_line=i)
                )
                i += 1
                continue

            # Check for method declaration
            if method_match := self.method_pattern.search(line):
                method_name = method_match.group(1)
                qualified_name = f"{current_class}.{method_name}" if current_class else method_name
                symbols.append(
                    Declaration(kind="function", name=qualified_name, start_line=i, end_line=i)
                )
                i += 1
                continue

            # Check for field declaration
            if field_match := self.field_pattern.search(line):
                field_name = field_match.group(1)
                qualified_name = f"{current_class}.{field_name}" if current_class else field_name
                symbols.append(
                    Declaration(kind="symbol", name=qualified_name, start_line=i, end_line=i)
                )

            i += 1

        return symbols


def parse_java(file_path: str, content: str) -> List[Declaration]:
    """Parse Java code and return declarations."""
    parser = JavaParser()
    return parser.parse(content)
