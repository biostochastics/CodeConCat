"""
types.py

Holds data classes and typed structures used throughout CodeConCat.
"""

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


@dataclass
class AnnotatedFileData:
    """
    A file's annotated content, ready to be written (Markdown/JSON).
    """
    file_path: str
    language: str
    annotated_content: str
    content: str = ""
    summary: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ParsedDocData:
    """
    Represents a doc file, storing raw text + file path + doc type (md, rst, etc.).
    """
    file_path: str
    doc_type: str
    content: str


@dataclass
class CodeConCatConfig:
    """
    Global configuration object. Merged from CLI args + .codeconcat.yml.

    Fields:
      - target_path: local directory or placeholder for GitHub
      - github_url: optional GitHub repository URL
      - github_token: personal access token for private repos
      - github_ref: optional GitHub reference (branch/tag)
      - include_languages / exclude_languages
      - include_paths / exclude_paths: patterns for including/excluding
      - extract_docs: whether to parse docs
      - merge_docs: whether to merge doc content into the same output
      - doc_extensions: list of recognized doc file extensions
      - custom_extension_map: user-specified extension→language
      - output: final file name
      - format: 'markdown' or 'json'
      - max_workers: concurrency
      - disable_tree: whether to disable directory structure
      - disable_copy: whether to disable copying output
      - disable_annotations: whether to disable annotations
      - disable_symbols: whether to disable symbol extraction
      - include_file_summary: whether to include file summaries
      - include_directory_structure: whether to show directory structure
      - remove_comments: whether to remove comments from output
      - remove_empty_lines: whether to remove empty lines
      - show_line_numbers: whether to show line numbers
    """

    # Basic path or GitHub info
    target_path: str = "."
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    github_ref: Optional[str] = None

    # Language filtering
    include_languages: List[str] = field(default_factory=list)
    exclude_languages: List[str] = field(default_factory=list)

    # Path filtering
    include_paths: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)

    # Doc extraction toggles
    extract_docs: bool = False
    merge_docs: bool = False
    doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])

    # Custom extension→language
    custom_extension_map: Dict[str, str] = field(default_factory=dict)

    # Output
    output: str = "code_concat_output.md"
    format: str = "markdown"
    max_workers: int = 4

    # Feature toggles
    disable_tree: bool = False
    disable_copy: bool = False
    disable_annotations: bool = False
    disable_symbols: bool = False

    # Display options
    include_file_summary: bool = False
    include_directory_structure: bool = False
    remove_comments: bool = False
    remove_empty_lines: bool = False
    show_line_numbers: bool = False
