"""
base_types.py

Holds data classes and typed structures used throughout CodeConCat.
"""

from __future__ import annotations

import abc
import re
import threading
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Rename this file to base_types.py to avoid conflict with Python's types module


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

VALID_FORMATS = {"markdown", "json", "xml", "text"}

# --- Content Segment and Compression Types ---


class ContentSegmentType(Enum):
    """Types of content segments for compression.

    This enum defines the different types of content segments that can be
    created during the compression process to optimize output size while
    preserving important code sections.

    Attributes:
        CODE: Represents a code segment that should be preserved in output
        OMITTED: Represents code that has been removed and replaced with a placeholder
        METADATA: Contains metadata or summary information about the code
    """

    CODE = "code"  # Kept code segment
    OMITTED = "omitted"  # Omitted code segment (replaced with placeholder)
    METADATA = "metadata"  # Metadata or summary segment


@dataclass
class ContentSegment:
    """Represents a segment of code content for compression.

    This dataclass holds information about a specific segment of code,
    including its type, content, line range, and any associated metadata.
    Used during the compression process to organize and manage code segments.

    Attributes:
        segment_type: The type of this segment (CODE, OMITTED, or METADATA)
        content: The actual text content of the segment
        start_line: Starting line number in the original file
        end_line: Ending line number in the original file
        metadata: Additional information about the segment (e.g., security issues, complexity)

    Complexity: O(1) for all operations (simple data container)
    """

    segment_type: ContentSegmentType
    content: str
    start_line: int
    end_line: int
    metadata: dict[str, Any] = field(
        default_factory=dict
    )  # For additional info like security issues


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

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self == other or self < other
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return not (self <= other)
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self == other or self > other
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
    """Custom security pattern for detecting sensitive data in code.

    Provides user-defined regex patterns for security scanning with built-in
    protection against Regular Expression Denial of Service (ReDoS) attacks.

    Attributes:
        name: Identifier for the security rule
        regex: User-provided regex pattern string (max 1000 chars)
        severity: Severity level (HIGH, MEDIUM, LOW, CRITICAL)

    Security Features:
        - ReDoS protection: 2-second timeout on regex compilation
        - Pattern length limitation: Maximum 1000 characters
        - Thread-based sandboxing for regex validation
        - Safe validation before pattern usage

    Example:
        pattern = CustomSecurityPattern(
            name="api_key_detection",
            regex=r"api[_-]?key['\"]*\\s*[:=]\\s*['\"]*[a-zA-Z0-9]+",
            severity="HIGH"
        )
    """

    name: str  # Identifier for the rule
    regex: str  # User-provided regex string (max 1000 chars, validated for ReDoS)
    severity: str  # User-provided severity (e.g., "HIGH", "MEDIUM")

    @field_validator("severity")
    def validate_severity(cls, value):
        try:
            # Ensure severity is uppercase and exists in the enum
            return SecuritySeverity[value.upper()].name
        except KeyError as e:
            valid_severities = ", ".join([s.name for s in SecuritySeverity])
            raise ValueError(
                f"Invalid severity '{value}'. Must be one of: {valid_severities}"
            ) from e

    @field_validator("regex")
    def validate_regex(cls, value):
        """Validate regex pattern with timeout protection against ReDoS attacks.

        Uses a separate thread with a 2-second timeout to prevent malicious
        or overly complex regex patterns from causing resource exhaustion.
        """
        import queue

        result_queue: queue.Queue = queue.Queue()

        def compile_regex():
            try:
                # Limit regex length as additional protection
                if len(value) > 1000:
                    result_queue.put((False, "Regex pattern too long (max 1000 chars)"))
                    return

                # Compile the regex
                compiled = re.compile(value)

                # Test with a simple string to catch immediate issues
                test_str = "test_string_for_validation"
                try:
                    compiled.search(test_str)
                except Exception:
                    # If search fails on simple string, pattern is problematic
                    result_queue.put((False, "Regex pattern failed basic validation"))
                    return

                result_queue.put((True, value))
            except re.error as e:
                result_queue.put((False, f"Invalid regex pattern: {e}"))
            except Exception as e:
                result_queue.put((False, f"Regex validation error: {e}"))

        # Run compilation in separate thread with timeout
        thread = threading.Thread(target=compile_regex, daemon=True)
        thread.start()
        thread.join(timeout=2.0)  # 2 second timeout

        if thread.is_alive():
            # Thread is still running after timeout
            raise ValueError("Regex pattern compilation timed out (possible ReDoS pattern)")

        try:
            success, result = result_queue.get_nowait()
            if success:
                return result
            else:
                raise ValueError(result)
        except queue.Empty as e:
            raise ValueError("Regex validation failed unexpectedly") from e


