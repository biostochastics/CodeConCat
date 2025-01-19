# file: codeconcat/parser/language_parsers/java_parser.py

import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_java(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = JavaParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="java",
        content=content,
        declarations=declarations
    )

class JavaParser(BaseParser):
    def __init__(self):
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """Set up patterns for Java code declarations."""
        self.patterns = {}
        
        # Java uses curly braces
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # Class pattern (including modifiers and inheritance)
        class_pattern = r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*class\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)"
        self.patterns["class"] = re.compile(class_pattern)

        # Interface pattern
        interface_pattern = r"^\s*(?:public\s+|private\s+|protected\s+)*interface\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)"
        self.patterns["interface"] = re.compile(interface_pattern)

        # Method pattern (including modifiers and return type)
        method_pattern = r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+)*(?:[a-zA-Z_][a-zA-Z0-9_<>[\],\s]*\s+)?(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s*\("
        self.patterns["method"] = re.compile(method_pattern)

        # Field pattern (including modifiers and type)
        field_pattern = r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*(?:[a-zA-Z_][a-zA-Z0-9_<>[\],\s]*\s+)(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s*[=;]"
        self.patterns["field"] = re.compile(field_pattern)

        self.modifiers = {"public", "private", "protected", "static", "final", "abstract"}

    def parse(self, content: str) -> List[Declaration]:
        """Parse Java code content and return list of declarations."""
        declarations = []
        lines = content.split('\n')
        in_comment = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('//'):
                i += 1
                continue
                
            # Handle block comments
            if "/*" in line and not in_comment:
                in_comment = True
                i += 1
                continue
            elif in_comment:
                if "*/" in line:
                    in_comment = False
                i += 1
                continue
            
            # Collect modifiers
            modifiers = set()
            words = line.split()
            j = 0
            while j < len(words) and words[j] in self.modifiers:
                modifiers.add(words[j])
                j += 1
            
            # Try to match patterns
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("n")
                    if not name:
                        continue
                        
                    # Find block end for block-based declarations
                    end_line = i
                    if kind in ("class", "interface", "enum", "method"):
                        brace_count = 0
                        found_opening = False
                        
                        # Find the end of the block by counting braces
                        j = i
                        while j < len(lines):
                            curr_line = lines[j].strip()
                            
                            if "{" in curr_line:
                                found_opening = True
                                brace_count += curr_line.count("{")
                            if "}" in curr_line:
                                brace_count -= curr_line.count("}")
                                
                            if found_opening and brace_count == 0:
                                end_line = j
                                break
                            j += 1
                            
                        # Extract docstring if present
                        docstring = self.extract_docstring(lines, i, end_line)
                        
                        # Add the declaration
                        declarations.append(Declaration(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=end_line + 1,
                            modifiers=modifiers,
                            docstring=docstring or ""
                        ))
                        
                        # Parse nested declarations only for class/interface/enum
                        if kind in ("class", "interface", "enum") and end_line > i:
                            nested_content = []
                            for k in range(i+1, end_line):
                                nested_line = lines[k].strip()
                                if nested_line and not nested_line.startswith('//'):
                                    nested_content.append((k, lines[k]))
                            
                            if nested_content:
                                for k, nested_line in nested_content:
                                    # Try to match each pattern
                                    for nested_kind, nested_pattern in self.patterns.items():
                                        if nested_kind in ("class", "interface", "enum"):
                                            continue  # Skip nested class declarations for now
                                        nested_match = nested_pattern.match(nested_line.strip())
                                        if nested_match:
                                            nested_name = nested_match.group("n")
                                            if nested_name:
                                                # Extract modifiers
                                                nested_modifiers = set()
                                                nested_words = nested_line.strip().split()
                                                m = 0
                                                while m < len(nested_words) and nested_words[m] in self.modifiers:
                                                    nested_modifiers.add(nested_words[m])
                                                    m += 1
                                                
                                                # Find the end of the nested block
                                                nested_end_line = k
                                                if "{" in nested_line:
                                                    nested_brace_count = 1
                                                    n = k + 1
                                                    while n < len(lines):
                                                        curr_nested_line = lines[n].strip()
                                                        if "{" in curr_nested_line:
                                                            nested_brace_count += curr_nested_line.count("{")
                                                        if "}" in curr_nested_line:
                                                            nested_brace_count -= curr_nested_line.count("}")
                                                        if nested_brace_count == 0:
                                                            nested_end_line = n
                                                            break
                                                        n += 1
                                                
                                                declarations.append(Declaration(
                                                    kind=nested_kind,
                                                    name=nested_name,
                                                    start_line=k + 1,
                                                    end_line=nested_end_line + 1,
                                                    modifiers=nested_modifiers,
                                                    docstring=""
                                                ))
                        i = end_line + 1
                        break
                    else:
                        # For non-block declarations (fields, etc.)
                        declarations.append(Declaration(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=i + 1,
                            modifiers=modifiers,
                            docstring=""
                        ))
                        i += 1
                        break
            else:
                i += 1
                
        # Filter declarations to keep only top-level class/interface/enum declarations and their members
        filtered_declarations = []
        top_level_declarations = [d for d in declarations if d.kind in ("class", "interface", "enum")]
        
        for top_level in top_level_declarations:
            filtered_declarations.append(top_level)
            
            # Add members of this top-level declaration
            start_line = top_level.start_line
            end_line = top_level.end_line
            for d in declarations:
                if d.start_line > start_line and d.end_line < end_line:
                    filtered_declarations.append(d)
                    
        return filtered_declarations

    def extract_docstring(self, lines, start, end):
        """Extract docstring from Java code."""
        docstring = ""
        for line in lines[start+1:end]:
            if line.strip().startswith("//"):
                docstring += line.strip().replace("//", "", 1).strip() + "\n"
        return docstring.strip()