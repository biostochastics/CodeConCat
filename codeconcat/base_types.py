"""Holds data classes and typed structures used throughout CodeConCat."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
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


# --- Module-level helper for multiprocessing (must be picklable) ---


def _compile_and_test_regex(pattern: str, result_queue: Any) -> None:
    """Compile regex and test with backtracking-prone strings.

    This function is defined at module level to be picklable for multiprocessing.
    Used by CustomSecurityPattern.validate_regex for ReDoS-safe validation.

    Args:
        pattern: The regex pattern to compile and test.
        result_queue: A multiprocessing Queue to put the result into.

    """
    try:
        compiled = re.compile(pattern)
        # Test with potential backtracking triggers
        test_strings = ["a" * 50, "ab" * 25, "x" * 30 + "y"]
        for test_str in test_strings:
            compiled.search(test_str)
        result_queue.put((True, pattern))
    except re.error as e:
        result_queue.put((False, f"Invalid regex: {e}"))
    except Exception as e:
        result_queue.put((False, f"Validation error: {e}"))


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


class SecuritySeverity(IntEnum):
    """Enumerate and order security severity levels.

    Uses IntEnum to provide automatic ordering and comparison methods.
    Severity levels are ordered from lowest (INFO=0) to highest (CRITICAL=4).

    Attributes:
        INFO: Informational finding (0)
        LOW: Low severity issue (1)
        MEDIUM: Medium severity issue (2)
        HIGH: High severity issue (3)
        CRITICAL: Critical severity issue (4)

    """

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SecurityIssue:
    """Represents a potential security issue found during scanning.

    Attributes:
        rule_id: Identifier of the rule that triggered the finding
        description: Description of the potential issue
        file_path: Path to the file containing the issue
        line_number: Line number where the issue was found
        severity: SecuritySeverity enum level (INFO=0 to CRITICAL=4)
        context: Snippet of code around the issue for context

    """

    rule_id: str  # Identifier of the rule that triggered the finding
    description: str  # Description of the potential issue
    file_path: str
    line_number: int
    severity: SecuritySeverity  # Enum for severity level
    context: str = ""  # Snippet of code around the issue


# Pydantic model for Custom Security Patterns
class CustomSecurityPattern(BaseModel):
    r"""Custom security pattern for detecting sensitive data in code.

    Provides user-defined regex patterns for security scanning with built-in
    protection against Regular Expression Denial of Service (ReDoS) attacks.

    Attributes:
        name: Identifier for the security rule.
        regex: User-provided regex pattern string (max 1000 chars).
        severity: Severity level (HIGH, MEDIUM, LOW, CRITICAL).

    ReDoS protection includes a 2-second timeout on regex compilation,
    pattern length limitation to 1000 characters maximum,
    thread-based sandboxing for regex validation,
    and safe validation before pattern usage.

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
    @classmethod
    def validate_severity(cls, value: str) -> str:
        """Validate if the given severity value corresponds to a valid `SecuritySeverity` enum.

        Args:
            value: The severity level to validate.

        Returns:
            The valid severity level from the `SecuritySeverity` enum.

        Raises:
            ValueError: If the given value is not a valid severity level.

        """
        try:
            # Ensure severity is uppercase and exists in the enum
            return SecuritySeverity[value.upper()].name
        except KeyError as e:
            valid_severities = ", ".join([s.name for s in SecuritySeverity])
            raise ValueError(
                f"Invalid severity '{value}'. Must be one of: {valid_severities}"
            ) from e

    @field_validator("regex")
    @classmethod
    def validate_regex(cls, value: str) -> str:
        """Validate regex pattern with proper ReDoS protection.

        Uses multiprocessing for true isolation (can actually kill runaway processes)
        combined with static analysis of known ReDoS patterns.

        Security features:
            - Pattern length limitation (max 1000 chars)
            - Static analysis for known ReDoS vulnerability patterns
            - Multiprocessing-based timeout that can actually terminate
            - Test validation with backtracking-prone strings
        """
        from multiprocessing import Process
        from multiprocessing import Queue as MPQueue

        from codeconcat.constants import (
            MAX_REGEX_LENGTH,
            REDOS_PATTERNS,
            REDOS_TIMEOUT_SECONDS,
        )

        # Length limit check (fast, no process needed)
        if len(value) > MAX_REGEX_LENGTH:
            raise ValueError(f"Regex pattern too long (max {MAX_REGEX_LENGTH} chars)")

        # Static analysis for known ReDoS patterns (fast, no process needed)
        for indicator in REDOS_PATTERNS:
            if re.search(indicator, value):
                raise ValueError(
                    "Regex pattern contains potential ReDoS vulnerability: "
                    "nested quantifiers detected"
                )

        # Use multiprocessing for actual timeout enforcement
        # Note: _compile_and_test_regex is defined at module level to be picklable
        result_queue: MPQueue = MPQueue()

        process = Process(
            target=_compile_and_test_regex,
            args=(value, result_queue),
            daemon=True,
        )
        process.start()
        process.join(timeout=REDOS_TIMEOUT_SECONDS)

        if process.is_alive():
            process.terminate()  # Actually kills the process
            process.join(timeout=0.5)
            if process.is_alive():
                process.kill()  # Force kill if terminate didn't work
            raise ValueError("Regex compilation timed out (possible ReDoS pattern)")

        try:
            success, result = result_queue.get_nowait()
            if success:
                return str(result)  # result is the validated regex pattern
            raise ValueError(result)
        except Exception:
            raise ValueError("Regex validation failed unexpectedly") from None


