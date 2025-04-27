"""
base_types.py

Holds data classes and typed structures used throughout CodeConCat.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

# Rename this file to base_types.py to avoid conflict with Python's types module
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator, validator

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
                return NotImplemented  # Handle cases where a value might not be in the defined order
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
            raise ValueError(
                f"Invalid severity '{value}'. Must be one of: {valid_severities}"
            )

    @field_validator("regex")
    def validate_regex(cls, value):
        try:
            # Accept special characters by default; just ensure it's a valid regex
            re.compile(value)
            return value
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")


# --- Core Data Types ---


# Abstract Base Class for Writable Items
class WritableItem(ABC):
    """Abstract base class for items that can be rendered by different writers."""

    @property
    @abstractmethod
    def file_path(self) -> str:
        """The path to the source file."""
        pass

    @abstractmethod
    def render_text_lines(self, config: "CodeConCatConfig") -> List[str]:
        """Renders the item as a list of strings for the text writer."""
        pass

    @abstractmethod
    def render_markdown_chunks(self, config: "CodeConCatConfig") -> List[str]:
        """Renders the item as a list of markdown string chunks."""
        pass

    @abstractmethod
    def render_json_dict(self, config: "CodeConCatConfig") -> Dict[str, Any]:
        """Renders the item as a dictionary for the JSON writer."""
        pass

    @abstractmethod
    def render_xml_element(self, config: "CodeConCatConfig") -> ET.Element:
        """Renders the item as an XML element structure."""
        pass


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
    imports: List[str] = field(default_factory=list)
    token_stats: Optional[TokenStats] = None
    security_issues: List[SecurityIssue] = field(default_factory=list)


@dataclass
class AnnotatedFileData(WritableItem):
    """Data structure for annotated file content, including structured analysis results."""

    # Core file info
    file_path: str
    language: str
    content: str  # Original content
    annotated_content: str  # Potentially processed content (e.g., comments removed)

    # Structured analysis results (passed from ParsedFileData)
    declarations: List[Declaration] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    token_stats: Optional[TokenStats] = None
    security_issues: List[SecurityIssue] = field(default_factory=list)

    # Optional AI-generated additions
    summary: Optional[str] = None  # AI-generated overall summary
    tags: List[str] = field(default_factory=list)

    # Implement WritableItem properties and methods
    @property
    def file_path(self) -> str:
        # Dataclasses allow direct field access to satisfy property
        return self.__dict__["file_path"]

    def render_text_lines(self, config: "CodeConCatConfig") -> List[str]:
        lines = []
        lines.append(
            f"Language: {self.language}" if self.language else "Language: Unknown"
        )

        # Summary
        if config.include_file_summary and self.summary:
            lines.append("\n## Summary:")
            lines.append(self.summary)

        # Declarations
        if config.include_declarations_in_summary and self.declarations:
            lines.append("\n## Declarations:")
            for decl in self.declarations:
                lines.append(
                    f"  - {decl.kind}: {decl.name} (Lines: {decl.start_line}-{decl.end_line})"
                )

        # Imports
        if config.include_imports_in_summary and self.imports:
            lines.append("\n## Imports:")
            for imp in sorted(self.imports):
                lines.append(f"  - {imp}")

        # Token Stats
        if config.include_tokens_in_summary and self.token_stats:
            lines.append("\n## Token Stats:")
            lines.append(f"  - Input Tokens: {self.token_stats.input_tokens}")
            lines.append(f"  - Output Tokens: {self.token_stats.output_tokens}")
            lines.append(f"  - Total Tokens: {self.token_stats.total_tokens}")

        # Security Issues
        if config.include_security_in_summary and self.security_issues:
            lines.append("\n## Security Issues:")
            for issue in self.security_issues:
                severity_val = (
                    issue.severity.value
                    if hasattr(issue.severity, "value")
                    else str(issue.severity)
                )
                lines.append(
                    f"  - Severity: {severity_val}, Line: {issue.line_number}, Description: {issue.description}"
                )

        # Tags
        if self.tags:
            lines.append("\n## Tags:")
            lines.append(f"  - {', '.join(sorted(self.tags))}")

        # Content (Use annotated_content if available and not disabled, else content)
        # TODO: Add config flag specifically for using annotated_content vs raw content?
        content_to_use = (
            self.annotated_content if self.annotated_content else self.content
        )
        if config.include_code_content and content_to_use:
            lines.append("\n## Content:")
            lines.append(content_to_use)

        return lines

    def render_markdown_chunks(self, config: "CodeConCatConfig") -> List[str]:
        chunks = []
        # Use annotated_content preferentially if it exists
        content_to_render = (
            self.annotated_content if self.annotated_content else self.content
        )
        lang_hint = self.language.lower() if self.language else ""

        if config.include_code_content and content_to_render:
            chunks.append(f"```{lang_hint}\n{content_to_render}\n```\n\n")

        # Placeholder for other sections like declarations, imports, etc. if added later
        # Example:
        # if config.include_declarations_in_summary and self.declarations:
        #    chunks.append("**Declarations:**\n")
        #    for decl in self.declarations:
        #        chunks.append(f"- `{decl.name}` ({decl.kind})\n")

        return chunks

    def render_json_dict(self, config: "CodeConCatConfig") -> Dict[str, Any]:
        entry = {"type": "code"}  # Always include type
        entry["file_path"] = self.file_path  # Always include file_path

        if self.language:
            entry["language"] = self.language

        # Use annotated_content if available, else raw content
        content_to_use = (
            self.annotated_content if self.annotated_content else self.content
        )
        if config.include_code_content and content_to_use:
            entry["content"] = content_to_use  # Decide which content field to use

        if config.include_file_summary and self.summary:
            entry["summary"] = self.summary

        if config.include_declarations_in_summary and self.declarations:
            entry["declarations"] = [decl.model_dump() for decl in self.declarations]

        if config.include_imports_in_summary and self.imports:
            entry["imports"] = sorted(self.imports)

        if config.include_tokens_in_summary and self.token_stats:
            entry["token_stats"] = self.token_stats.model_dump()

        if config.include_security_in_summary and self.security_issues:
            entry["security_issues"] = [
                issue.model_dump() for issue in self.security_issues
            ]

        if self.tags:
            entry["tags"] = list(self.tags)  # Convert set to list

        return entry

    def render_xml_element(self, config: "CodeConCatConfig") -> ET.Element:
        file_elem = ET.Element("file")
        ET.SubElement(file_elem, "path").text = self.file_path
        if self.language:
            ET.SubElement(file_elem, "language").text = self.language

        # Content (use annotated preferentially, wrap in CDATA)
        content_to_use = (
            self.annotated_content if self.annotated_content else self.content
        )
        if config.include_code_content and content_to_use:
            content_elem = ET.SubElement(file_elem, "content")
            content_elem.text = f"<![CDATA[{content_to_use}]]>"

        # Summary (wrap in CDATA)
        if config.include_file_summary and self.summary:
            summary_elem = ET.SubElement(file_elem, "summary")
            summary_elem.text = f"<![CDATA[{self.summary}]]>"

        # Declarations
        if config.include_declarations_in_summary and self.declarations:
            decls_elem = ET.SubElement(file_elem, "declarations")
            for decl in self.declarations:
                ET.SubElement(
                    decls_elem,
                    "declaration",
                    kind=decl.kind,
                    name=decl.name,
                    start_line=str(decl.start_line),
                    end_line=str(decl.end_line),
                )

        # Imports
        if config.include_imports_in_summary and self.imports:
            imports_elem = ET.SubElement(file_elem, "imports")
            for imp in sorted(self.imports):
                ET.SubElement(imports_elem, "import", name=imp)

        # Token Stats
        if config.include_tokens_in_summary and self.token_stats:
            stats_elem = ET.SubElement(file_elem, "token_stats")
            ET.SubElement(stats_elem, "input_tokens").text = str(
                self.token_stats.input_tokens
            )
            ET.SubElement(stats_elem, "output_tokens").text = str(
                self.token_stats.output_tokens
            )
            ET.SubElement(stats_elem, "total_tokens").text = str(
                self.token_stats.total_tokens
            )

        # Security Issues (wrap description in CDATA)
        if config.include_security_in_summary and self.security_issues:
            sec_issues_elem = ET.SubElement(file_elem, "security_issues")
            for issue in self.security_issues:
                severity_val = (
                    issue.severity.value
                    if hasattr(issue.severity, "value")
                    else str(issue.severity)
                )
                issue_elem = ET.SubElement(
                    sec_issues_elem,
                    "issue",
                    severity=severity_val,
                    line=str(issue.line_number),
                )
                desc_elem = ET.SubElement(issue_elem, "description")
                desc_elem.text = f"<![CDATA[{issue.description}]]>"

        # Tags
        if self.tags:
            tags_elem = ET.SubElement(file_elem, "tags")
            for tag in sorted(self.tags):
                ET.SubElement(tags_elem, "tag", name=tag)

        return file_elem


@dataclass
class ParsedDocData(WritableItem):
    """Data structure for parsed documentation content."""

    file_path: str
    doc_type: str
    content: str

    # Implement WritableItem properties and methods
    @property
    def file_path(self) -> str:
        return self.__dict__["file_path"]

    def render_text_lines(self, config: "CodeConCatConfig") -> List[str]:
        lines = []
        if self.doc_type:
            lines.append(f"Type: {self.doc_type}")
        if config.include_doc_content and self.content:
            lines.append("\n## Content:")
            lines.append(self.content)
        return lines

    def render_markdown_chunks(self, config: "CodeConCatConfig") -> List[str]:
        chunks = []
        if config.include_doc_content and self.content:
            # Use 'markdown' hint for docs, could refine if doc_type gives better hints
            chunks.append(f"```markdown\n{self.content}\n```\n\n")
        return chunks

    def render_json_dict(self, config: "CodeConCatConfig") -> Dict[str, Any]:
        entry = {"type": "documentation"}
        entry["file_path"] = self.file_path

        if self.doc_type:
            entry["doc_type"] = self.doc_type

        if config.include_doc_content and self.content:
            entry["content"] = self.content

        return entry

    def render_xml_element(self, config: "CodeConCatConfig") -> ET.Element:
        doc_elem = ET.Element("doc")
        ET.SubElement(doc_elem, "path").text = self.file_path
        if self.doc_type:
            ET.SubElement(doc_elem, "doc_type").text = self.doc_type

        # Content (wrap in CDATA)
        if config.include_doc_content and self.content:
            content_elem = ET.SubElement(doc_elem, "content")
            content_elem.text = f"<![CDATA[{self.content}]]>"

        return doc_elem


@dataclass
class ParseResult:
    """Result of parsing a code file."""

    file_path: str
    language: str
    content: str
    declarations: List[Declaration]
    imports: List[str]  # Add imports field
    token_stats: Optional[TokenStats] = None
    security_issues: List[SecurityIssue] = field(default_factory=list)

    # For backward compatibility with code that expects (declarations, imports) tuple
    def __getitem__(self, key):
        """Enable subscripting like result[0] and result[1]"""
        if key == 0:
            return self.declarations
        elif key == 1:
            return self.imports
        else:
            raise IndexError(f"ParseResult index {key} out of range")

    def __iter__(self):
        """Enable iteration and unpacking like 'declarations, imports = result'"""
        yield self.declarations
        yield self.imports

    def __len__(self):
        """Return length for compatibility"""
        return 2  # Always 2 items (declarations, imports) for backwards compatibility


# Pydantic model for Global Configuration
class CodeConCatConfig(BaseModel):
    """Global configuration object using Pydantic for validation.

    Merged from CLI args + .codeconcat.yml.
    Fields are validated upon instantiation.
    """

    # For backward compatibility with code that treats this like a dictionary
    def get(self, key: str, default=None):
        """Provide dictionary-like access with .get() method"""
        return getattr(self, key, default)

    target_path: str = "."
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    github_ref: Optional[str] = None
    include_languages: List[str] = Field(default_factory=list)
    exclude_languages: List[str] = Field(default_factory=list)
    include_paths: Optional[List[str]] = Field(
        None, description="Patterns for files/directories to include."
    )
    exclude_paths: Optional[List[str]] = Field(
        None, description="Patterns for files/directories to exclude."
    )
    use_gitignore: bool = Field(
        True, description="Whether to respect rules found in .gitignore files."
    )
    use_default_excludes: bool = Field(
        True, description="Whether to use the built-in default exclude patterns."
    )
    include_languages: Optional[List[str]] = Field(
        None, description="Specific languages to include (by identifier)."
    )
    exclude_languages: List[str] = Field(default_factory=list)
    extract_docs: bool = False
    show_skip: bool = False  # Whether to print skipped files after parsing
    merge_docs: bool = False
    doc_extensions: List[str] = Field(
        default_factory=lambda: [".md", ".rst", ".txt", ".rmd"]
    )
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
    verbose: bool = False  # Added for verbose logging control

    # Markdown cross-linking
    cross_link_symbols: bool = (
        False  # Option to cross-link symbol summaries and definitions
    )

    # Progress Bar
    disable_progress_bar: bool = False  # Disable tqdm progress bars

    # New Output Structure/Verbosity Controls
    output_preset: Optional[str] = "medium"  # 'lean', 'medium', 'full', or None
    include_repo_overview: bool = True  # Default based on 'medium'
    include_file_index: bool = True  # Default based on 'medium'
    include_file_summary: bool = True  # Default based on 'medium'
    include_declarations_in_summary: bool = True  # Default based on 'medium'
    include_imports_in_summary: bool = (
        False  # Default based on 'medium' (maybe imports are too verbose?)
    )
    include_tokens_in_summary: bool = True  # Default based on 'medium'
    include_security_in_summary: bool = True  # Default based on 'medium'

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

    @validator("output_preset", pre=True, always=True)
    def validate_output_preset(cls, v):
        if v is None or isinstance(v, str) and v.lower() in ["lean", "medium", "full"]:
            return v.lower() if isinstance(v, str) else v
        raise ValueError(
            "output_preset must be one of 'lean', 'medium', 'full', or None"
        )

    @field_validator("split_output")
    def check_split_output(cls, v):
        if v < 1:
            raise ValueError("split_output must be an integer greater than 0.")
        return v

    class Config:
        extra = "ignore"  # Ignore extra fields from config file/CLI
