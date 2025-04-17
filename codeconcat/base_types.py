"""
base_types.py

Holds data classes and typed structures used throughout CodeConCat.
"""

# Rename this file to base_types.py to avoid conflict with Python's types module
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from pydantic import BaseModel, Field, ValidationError, field_validator

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

# --- Security Related Enums and Types ---


class SecuritySeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    # Optional: For ordering or comparison
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            # Define the order from lowest to highest
            order = [
                SecuritySeverity.INFO,
                SecuritySeverity.LOW,
                SecuritySeverity.MEDIUM,
                SecuritySeverity.HIGH,
                SecuritySeverity.CRITICAL,
            ]
            try:
                return order.index(self) < order.index(other)
            except ValueError:
                return (
                    NotImplemented  # Handle cases where a value might not be in the defined order
                )
        return NotImplemented


@dataclass
class SecurityIssue:
    """Represents a potential security issue found."""

    rule_id: str  # Identifier of the rule that triggered the finding
    description: str  # Description of the potential issue
    file_path: str
    line_number: int
    severity: SecuritySeverity  # Enum for severity level
    context: str = ""  # Snippet of code around the issue


# Pydantic model for Custom Security Patterns
class CustomSecurityPattern(BaseModel):
    name: str  # Identifier for the rule
    regex: str  # User-provided regex string
    severity: str  # User-provided severity (e.g., "HIGH", "MEDIUM")

    @field_validator("severity")
    def validate_severity(cls, value):
        try:
            # Ensure severity is uppercase and exists in the enum
            return SecuritySeverity[value.upper()].name
        except KeyError:
            valid_severities = ", ".join([s.name for s in SecuritySeverity])
            raise ValueError(f"Invalid severity '{value}'. Must be one of: {valid_severities}")

    @field_validator("regex")
    def validate_regex(cls, value):
        try:
            # Accept special characters by default; just ensure it's a valid regex
            re.compile(value)
            return value
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")


# --- Core Data Types ---


@dataclass
class Declaration:
    """A declaration in a code file."""

    kind: str
    name: str
    start_line: int
    end_line: int
    modifiers: Set[str] = field(default_factory=set)
    docstring: str = ""
    children: List["Declaration"] = field(default_factory=list)

    def __post_init__(self):
        """Initialize a declaration."""
        pass


@dataclass
class TokenStats:
    """Statistics about token usage."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class ParsedFileData:
    """Data structure for a single parsed code file."""

    file_path: str
    language: str
    content: str
    declarations: List[Declaration] = field(default_factory=list)
    token_stats: Optional[TokenStats] = None
    security_issues: List[SecurityIssue] = field(default_factory=list)


@dataclass
class AnnotatedFileData:
    """Data structure for annotated file content."""

    file_path: str
    language: str
    content: str
    annotated_content: str
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ParsedDocData:
    """Data structure for a parsed documentation file."""

    file_path: str
    doc_type: str
    content: str


@dataclass
class ParseResult:
    """Result of parsing a code file."""

    file_path: str
    language: str
    content: str
    declarations: List[Declaration]


# Pydantic model for Global Configuration
class CodeConCatConfig(BaseModel):
    """Global configuration object using Pydantic for validation.

    Merged from CLI args + .codeconcat.yml.
    Fields are validated upon instantiation.
    """

    target_path: str = "."
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    github_ref: Optional[str] = None
    include_languages: List[str] = Field(default_factory=list)
    exclude_languages: List[str] = Field(default_factory=list)
    include_paths: List[str] = Field(default_factory=list)
    exclude_paths: List[str] = Field(default_factory=list)
    extract_docs: bool = False
    show_skip: bool = False  # Whether to print skipped files after parsing
    merge_docs: bool = False
    doc_extensions: List[str] = Field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])
    custom_extension_map: Dict[str, str] = Field(default_factory=dict)
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
    remove_docstrings: bool = False
    show_line_numbers: bool = False
    enable_token_counting: bool = False
    enable_security_scanning: bool = True  # Default enable security scanning
    security_scan_severity_threshold: str = "MEDIUM"  # Minimum severity to report
    security_ignore_paths: List[str] = Field(
        default_factory=list
    )  # Glob patterns for files/dirs to skip
    security_ignore_patterns: List[str] = Field(
        default_factory=list
    )  # Regex for findings content to ignore
    security_custom_patterns: List[CustomSecurityPattern] = Field(
        default_factory=list
    )  # User-defined rules

    # Sorting
    sort_files: bool = False

    # Advanced options
    max_workers: int = 4
    split_output: int = 1  # Number of files to split output into

    # Markdown cross-linking
    cross_link_symbols: bool = False  # Option to cross-link symbol summaries and definitions

    # --- Pydantic Validators --- #

    @field_validator("format")
    def validate_format(cls, value):
        if value not in VALID_FORMATS:
            raise ValueError(
                f"Invalid format '{value}'. Must be one of: {', '.join(VALID_FORMATS)}"
            )
        return value

    @field_validator("security_scan_severity_threshold")
    def validate_severity_threshold(cls, value):
        try:
            # Ensure threshold is uppercase for enum matching
            return SecuritySeverity[value.upper()].name
        except KeyError:
            valid_severities = ", ".join([s.name for s in SecuritySeverity])
            raise ValueError(
                f"Invalid security_scan_severity_threshold: '{value}'. "
                f"Must be one of: {valid_severities}"
            )

    @field_validator("split_output")
    def check_split_output(cls, v):
        if v < 1:
            raise ValueError("split_output must be 1 or greater")
        return v

    # The validator for security_custom_patterns automatically handles
    # validating each item in the list against the CustomSecurityPattern model,
    # including its own validators for 'severity' and 'regex'.
