# file: codeconcat/parser/language_parsers/pattern_library.py

"""
Pattern library for language parsers.

This module provides common regex patterns that can be reused across different
language parsers to improve consistency and reduce duplication. Patterns are
organized by their purpose and language family compatibility.
"""

import re
from typing import Dict, List, Pattern, Union


# Common identifier patterns
IDENTIFIER_BASIC = r'[a-zA-Z_][a-zA-Z0-9_]*'
IDENTIFIER_UNICODE = r'[\w\u0080-\uffff]+'  # Unicode word character class for international identifiers

# Common modifiers across multiple languages
C_FAMILY_MODIFIERS = [
    'public', 'private', 'protected', 'static', 'final', 'abstract',
    'synchronized', 'native', 'strictfp', 'const', 'volatile', 'transient',
    'virtual', 'override', 'sealed', 'readonly', 'inline', 'explicit', 'extern'
]

PYTHON_DECORATORS = r'(?:@[\w\.]+(?:\([^)]*\))?\s*)*'


class DocstringPatterns:
    """Patterns for extracting docstrings in different languages."""
    
    # Python triple-quoted docstrings
    PYTHON_TRIPLE_QUOTE = re.compile(r'^\s*(""".*?"""|\'\'\'.*?\'\'\')', re.DOTALL)
    
    # Java/C#/Kotlin style docstrings
    JAVADOC = re.compile(r'/\*\*.*?\*/', re.DOTALL)
    
    # Go style docstrings (block comments)
    GO_DOC = re.compile(r'/\*.*?\*/', re.DOTALL)
    
    # Single-line comment docstrings (e.g., ///, ///, #)
    SINGLE_LINE_DOC = {
        'csharp': re.compile(r'^\s*///.*$', re.MULTILINE),
        'python': re.compile(r'^\s*#.*$', re.MULTILINE),
        'javascript': re.compile(r'^\s*//.*$', re.MULTILINE),
    }

    @staticmethod
    def extract_python_docstring(lines: List[str], start: int, end: int) -> str:
        """Extract Python-style docstring from lines."""
        for i in range(start, min(end + 1, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                doc_lines = []
                quote = line[:3]
                if line.endswith(quote) and len(line) > 3:
                    return line[3:-3].strip()
                doc_lines.append(line[3:])
                for j in range(i + 1, end + 1):
                    line2 = lines[j]
                    if line2.strip().endswith(quote):
                        doc_lines.append(line2.strip()[:-3])
                        return "\n".join(doc_lines).strip()
                    doc_lines.append(line2.strip())
        return ""


class CommentPatterns:
    """Patterns for identifying comments in different languages."""
    
    # Single-line comments
    SINGLE_LINE = {
        'python': r'#',
        'javascript': r'//',
        'cpp': r'//',
        'java': r'//',
        'csharp': r'//',
        'ruby': r'#',
        'bash': r'#',
        'go': r'//',
        'rust': r'///',
        'php': r'//',
    }
    
    # Block comment start/end
    BLOCK_COMMENT = {
        'javascript': (r'/\*', r'\*/'),
        'cpp': (r'/\*', r'\*/'),
        'java': (r'/\*', r'\*/'),
        'csharp': (r'/\*', r'\*/'),
        'go': (r'/\*', r'\*/'),
        'rust': (r'/\*', r'\*/'),
        'php': (r'/\*', r'\*/'),
        'css': (r'/\*', r'\*/'),
    }


class FunctionPatterns:
    """Patterns for identifying functions in different languages."""
    
    # C-style function patterns with optional modifiers and return type
    C_STYLE = re.compile(
        r'^\s*(?:(?:' + '|'.join(C_FAMILY_MODIFIERS) + r')\s+)*'
        r'(?:(?P<return_type>[\w\.\$<>,\[\]?]+\s+)+?)?'
        r'(?P<name>' + IDENTIFIER_BASIC + r')\s*\([^)]*\)'
    )
    
    # Python function pattern with optional decorators
    PYTHON = re.compile(
        r'^\s*' + PYTHON_DECORATORS +
        r'def\s+(?P<name>' + IDENTIFIER_BASIC + r')\s*\([^)]*\)\s*(?:->\s*[^:]+)?:'
    )
    
    # JavaScript/TypeScript function patterns (including arrow functions)
    JS_TS = {
        'function_declaration': re.compile(
            r'^\s*(?:export\s+)?(?:async\s+)?function\s+(?P<name>' + IDENTIFIER_BASIC + r')\s*\([^)]*\)'
        ),
        'method_declaration': re.compile(
            r'^\s*(?:static\s+)?(?:async\s+)?(?P<name>' + IDENTIFIER_BASIC + r')\s*\([^)]*\)'
        ),
        'arrow_function': re.compile(
            r'^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>' + IDENTIFIER_BASIC + r')\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z_][a-zA-Z0-9_]*)\s*=>'
        )
    }


class ClassPatterns:
    """Patterns for identifying classes in different languages."""
    
    # C-style class definitions
    C_STYLE = re.compile(
        r'^\s*(?:(?:' + '|'.join(C_FAMILY_MODIFIERS) + r')\s+)*'
        r'class\s+(?P<name>' + IDENTIFIER_BASIC + r')(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?'
    )
    
    # Python class with optional decorators and inheritance
    PYTHON = re.compile(
        r'^\s*' + PYTHON_DECORATORS +
        r'class\s+(?P<name>' + IDENTIFIER_BASIC + r')(?:\s*\([^)]*\))?:'
    )
    
    # JavaScript/TypeScript class
    JS_TS = re.compile(
        r'^\s*(?:export\s+)?class\s+(?P<name>' + IDENTIFIER_BASIC + r')(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?'
    )


class ImportPatterns:
    """Patterns for identifying imports in different languages."""
    
    # Python imports
    PYTHON = {
        'import': re.compile(r'^\s*import\s+(?P<module>[a-zA-Z0-9_.,\s]+)(?:\s+as\s+(?P<alias>[a-zA-Z0-9_]+))?'),
        'from_import': re.compile(r'^\s*from\s+(?P<source>[a-zA-Z0-9_.]+)\s+import\s+(?P<imports>[a-zA-Z0-9_.*,\s]+)')
    }
    
    # JavaScript/TypeScript imports
    JS_TS = {
        'import': re.compile(r'^\s*import\s+(?:{[^}]+}|\*\s+as\s+[a-zA-Z0-9_]+|[a-zA-Z0-9_]+)\s+from\s+[\'"][^\'"]+"[\'"]'),
        'require': re.compile(r'^\s*(?:const|let|var)\s+(?P<name>[a-zA-Z0-9_{}:,\s]+)\s*=\s*require\s*\([\'"][^\'"]+"[\'"]\)')
    }
    
    # Java imports
    JAVA = re.compile(r'^\s*import\s+(?:static\s+)?(?P<package>[a-zA-Z0-9_.]+(?:\.[a-zA-Z0-9_]+|\*));')
    
    # Go imports
    GO = re.compile(r'^\s*import\s+(?:\([^)]+\)|"[^"]+")')


def create_pattern_with_modifiers(
    base_pattern: str,
    modifiers: List[str] = None,
    prefix: str = r'^\s*'
) -> Pattern:
    """
    Create a regex pattern with optional modifiers.
    
    Args:
        base_pattern: The core pattern to match after the modifiers.
        modifiers: A list of modifier keywords (e.g., 'public', 'static').
        prefix: Prefix to add at the start of the pattern (default: whitespace).
        
    Returns:
        A compiled regex pattern.
    """
    if modifiers:
        modifier_pattern = f"(?:(?:{'|'.join(modifiers)})\\s+)*"
        return re.compile(f"{prefix}{modifier_pattern}{base_pattern}")
    return re.compile(f"{prefix}{base_pattern}")
