import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_php(file_path: str, content: str) -> Optional[ParsedFileData]:
    """Parse PHP code and return declarations."""
    try:
        parser = PhpParser()
        parser._setup_patterns()  # Initialize patterns
        declarations = parser.parse(content)
        return ParsedFileData(
            file_path=file_path,
            language="php",
            content=content,
            declarations=declarations,
            token_stats=None,
            security_issues=[]
        )
    except Exception as e:
        print(f"Error parsing PHP file: {e}")
        return ParsedFileData(
            file_path=file_path,
            language="php",
            content=content,
            declarations=[],
            token_stats=None,
            security_issues=[]
        )

class PhpParser(BaseParser):
    def _setup_patterns(self):
        """Set up regex patterns for PHP code parsing."""
        self.patterns = {
            'namespace': re.compile(r'namespace\s+([^;{]+)'),
            'class': re.compile(r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?'),
            'interface': re.compile(r'interface\s+(\w+)(?:\s+extends\s+[^{]+)?'),
            'trait': re.compile(r'trait\s+(\w+)'),
            'function': re.compile(r'function\s+(\w+)\s*\([^)]*\)(?:\s*:\s*[^{]+)?'),
            'arrow_function': re.compile(r'\$(\w+)\s*=\s*fn\s*\([^)]*\)\s*=>'),
            'php_tag': re.compile(r'<\?php'),
            'comment': re.compile(r'//.*$|#.*$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
        }
    
    def parse(self, content: str) -> List[Declaration]:
        """Parse PHP code content and return list of declarations."""
        declarations = []
        lines = content.split('\n')
        i = 0
        current_namespace = ""
        php_tag_offset = 0
        
        # Find PHP tag to adjust line numbers
        while i < len(lines):
            line = lines[i].strip()
            if self.patterns['php_tag'].search(line):
                php_tag_offset = i + 1
                break
            i += 1
        
        i = php_tag_offset
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or self.patterns['comment'].match(line):
                i += 1
                continue
            
            # Handle namespaces
            namespace_match = self.patterns['namespace'].match(line)
            if namespace_match:
                current_namespace = namespace_match.group(1).strip().replace('\\\\', '\\')
                declarations.append(Declaration(
                    kind='namespace',
                    name=current_namespace,
                    start_line=i + 1,
                    end_line=i + 1,
                    modifiers=set(),
                    docstring=""
                ))
                i += 1
                continue
            
            # Handle classes
            class_match = self.patterns['class'].match(line)
            if class_match:
                name = class_match.group(1)
                if current_namespace:
                    name = f"{current_namespace}\\{name}"
                else:
                    name = name
                
                # Find class end
                start_line = i + 1
                end_line = self._find_block_end(lines, i)
                
                declarations.append(Declaration(
                    kind='class',
                    name=name,
                    start_line=start_line,
                    end_line=end_line + 1,
                    modifiers=set(),
                    docstring=""
                ))
                i = end_line + 1
                continue
            
            # Handle interfaces
            interface_match = self.patterns['interface'].match(line)
            if interface_match:
                name = interface_match.group(1)
                if current_namespace:
                    name = f"{current_namespace}\\{name}"
                else:
                    name = name
                
                # Find interface end
                start_line = i + 1
                end_line = self._find_block_end(lines, i)
                
                declarations.append(Declaration(
                    kind='interface',
                    name=name,
                    start_line=start_line,
                    end_line=end_line + 1,
                    modifiers=set(),
                    docstring=""
                ))
                i = end_line + 1
                continue
            
            # Handle traits
            trait_match = self.patterns['trait'].match(line)
            if trait_match:
                name = trait_match.group(1)
                if current_namespace:
                    name = f"{current_namespace}\\{name}"
                else:
                    name = name
                
                # Find trait end
                start_line = i + 1
                end_line = self._find_block_end(lines, i)
                
                declarations.append(Declaration(
                    kind='trait',
                    name=name,
                    start_line=start_line,
                    end_line=end_line + 1,
                    modifiers=set(),
                    docstring=""
                ))
                i = end_line + 1
                continue
            
            # Handle functions
            function_match = self.patterns['function'].match(line)
            if function_match:
                name = function_match.group(1)
                if current_namespace:
                    name = f"{current_namespace}\\{name}"
                else:
                    name = name
                
                # Find function end
                start_line = i + 1
                end_line = self._find_block_end(lines, i)
                
                declarations.append(Declaration(
                    kind='function',
                    name=name,
                    start_line=start_line,
                    end_line=end_line + 1,
                    modifiers=set(),
                    docstring=""
                ))
                i = end_line + 1
                continue
            
            # Handle arrow functions
            arrow_match = self.patterns['arrow_function'].match(line)
            if arrow_match:
                name = arrow_match.group(1)
                if current_namespace:
                    name = f"{current_namespace}\\{name}"
                else:
                    name = name
                
                declarations.append(Declaration(
                    kind='function',
                    name=name,
                    start_line=i + 1,
                    end_line=i + 1,
                    modifiers=set(),
                    docstring=""
                ))
                i += 1
                continue
            
            i += 1
        
        return declarations
    
    def _find_block_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a code block starting at the given index."""
        brace_count = 0
        found_opening = False
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            
            if '{' in line:
                found_opening = True
                brace_count += line.count('{')
            if '}' in line:
                brace_count -= line.count('}')
            
            if found_opening and brace_count == 0:
                return i
        
        return start_idx  # Fallback if no end found