# --- Data Structures for Parsing & Processing ---


@dataclass
class Declaration:
    """Represents a code declaration (function, class, variable, etc.).

    Attributes:
        kind: Type of declaration (e.g., 'function', 'class', 'method', 'variable')
        name: Name of the declaration
        start_line: Starting line number in the original file
        end_line: Ending line number in the original file
        modifiers: Set of modifiers (e.g., {'public', 'static', 'async'})
        docstring: Documentation string associated with the declaration
        signature: Function/method signature without the body
        children: List of nested declarations (for classes/functions with inner definitions)
        ai_summary: AI-generated summary for this declaration (if enabled)

    """

    kind: str
    name: str
    start_line: int
    end_line: int
    modifiers: set[str] = field(default_factory=set)
    docstring: str = ""
    signature: str = ""  # Function/method signature without body
    children: list[Declaration] = field(default_factory=list)
    ai_summary: str | None = None  # AI-generated summary for this declaration

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
    ai_summary: str | None = None  # AI-generated summary
    ai_metadata: dict[str, Any] | None = None  # Metadata about AI generation
    # Differential output fields
    diff_content: str | None = None  # Unified diff content
    diff_metadata: DiffMetadata | None = None  # Metadata about the diff


@dataclass
class ParseResult:
    """Represents the result of a parsing operation.

    Captures various outcomes and characteristics of the parse process.

    Attributes:
        declarations: A list of parsed declarations from the code.
        imports: A list of import statements found in the code.
        missed_features: A list of features not supported by the parser.
        security_issues: A list containing any discovered security issues.
        ast_root: Holds tree_sitter.Node if available.
        error: Describes any parsing errors encountered.
        engine_used: The parsing engine used, defaults to "regex".
        parser_quality: Indicates the quality of the parse as "full", "partial", or "basic".
        file_path: Path to the file being parsed.
        language: Language of the file being parsed.
        content: The content of the file being parsed.
        token_stats: Statistics about the tokens processed.
        module_docstring: The docstring of the module if available.
        module_name: The name of the module if available.
        degraded: Indicates whether the parsing was degraded.
        confidence_score: Confidence score (0.0-1.0) for result merger decisions.
        parser_type: Parser type used: "tree-sitter", "enhanced", or "standard".

    The result extensively uses optional fields to enhance flexibility,
    catering to both mandatory and discretionary parsing scenarios.

    """

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
    # New fields for intelligent result merging (Phase 0)
    confidence_score: float | None = None  # 0.0-1.0 confidence for merger decisions
    parser_type: str | None = None  # "tree-sitter", "enhanced", "standard"


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
        """Render the item as a list of strings for the text writer."""
        pass

    @abstractmethod
    def render_markdown_chunks(self, config: CodeConCatConfig) -> list[str]:
        """Render the item as a list of markdown string chunks."""
        pass

    @abstractmethod
    def render_json_dict(self, config: CodeConCatConfig) -> dict[str, Any]:
        """Render the item as a dictionary for the JSON writer."""
        pass

    @abstractmethod
    def render_xml_element(self, config: CodeConCatConfig) -> ET.Element:
        """Render the item as an XML element structure."""
        pass


