"""Base types used throughout CodeConcat."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Declaration:
    """
    Represents a top-level construct in a code file, e.g. a function, class, or symbol.
    Kinds can be: 'function', 'class', 'struct', 'symbol'
    """
    kind: str
    name: str
    start_line: int
    end_line: int

@dataclass
class ParsedFileData:
    """
    Parsed output of a single code file.
    """
    file_path: str
    language: str
    content: str
    declarations: List[Declaration] = field(default_factory=list)
    token_stats: Optional['TokenStats'] = None  # Forward reference
    security_issues: List['SecurityIssue'] = field(default_factory=list)  # Forward reference

@dataclass
class CodeConCatConfig:
    """Global configuration object."""
    target_path: str = "."
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    github_ref: Optional[str] = None
    include_languages: List[str] = field(default_factory=list)
    exclude_languages: List[str] = field(default_factory=list)
    include_paths: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)
    extract_docs: bool = False
    merge_docs: bool = False
    doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])
    custom_extension_map: Dict[str, str] = field(default_factory=dict)
    output: str = "code_concat_output.md"
    format: str = "markdown"
    max_workers: int = 4
    disable_tree: bool = False
    disable_copy: bool = False
    disable_annotations: bool = False
    disable_symbols: bool = False
    include_file_summary: bool = False
    include_directory_structure: bool = False
    remove_comments: bool = False
    remove_empty_lines: bool = False
    show_line_numbers: bool = False
