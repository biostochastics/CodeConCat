"""
base_types.py

Holds data classes and typed structures used throughout CodeConCat.
"""

# Rename this file to base_types.py to avoid conflict with Python's types module
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

PROGRAMMING_QUOTES = [
    '"Clean code always looks like it was written by someone who cares." - Robert C. Martin',
    '"First, solve the problem. Then write the code." - John Johnson',
    '"Any fool can write code that a computer can understand. Good programmers write code that humans can understand." - Martin Fowler',
    "\"Programming isn't about what you know; it's about what you can figure out.\" - Chris Pine",
    '"Code is like humor. When you have to explain it, it\'s bad." - Cory House',
    '"The most important property of a program is whether it accomplishes the intention of its user." - C.A.R. Hoare',
    "\"Good code is its own best documentation. As you're about to add a comment, ask yourself, 'How can I improve the code so that this comment isn't needed?'\" - Steve McConnell",
    '"Measuring programming progress by lines of code is like measuring aircraft building progress by weight." - Bill Gates',
    '"Talk is cheap. Show me the code." - Linus Torvalds',
    '"Truth can only be found in one place: the code." - Robert C. Martin',
    '"It is not enough for code to work." - Robert C. Martin',
    '"Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it." - Brian W. Kernighan',
    '"Sometimes it pays to stay in bed on Monday rather than spending the rest of the week debugging Monday\'s code." - Dan Salomon',
    '"Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live." - Rick Osborne',
]

VALID_FORMATS = {"markdown", "json", "xml"}

@dataclass
class SecurityIssue:
    """Represents a detected security issue in the code."""

    line_number: int
    line_content: str
    issue_type: str
    severity: str
    description: str


@dataclass
class TokenStats:
    """Token statistics for a file."""

    gpt3_tokens: int
    gpt4_tokens: int
    davinci_tokens: int
    claude_tokens: int


@dataclass
class Declaration:
    """A declaration in a code file."""

    kind: str
    name: str
    start_line: int
    end_line: int
    modifiers: Set[str] = field(default_factory=set)
    docstring: str = ""

    def __post_init__(self):
        """Initialize a declaration."""
        pass


@dataclass
class ParsedFileData:
    """
    Parsed output of a single code file.
    """

    file_path: str
    language: str
    content: str
    declarations: List[Declaration] = field(default_factory=list)
    token_stats: Optional[TokenStats] = None
    security_issues: List[SecurityIssue] = field(default_factory=list)


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
    """Global configuration object. Merged from CLI args + .codeconcat.yml.

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
      - format: 'markdown', 'json', or 'xml'
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
    disable_ai_context: bool = False
    include_file_summary: bool = True
    include_directory_structure: bool = True
    remove_comments: bool = False
    remove_empty_lines: bool = False
    show_line_numbers: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.format not in VALID_FORMATS:
            raise ValueError(f"Invalid format '{self.format}'. Must be one of: {', '.join(VALID_FORMATS)}")