@dataclass
class DiffMetadata:
    """Metadata for differential file changes between Git refs.

    Contains information about the nature and scope of changes
    to a file between two Git references.
    """

    from_ref: str  # Starting Git ref (branch, tag, or commit SHA)
    to_ref: str  # Ending Git ref (branch, tag, or commit SHA)
    change_type: str  # Type of change: 'added', 'modified', 'deleted', 'renamed'
    additions: int  # Number of lines added
    deletions: int  # Number of lines deleted
    binary: bool  # Whether the file is binary
    old_path: str | None = None  # Original path if renamed
    similarity: float | None = None  # Similarity percentage for renamed files


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
    summary: str = ""  # Human-readable summary
    ai_summary: str | None = None  # AI-generated detailed summary
    ai_metadata: dict | None = None  # AI metadata including meta-overview, tokens, cost, etc.

    # Structured analysis results (passed from ParsedFileData) - parameters with defaults
    declarations: list[Declaration] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    token_stats: TokenStats | None = None
    security_issues: list[SecurityIssue] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Differential output fields
    diff_content: str | None = None  # Unified diff content
    diff_metadata: DiffMetadata | None = None  # Metadata about the diff

    def render_text_lines(self, config: CodeConCatConfig) -> list[str]:
        """Render the annotated file as plain text lines.

        Args:
            config: Configuration for rendering options

        Returns:
            List of text lines representing the file

        """
        from codeconcat.writer.rendering_adapters import TextRenderAdapter

        return TextRenderAdapter.render_annotated_file(self, config)

    def render_markdown_chunks(self, config: CodeConCatConfig) -> list[str]:
        """Render the annotated file as Markdown chunks.

        Args:
            config: Configuration for rendering options

        Returns:
            List of Markdown-formatted text chunks

        """
        from codeconcat.writer.rendering_adapters import MarkdownRenderAdapter

        return MarkdownRenderAdapter.render_annotated_file(self, config)

    def render_json_dict(self, config: CodeConCatConfig) -> dict[str, Any]:
        """Render the annotated file as a JSON-serializable dictionary.

        Args:
            config: Configuration for rendering options

        Returns:
            Dictionary representation of the file data

        """
        from codeconcat.writer.rendering_adapters import JsonRenderAdapter

        return JsonRenderAdapter.annotated_file_to_dict(self, config)

    def render_xml_element(self, config: CodeConCatConfig) -> ET.Element:
        """Render the annotated file as an XML element.

        Args:
            config: Configuration for rendering options

        Returns:
            ET.Element containing the XML representation

        """
        from codeconcat.writer.rendering_adapters import XmlRenderAdapter

        return XmlRenderAdapter.create_annotated_file_element(self, config)