# --- Data Structures for Parsing & Processing ---


@dataclass
class Declaration:
    """A declaration in a code file."""

    kind: str
    name: str
    start_line: int
    end_line: int
    modifiers: set[str] = field(default_factory=set)
    docstring: str = ""
    signature: str = ""  # Function/method signature without body
    children: list[Declaration] = field(default_factory=list)

    def __post_init__(self):
        """Initialize a declaration."""
        pass


# Moved from processor.token_counter to break circular import
@dataclass
class TokenStats:
    """Token statistics for a file."""

    gpt4_tokens: int
    claude_tokens: int


@dataclass
class ParsedFileData:
    """Data structure for a single parsed code file."""

    file_path: str
    content: str | None  # Optional because reading might fail
    language: str | None
    declarations: list[Declaration] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    token_stats: TokenStats | None = None
    security_issues: list[SecurityIssue] = field(default_factory=list)
    parse_result: Any | None = None


# New ParseResult Dataclass
@dataclass
@dataclass
class ParseResult:
    # Required fields first (no defaults)
    declarations: list[Declaration] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    missed_features: list[str] = field(default_factory=list)  # ["methods", "async_functions", etc.]
    security_issues: list[Any] = field(default_factory=list)
    # Optional fields with defaults
    ast_root: Any | None = None  # Holds tree_sitter.Node if available
    error: str | None = None  # To report parsing errors
    engine_used: str = "regex"  # Track which engine actually produced result
    parser_quality: str = "unknown"  # "full", "partial", "basic"
    # Additional fields used by parsers
    file_path: str | None = None
    language: str | None = None
    content: str | None = None
    token_stats: Any | None = None
    # Additional fields that file_parser.py expects
    module_docstring: str | None = None
    module_name: str | None = None
    degraded: bool = False


class WritableItem(ABC):
    """Abstract base class for items that can be rendered by different writers."""

    # REMOVED: Abstract property for file_path.
    # Relying on subclasses to define the field directly.
    # @property
    # @abstractmethod
    # def file_path(self) -> str:
    #     """The path to the source file."""
    #     pass

    @abstractmethod
    def render_text_lines(self, config: CodeConCatConfig) -> list[str]:
        """Renders the item as a list of strings for the text writer."""
        pass

    @abstractmethod
    def render_markdown_chunks(self, config: CodeConCatConfig) -> list[str]:
        """Renders the item as a list of markdown string chunks."""
        pass

    @abstractmethod
    def render_json_dict(self, config: CodeConCatConfig) -> dict[str, Any]:
        """Renders the item as a dictionary for the JSON writer."""
        pass

    @abstractmethod
    def render_xml_element(self, config: CodeConCatConfig) -> ET.Element:
        """Renders the item as an XML element structure."""
        pass


@dataclass
class AnnotatedFileData(WritableItem):
    """Data structure for annotated file content, including structured analysis results.

    This class focuses solely on storing structured data and does not contain any rendering logic.
    Rendering is delegated to specialized rendering adapters for different output formats.
    """

    # Core file info - required parameters (no defaults) must come first
    file_path: str
    language: str
    content: str  # Original content
    annotated_content: str  # Potentially processed content (e.g., comments removed)

    # Optional AI-generated additions
    summary: str = ""  # AI-generated overall summary

    # Structured analysis results (passed from ParsedFileData) - parameters with defaults
    declarations: list[Declaration] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    token_stats: TokenStats | None = None
    security_issues: list[SecurityIssue] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def render_text_lines(self, config: CodeConCatConfig) -> list[str]:
        from codeconcat.writer.rendering_adapters import TextRenderAdapter

        return TextRenderAdapter.render_annotated_file(self, config)

    def render_markdown_chunks(self, config: CodeConCatConfig) -> list[str]:
        from codeconcat.writer.rendering_adapters import MarkdownRenderAdapter

        return MarkdownRenderAdapter.render_annotated_file(self, config)

    def render_json_dict(self, config: CodeConCatConfig) -> dict[str, Any]:
        from codeconcat.writer.rendering_adapters import JsonRenderAdapter

        return JsonRenderAdapter.annotated_file_to_dict(self, config)

    def render_xml_element(self, config: CodeConCatConfig) -> ET.Element:
        from codeconcat.writer.rendering_adapters import XmlRenderAdapter

        return XmlRenderAdapter.create_annotated_file_element(self, config)


