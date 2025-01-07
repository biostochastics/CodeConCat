"""PHP language parser for CodeConcat."""

from typing import List
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.base_types import Declaration


class PhpParser(BaseParser):
    """PHP language parser."""

    def _setup_patterns(self):
        """Set up PHP-specific patterns."""
        # Namespace pattern
        self.namespace_pattern = self._create_pattern(
            r'namespace\s+([\w\\]+);'
        )

        # Use/import pattern
        self.use_pattern = self._create_pattern(
            r'use\s+([\w\\]+)(?:\s+as\s+(\w+))?;'
        )

        # Class pattern (including abstract, final, and traits)
        self.class_pattern = self._create_pattern(
            r'(?:abstract\s+|final\s+)?'
            r'(?:class|interface|trait)\s+'
            r'(\w+)'
            r'(?:\s+extends\s+[\w\\]+)?'
            r'(?:\s+implements\s+[\w\\,\s]+)?'
            r'\s*{'
        )

        # Method pattern
        self.method_pattern = self._create_pattern(
            r'(?:public\s+|protected\s+|private\s+)?'
            r'(?:static\s+|final\s+|abstract\s+)*'
            r'function\s+'
            r'(?:&\s*)?'  # Reference return
            r'(\w+)'  # Method name
            r'\s*\([^)]*\)'  # Parameters
            r'(?:\s*:\s*\??[\w\\|]+)?'  # Return type hint
            r'\s*(?:{|;)'  # Body or abstract method
        )

        # Property pattern
        self.property_pattern = self._create_pattern(
            r'(?:public\s+|protected\s+|private\s+)?'
            r'(?:static\s+|readonly\s+)*'
            r'(?:var\s+)?'
            r'\$(\w+)'  # Property name
            r'(?:\s*=\s*[^;]+)?;'  # Optional initialization
        )

        # Constant pattern
        self.const_pattern = self._create_pattern(
            r'const\s+'
            r'(\w+)'  # Constant name
            r'\s*=\s*[^;]+;'  # Value required
        )

    def parse(self, content: str) -> List[Declaration]:
        """Parse PHP code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_namespace = None
        current_class = None
        
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
            if line.startswith('//') or line.startswith('#'):
                i += 1
                continue

            # Track braces for scope
            brace_count += line.count('{') - line.count('}')
            
            # Check for namespace declaration
            if namespace_match := self.namespace_pattern.search(line):
                current_namespace = namespace_match.group(1)
                i += 1
                continue

            # Check for class/interface/trait declaration
            if class_match := self.class_pattern.search(line):
                class_name = class_match.group(1)
                qualified_name = f"{current_namespace}\\{class_name}" if current_namespace else class_name
                current_class = qualified_name
                symbols.append(Declaration(
                    kind="class",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for method declaration
            if method_match := self.method_pattern.search(line):
                method_name = method_match.group(1)
                qualified_name = f"{current_class}::{method_name}" if current_class else method_name
                symbols.append(Declaration(
                    kind="function",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for property declaration
            if property_match := self.property_pattern.search(line):
                property_name = property_match.group(1)
                qualified_name = f"{current_class}::{property_name}" if current_class else property_name
                symbols.append(Declaration(
                    kind="symbol",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))

            # Check for constant declaration
            if const_match := self.const_pattern.search(line):
                const_name = const_match.group(1)
                qualified_name = f"{current_class}::{const_name}" if current_class else const_name
                symbols.append(Declaration(
                    kind="symbol",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))

            i += 1

        return symbols


def parse_php(file_path: str, content: str) -> List[Declaration]:
    """Parse PHP code and return declarations."""
    parser = PhpParser()
    return parser.parse(content)