# New Parser Interface
class ParserInterface(ABC):
    """Abstract Base Class defining the interface for language parsers."""

    @abstractmethod
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
        """Render documentation file as plain text lines.

        Args:
            config: Configuration for rendering options.

        Returns:
            List of text lines representing the documentation.

        """
        from codeconcat.writer.rendering_adapters import TextRenderAdapter

        return TextRenderAdapter.render_doc_file(self, config)

    def render_markdown_chunks(self, config: CodeConCatConfig) -> list[str]:
        """Render documentation file as Markdown chunks.

        Args:
            config: Configuration for rendering options.

        Returns:
            List of Markdown-formatted text chunks.

        """
        from codeconcat.writer.rendering_adapters import MarkdownRenderAdapter

        return MarkdownRenderAdapter.render_doc_file(self, config)

    def render_json_dict(self, config: CodeConCatConfig) -> dict[str, Any]:
        """Render documentation file as a JSON-serializable dictionary.

        Args:
            config: Configuration for rendering options.

        Returns:
            Dictionary representation of the documentation data.

        """
        from codeconcat.writer.rendering_adapters import JsonRenderAdapter

        return JsonRenderAdapter.doc_file_to_dict(self, config)

    def render_xml_element(self, config: CodeConCatConfig) -> ET.Element:
        """Render documentation file as an XML element.

        Args:
            config: Configuration for rendering options.

        Returns:
            ET.Element containing the XML representation.

        """
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
        """Provide dictionary-like access with .get() method."""
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

    enable_result_merging: bool = Field(
        True,
        description="Enable intelligent result merging from multiple parsers instead of single-winner selection. "
        "Combines declarations from tree-sitter, enhanced, and standard parsers for maximum coverage.",
        validate_default=True,
    )

    merge_strategy: str = Field(
        "confidence",
        description="Strategy for merging parse results: 'confidence' (weight by confidence), "
        "'union' (combine all features), 'fast_fail' (first high-confidence wins), "
        "'best_of_breed' (pick best parser per feature type).",
        validate_default=True,
    )

    parser_early_termination: bool = Field(
        True,
        description="Enable early termination of parser fallback chain when tree-sitter succeeds. "
        "When True, skips enhanced and standard parsers if tree-sitter produces sufficient results. "
        "Set to False to always run all parsers for maximum coverage (slower).",
        validate_default=True,
    )

    parser_early_termination_threshold: int = Field(
        1,
        description="Minimum number of declarations tree-sitter must find to trigger early termination. "
        "Higher values ensure more thorough parsing at the cost of speed.",
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
    # Diff mode fields
    diff_from: str | None = Field(
        None,
        description="Starting Git ref for diff mode (branch, tag, or commit SHA).",
    )
    diff_to: str | None = Field(
        None,
        description="Ending Git ref for diff mode (branch, tag, or commit SHA).",
    )
    # Removed duplicate - using the one below with None
    exclude_languages: list[str] = Field(
        default_factory=list, description="List of language identifiers to exclude from processing"
    )
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
    extract_docs: bool = Field(
        False, description="Extract documentation files (Markdown, RST, etc.) alongside code"
    )
    show_skip: bool = Field(False, description="Print skipped files after processing")
    merge_docs: bool = Field(False, description="Merge documentation with code output")
    doc_extensions: list[str] = Field(
        default_factory=lambda: [".md", ".rst", ".txt", ".rmd"],
        description="File extensions to treat as documentation",
    )
    custom_extension_map: dict[str, str] = Field(
        default_factory=dict,
        description="Custom mapping of file extensions to language identifiers",
    )
    output: str = Field("", description="Output file path (auto-generated if empty)")
    format: str = Field(
        "markdown", description="Output format: 'markdown', 'json', 'xml', or 'text'"
    )

    @field_validator("format", mode="before")
    @classmethod
    def _validate_format(cls, value: str | None) -> str:
        """Validate and normalize output format against VALID_FORMATS."""
        if value is None or str(value).strip() == "":
            return "markdown"
        normalised = str(value).strip().lower()
        if normalised not in VALID_FORMATS:
            allowed = ", ".join(sorted(VALID_FORMATS))
            raise ValueError(f"Invalid output format '{value}'. Must be one of: {allowed}.")
        return normalised

    xml_processing_instructions: bool = Field(
        False, description="Include AI processing instructions in XML output"
    )
    max_workers: int = Field(
        4, description="Maximum number of worker threads for parallel processing"
    )
    disable_tree: bool = Field(False, description="Disable directory tree visualization in output")
    disable_copy: bool = Field(False, description="Disable automatic clipboard copy of output")
    disable_annotations: bool = Field(False, description="Disable AI annotations in output")
    disable_symbols: bool = Field(False, description="Disable symbol extraction and listing")
    disable_ai_context: bool = Field(False, description="Disable AI context generation for output")
    include_file_summary: bool = Field(True, description="Include file summary section in output")
    include_directory_structure: bool = Field(
        True, description="Include directory structure in output"
    )
    remove_comments: bool = Field(False, description="Remove comments from code in output")
    remove_empty_lines: bool = Field(False, description="Remove empty lines from code in output")
    remove_docstrings: bool = Field(False, description="Remove docstrings from code in output")
    show_line_numbers: bool = Field(False, description="Include line numbers in code output")
    enable_token_counting: bool = Field(
        False, description="Enable token counting for AI processing"
    )
    enable_security_scanning: bool = Field(
        True, description="Enable security scanning for code patterns"
    )
    security_scan_severity_threshold: str = Field(
        "MEDIUM", description="Minimum severity level to report (INFO, LOW, MEDIUM, HIGH, CRITICAL)"
    )
    security_ignore_paths: list[str] = Field(
        default_factory=list,
        description="Glob patterns for files/directories to skip during security scanning",
    )
    security_ignore_patterns: list[str] = Field(
        default_factory=list, description="Regex patterns for security findings content to ignore"
    )
    security_custom_patterns: list[CustomSecurityPattern] = Field(
        default_factory=list, description="User-defined custom security patterns for scanning"
    )

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
    sort_files: bool = Field(False, description="Sort files alphabetically in output")

    # Advanced options
    # max_workers already defined above on line 543
    split_output: int = Field(
        1, description="Number of files to split output into for large codebases"
    )
    verbose: int = Field(0, description="Verbosity level for logging (0=quiet, 1=info, 2+=debug)")
    quiet: bool = Field(False, description="Suppress all non-error output for API usage")

    # Markdown cross-linking
    cross_link_symbols: bool = Field(
        False,
        description="Enable cross-linking between symbol summaries and their definitions in output",
    )

    # Progress Bar
    disable_progress_bar: bool = Field(False, description="Disable progress bars during processing")

    # New Output Structure/Verbosity Controls
    output_preset: str | None = Field(
        "medium",
        description="Output preset: 'lean' (minimal), 'medium' (balanced), or 'full' (complete)",
    )
    include_repo_overview: bool = Field(
        True, description="Include repository overview section in output"
    )
    include_file_index: bool = Field(True, description="Include file index section in output")
    # include_file_summary already defined above on line 549
    include_declarations_in_summary: bool = Field(
        True, description="Include function/class declarations in file summaries"
    )
    include_imports_in_summary: bool = Field(
        False,
        description="Include import statements in file summaries (disabled by default to reduce verbosity)",
    )
    include_tokens_in_summary: bool = Field(
        True, description="Include token counts in file summaries"
    )
    include_security_in_summary: bool = Field(
        True, description="Include security issues in file summaries"
    )

    # use_default_excludes already defined above on line 529
    # New flag for output masking
    mask_output_content: bool = Field(
        False,
        description="Mask sensitive data (secrets, API keys, etc.) directly in the file content within the output. "
        "This flag affects the actual code/content displayed, not just metadata. "
        "Different from redact_paths which only affects file path display. "
        "Requires security scanning to be enabled.",
    )

    # Redact absolute paths in outputs/logs to avoid leaking local usernames and directories
    redact_paths: bool = Field(
        False,
        description="Redact absolute filesystem paths in generated outputs and logs (replaces with relative or placeholder paths). "
        "This flag affects file paths in output structure/metadata but not file content itself.",
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

    # --- AI Summarization Options ---
    enable_ai_summary: bool = Field(
        False, description="Enable AI-powered code summarization (requires API key)."
    )
    ai_provider: str = Field(
        "openai",
        description=(
            "AI provider to use: openai, anthropic, openrouter, ollama, local_server, "
            "vllm, lmstudio, llamacpp_server, llamacpp (deprecated)"
        ),
    )
    ai_api_key: str | None = Field(
        None, description="API key for the AI provider (can also use environment variables)"
    )
    ai_api_base: str | None = Field(
        None,
        description="Override API base URL for the selected AI provider (useful for local servers)",
    )
    ai_model: str | None = Field(
        None,
        description="Specific model to use (provider-dependent, e.g., 'gpt-3.5-turbo', 'claude-3-haiku')",
    )
    ai_temperature: float = Field(
        0.3, description="Temperature for AI generation (0.0-1.0, lower is more deterministic)"
    )
    ai_max_tokens: int = Field(500, description="Maximum tokens for AI summaries")
    ai_cache_enabled: bool = Field(
        True, description="Cache AI summaries to avoid redundant API calls"
    )
    ai_summarize_functions: bool = Field(
        False, description="Generate summaries for individual functions/methods"
    )
    ai_min_file_lines: int = Field(
        5, description="Minimum file size (in lines) to trigger summarization"
    )
    ai_min_function_lines: int = Field(
        10, description="Minimum function size (in lines) to trigger summarization"
    )
    ai_max_functions_per_file: int = Field(
        10, description="Maximum number of functions to summarize per file"
    )
    ai_max_content_chars: int = Field(
        50000, description="Maximum characters of content to send to AI (truncate if larger)"
    )
    ai_max_concurrent: int = Field(5, description="Maximum concurrent AI API requests")
    ai_include_languages: list[str] | None = Field(
        None, description="Only summarize these languages (None means all)"
    )
    ai_exclude_languages: list[str] = Field(
        default_factory=list, description="Languages to exclude from summarization"
    )
    ai_exclude_patterns: list[str] = Field(
        default_factory=lambda: ["*test*", "*spec*", "*mock*"],
        description="File path patterns to exclude from summarization",
    )

    # Meta-overview configuration
    ai_meta_overview: bool = Field(
        False, description="Enable meta-overview generation from all file summaries"
    )
    ai_meta_overview_prompt: str | None = Field(
        None,
        description="Custom prompt for meta-overview generation. If None, uses default prompt.",
    )
    ai_meta_overview_max_tokens: int = Field(
        8000,
        description="Maximum tokens for meta-overview generation (completion tokens for reasoning models)",
    )
    ai_meta_overview_position: str = Field(
        "top",
        description="Position of meta-overview in output ('top' or 'bottom')",
        pattern="^(top|bottom)$",
    )
    ai_meta_overview_model: str | None = Field(
        None,
        description="Optional model override for meta-overview generation. If None, uses higher-tier model based on provider.",
    )
    ai_meta_overview_use_higher_tier: bool = Field(
        True,
        description="Use higher-tier models for meta-overview generation (claude-sonnet-4-5, gpt-5, gemini-2.5-pro)",
    )
    ai_save_summaries: bool = Field(
        False,
        description="Save individual summaries and meta-overview to separate files on disk",
    )
    ai_summaries_dir: str = Field(
        "codeconcat_summaries",
        description="Directory for saving AI summaries (relative to output or absolute path)",
    )
    ai_timeout: int = Field(
        600,
        description="Timeout in seconds for AI operations (default: 600 = 10 minutes)",
    )

    # --- Local LLM Performance Options (llama.cpp) ---
    llama_gpu_layers: int | None = Field(
        None,
        description="Number of layers to offload to GPU for llama.cpp (0=CPU only, None=auto)",
    )
    llama_context_size: int | None = Field(
        None,
        description="Context window size for llama.cpp (default: 2048)",
    )
    llama_threads: int | None = Field(
        None,
        description="Number of CPU threads for llama.cpp inference",
    )
    llama_batch_size: int | None = Field(
        None,
        description="Batch size for llama.cpp prompt processing",
    )

    # --- Report Generation Options ---
    write_test_security_report: bool = Field(
        False,
        description="Write test file security findings to a separate report file",
    )
    write_unsupported_report: bool = Field(
        False,
        description="Write unsupported/skipped files report to a JSON file",
    )