# New Parser Interface
class ParserInterface(abc.ABC):
    """Abstract Base Class defining the interface for language parsers."""

    @abc.abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse the given code content.

        Args:
            content: The code content as a string.
            file_path: The path to the file being parsed (for context/error reporting).

        Returns:
            A ParseResult object containing declarations, imports, potential AST,
            error information, and the engine used.
        """
        pass


class EnhancedParserInterface(ParserInterface):
    """Enhanced interface for language parsers with improved capabilities.

    This extends the base ParserInterface with methods for capability reporting
    and validation, supporting more robust parser selection and fallback logic.
    """

    def get_capabilities(self) -> dict[str, bool]:
        """Report the capabilities of this parser.

        Returns:
            A dictionary mapping capability names to booleans indicating support.
            Examples include: 'can_parse_functions', 'can_parse_classes', etc.
        """
        return {
            "can_parse_functions": True,
            "can_parse_classes": True,
            "can_parse_imports": True,
            "can_extract_docstrings": True,
        }

    def validate(self) -> bool:
        """Validate that the parser is properly configured and ready to use.

        This method can be used to check for required dependencies, valid
        configurations, or other prerequisites before attempting parsing.

        Returns:
            True if the parser is valid and ready to use, False otherwise.
        """
        return True


@dataclass
class ParsedDocData(WritableItem):
    """Data structure for parsed documentation files (e.g., Markdown)."""

    # Required fields first
    file_path: str
    content: str

    # Fields with defaults
    doc_type: str = "markdown"  # Default to markdown, can be overridden
    summary: str | None = None  # Optional summary
    tags: list[str] = field(default_factory=list)

    # Implement WritableItem properties and methods
    def render_text_lines(self, config: CodeConCatConfig) -> list[str]:
        from codeconcat.writer.rendering_adapters import TextRenderAdapter

        return TextRenderAdapter.render_doc_file(self, config)

    def render_markdown_chunks(self, config: CodeConCatConfig) -> list[str]:
        from codeconcat.writer.rendering_adapters import MarkdownRenderAdapter

        return MarkdownRenderAdapter.render_doc_file(self, config)

    def render_json_dict(self, config: CodeConCatConfig) -> dict[str, Any]:
        from codeconcat.writer.rendering_adapters import JsonRenderAdapter

        return JsonRenderAdapter.doc_file_to_dict(self, config)

    def render_xml_element(self, config: CodeConCatConfig) -> ET.Element:
        from codeconcat.writer.rendering_adapters import XmlRenderAdapter

        return XmlRenderAdapter.create_doc_file_element(self, config)


# --- Core Data Types ---


# Abstract Base Class for Writable Items
# WritableItem class has been moved up before AnnotatedFileData to prevent circular references


# --- Configuration Model ---


class CodeConCatConfig(BaseModel):
    """Global configuration object using Pydantic for validation.

    Merged from CLI args + .codeconcat.yml.
    Fields are validated upon instantiation.
    """

    # For backward compatibility with code that treats this like a dictionary
    def get(self, key: str, default=None):
        """Provide dictionary-like access with .get() method"""
        return getattr(self, key, default)

    # --- Add missing parser config fields ---
    parser_engine: str = Field(
        "tree_sitter",
        description="Parsing engine to use ('tree_sitter' or 'regex').",
        validate_default=True,
    )
    fallback_to_regex: bool = Field(
        True,
        description="If tree-sitter parsing fails, fallback to the simpler regex parser.",
        validate_default=True,
    )

    use_enhanced_parsers: bool = Field(
        True,
        description="Use enhanced regex parsers where available instead of standard ones.",
        validate_default=True,
    )

    use_enhanced_pipeline: bool = Field(
        True,
        description="Use the enhanced parsing pipeline with progressive fallbacks (tree-sitter → enhanced → standard).",
        validate_default=True,
    )
    # --- End added fields ---

    target_path: str = Field(
        ".", description="Local path to process if source_url is not provided."
    )
    # Rename github_url -> source_url
    source_url: str | None = Field(
        None,
        description="URL of the remote source (Git repository, ZIP archive). If set, target_path is ignored for input.",
    )
    github_token: str | None = Field(
        None,
        description="GitHub token for accessing private repositories or increasing rate limits.",
    )
    # Rename github_ref -> source_ref
    source_ref: str | None = Field(
        None,
        description="Specific branch, tag, or commit SHA to use from the Git repository specified in source_url.",
    )
    # Removed duplicate - using the one below with None
    exclude_languages: list[str] = Field(default_factory=list)
    include_paths: list[str] = Field(
        default_factory=list, description="Patterns for files/directories to include."
    )
    exclude_paths: list[str] = Field(
        default_factory=list, description="Patterns for files/directories to exclude."
    )
    use_gitignore: bool = Field(
        True, description="Whether to respect rules found in .gitignore files."
    )
    use_default_excludes: bool = Field(
        True, description="Whether to use the built-in default exclude patterns."
    )
    include_languages: list[str] | None = Field(
        None, description="Specific languages to include (by identifier)."
    )
    # Removed duplicate exclude_languages
    extract_docs: bool = False
    show_skip: bool = False  # Whether to print skipped files after parsing
    merge_docs: bool = False
    doc_extensions: list[str] = Field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])
    custom_extension_map: dict[str, str] = Field(default_factory=dict)
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
    security_ignore_paths: list[str] = Field(
        default_factory=list
    )  # Glob patterns for files/dirs to skip
    security_ignore_patterns: list[str] = Field(
        default_factory=list
    )  # Regex for findings content to ignore
    security_custom_patterns: list[CustomSecurityPattern] = Field(default_factory=list)

    # Semgrep integration options
    enable_semgrep: bool = Field(
        False,
        description="Enable semgrep security scanning using the Apiiro malicious code ruleset",
    )
    # Removed duplicate semgrep_ruleset - using the one below
    semgrep_languages: list[str] | None = Field(
        None,
        description="list of languages to scan with semgrep (defaults to all detected languages)",
    )
    install_semgrep: bool = Field(
        False, description="Install semgrep and the Apiiro ruleset if not already installed"
    )
    strict_security: bool = Field(
        False, description="Fail validation when suspicious content is detected"
    )  # Fail validation when suspicious content is detected
    # External Semgrep Scanning
    enable_external_semgrep: bool = Field(
        True, description="Whether to enable external security scanning using Semgrep."
    )
    semgrep_ruleset: str | None = Field(
        "p/ci",
        description="Semgrep ruleset to use (e.g., 'p/ci', path to rules, or registry name). Set to None to use Semgrep defaults.",
    )

    # Sorting
    sort_files: bool = False

    # Advanced options
    # max_workers already defined above on line 543
    split_output: int = 1  # Number of files to split output into
    verbose: int = 0  # Added for verbose logging control
    quiet: bool = False  # Suppress all non-error output for API usage

    # Markdown cross-linking
    cross_link_symbols: bool = False  # Option to cross-link symbol summaries and definitions

    # Progress Bar
    disable_progress_bar: bool = False  # Disable tqdm progress bars

    # New Output Structure/Verbosity Controls
    output_preset: str | None = "medium"  # 'lean', 'medium', 'full', or None
    include_repo_overview: bool = True  # Default based on 'medium'
    include_file_index: bool = True  # Default based on 'medium'
    # include_file_summary already defined above on line 549
    include_declarations_in_summary: bool = True  # Default based on 'medium'
    include_imports_in_summary: bool = (
        False  # Default based on 'medium' (maybe imports are too verbose?)
    )
    xml_processing_instructions: bool = Field(
        True, description="Include AI processing instructions in XML output for LLM navigation"
    )
    include_tokens_in_summary: bool = True  # Default based on 'medium'
    include_security_in_summary: bool = True  # Default based on 'medium'

    # use_default_excludes already defined above on line 529
    # New flag for output masking
    mask_output_content: bool = Field(
        False,
        description="Mask sensitive data directly in the final output content (if security scanning is enabled).",
    )

    # --- Compression Options ---
    enable_compression: bool = Field(
        False,
        description="Enable content compression to reduce output size while preserving important segments.",
    )
    compression_level: str = Field(
        "medium",
        description="Compression intensity: 'low', 'medium', 'high', or 'aggressive'.",
    )
    compression_placeholder: str = Field(
        "[...code omitted ({lines} lines, {issues} issues)...]",
        description="Template for placeholder text replacing omitted segments.",
    )
    compression_keep_threshold: int = Field(
        3,
        description="Minimum lines to consider keeping a segment (smaller segments always kept).",
    )
    compression_keep_tags: list[str] = Field(
        default_factory=lambda: ["important", "keep", "security"],
        description="Special comment tags that mark segments to always keep despite compression.",
    )

    # --- Processing Options ---
    analysis_prompt: str | None = Field(
        None,
        description="Analysis prompt for AI-assisted code analysis (loaded from file or provided directly).",
    )
    # ... rest of the code remains the same ...
