"""
types.py

Holds data classes and typed structures used throughout CodeConCat.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Declaration:
    """
    Represents a top-level construct in a code file, e.g. a function or class.
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
      - include_languages / exclude_languages
      - exclude_paths: patterns for ignoring
      - docs: whether to parse docs
      - merge_docs: whether to merge doc content into the same output
      - doc_extensions: list of recognized doc file extensions
      - custom_extension_map: user-specified extension→language
      - output: final file name
      - format: 'markdown' or 'json'
      - max_workers: concurrency
      - ...
    """
    target_path: str = "."
    github_url: Optional[str] = None

    include_languages: List[str] = field(default_factory=list)
    exclude_languages: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)

    docs: bool = False
    merge_docs: bool = False
    doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])

    custom_extension_map: Dict[str, str] = field(default_factory=dict)

    output: str = "code_concat_output.md"
    format: str = "markdown"  # or "json"

    max_workers: int = 4
