"""Go language parser for CodeConcat."""

from typing import List
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.base_types import Declaration


class GoParser(BaseParser):
    """Go language parser."""

    def _setup_patterns(self):
        """Set up Go-specific patterns."""
        # Package pattern
        self.package_pattern = self._create_pattern(
            r'package\s+(\w+)'
        )

        # Import pattern
        self.import_pattern = self._create_pattern(
            r'import\s+(?:\(\s*|\s*"?)([^"\s]+)"?'
        )

        # Function pattern (including methods)
        self.func_pattern = self._create_pattern(
            r'func\s+'  # func keyword
            r'(?:\([^)]+\)\s+)?'  # Optional receiver for methods
            r'(\w+)'  # Function name
            r'\s*\([^)]*\)'  # Parameters
            r'(?:\s*\([^)]*\)|\s+[\w.*\[\]{}<>,\s]+)?'  # Optional return type(s)
            r'\s*{'  # Function body start
        )

        # Type pattern (struct/interface)
        self.type_pattern = self._create_pattern(
            r'type\s+'
            r'(\w+)\s+'  # Type name
            r'(?:struct|interface)\s*{'  # Type kind
        )

        # Variable pattern (var/const)
        self.var_pattern = self._create_pattern(
            r'(?:var|const)\s+'
            r'(\w+)'  # Variable name
            r'(?:\s+[\w.*\[\]{}<>,\s]+)?'  # Optional type
            r'(?:\s*=\s*[^;]+)?'  # Optional value
        )

    def parse(self, content: str) -> List[Declaration]:
        """Parse Go code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_package = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle block comments
            if line.startswith('/*'):
                in_comment = True
                if '*/' in line[2:]:
                    in_comment = False
                i += 1
                continue
            if in_comment:
                if '*/' in line:
                    in_comment = False
                i += 1
                continue
            
            # Skip line comments
            if line.startswith('//'):
                i += 1
                continue

            # Track braces for scope
            brace_count += line.count('{') - line.count('}')
            
            # Check for package declaration
            if package_match := self.package_pattern.search(line):
                current_package = package_match.group(1)
                i += 1
                continue

            # Check for function/method declaration
            if func_match := self.func_pattern.search(line):
                func_name = func_match.group(1)
                qualified_name = f"{current_package}.{func_name}" if current_package else func_name
                symbols.append(Declaration(
                    kind="function",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for type declaration
            if type_match := self.type_pattern.search(line):
                type_name = type_match.group(1)
                qualified_name = f"{current_package}.{type_name}" if current_package else type_name
                symbols.append(Declaration(
                    kind="class",  # Using class for both struct and interface
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for variable/constant declaration
            if var_match := self.var_pattern.search(line):
                var_name = var_match.group(1)
                qualified_name = f"{current_package}.{var_name}" if current_package else var_name
                symbols.append(Declaration(
                    kind="symbol",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))

            i += 1

        return symbols


def parse_go(file_path: str, content: str) -> List[Declaration]:
    """Parse Go code and return declarations."""
    parser = GoParser()
    return parser.parse(content)
