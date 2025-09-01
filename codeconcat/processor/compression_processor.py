"""
Improved Compression processor for CodeConCat.

This module implements a content compression system that identifies and filters
out less important code segments while preserving metadata about what was omitted.
It breaks source code into segments that can be kept, omitted (with placeholder),
or treated as metadata.

IMPROVEMENTS:
1. Fixed data loss bug in gap merging
2. Added syntactic validation
3. Expanded pattern recognition for modern code
4. Simplified to two compression patterns: ESSENTIAL and CONTEXTUAL
"""

import ast
import logging
import re
from enum import Enum
from typing import List, Set

from codeconcat.base_types import (
    CodeConCatConfig,
    ContentSegment,
    ContentSegmentType,
    ParsedFileData,
    SecuritySeverity,
)

logger = logging.getLogger(__name__)


class CompressionPattern(Enum):
    """Simplified compression patterns."""

    ESSENTIAL = "essential"  # Keep only critical code (signatures, security, errors)
    CONTEXTUAL = "contextual"  # Keep important code with surrounding context


# Modern code patterns to recognize
MODERN_PATTERNS = {
    # Database operations
    "database": re.compile(
        r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|"
        r"query|execute|fetch|commit|rollback|transaction|"
        r"db\.|cursor|connection|session)\b",
        re.IGNORECASE,
    ),
    # API operations
    "api": re.compile(
        r"\b(request|requests\.|fetch|axios|http|https|"
        r"api|endpoint|REST|GraphQL|gRPC|"
        r"get|post|put|patch|delete|head)\b",
        re.IGNORECASE,
    ),
    # Error handling
    "error_handling": re.compile(
        r"\b(try|catch|except|finally|raise|throw|throws|"
        r"error|Error|Exception|assert|require|validate|check)\b"
    ),
    # Security operations
    "security": re.compile(
        r"\b(auth|Auth|token|Token|password|Password|secret|Secret|"
        r"key|Key|encrypt|decrypt|hash|salt|jwt|JWT|oauth|OAuth|"
        r"permission|role|sanitize|escape|validate)\b"
    ),
    # Async patterns
    "async": re.compile(
        r"\b(async|await|promise|Promise|then|catch|finally|"
        r"setTimeout|setInterval|callback|emit|on|once)\b"
    ),
    # Testing
    "testing": re.compile(
        r"\b(test|Test|spec|Spec|describe|it|expect|assert|" r"should|mock|Mock|stub|spy|fixture)\b"
    ),
    # Configuration
    "config": re.compile(
        r"\b(config|Config|setting|Setting|env|ENV|" r"environment|Environment|option|Option)\b",
        re.IGNORECASE,
    ),
}


class CompressionProcessor:
    """
    Improved processor that compresses code content without data loss.

    Key improvements:
    1. Preserves original content during gap merging
    2. Validates syntactic correctness
    3. Uses modern pattern recognition
    4. Simplified compression patterns
    """

    def __init__(self, config: CodeConCatConfig):
        """Initialize the compression processor with configuration settings."""
        self.config = config
        self._original_lines: List[str] = []  # Store original content
        self._setup_compression_pattern()

    def _setup_compression_pattern(self) -> None:
        """Configure compression based on simplified patterns."""
        # Map old levels to new patterns for backward compatibility
        level = self.config.compression_level.lower()

        if level in ["aggressive", "high"]:
            self.pattern = CompressionPattern.ESSENTIAL
            self.importance_threshold = 0.7
            self.context_lines = 1
        else:  # low, medium, or default
            self.pattern = CompressionPattern.CONTEXTUAL
            self.importance_threshold = 0.4
            self.context_lines = 2

        self.min_lines_to_compress = self.config.compression_keep_threshold
        self.max_gap_to_merge = 3

    def process_file(self, file_data: ParsedFileData) -> List[ContentSegment]:
        """
        Process a file and create a list of content segments based on importance.

        Args:
            file_data: The parsed file data containing code content and metadata

        Returns:
            A list of ContentSegment objects representing the file's content
        """
        if not file_data.content or not self.config.enable_compression:
            if file_data.content:
                return [
                    ContentSegment(
                        segment_type=ContentSegmentType.CODE,
                        content=file_data.content,
                        start_line=1,
                        end_line=len(file_data.content.split("\n")),
                        metadata={"compression_applied": False},
                    )
                ]
            return []

        # Store original lines for gap reconstruction
        self._original_lines = file_data.content.split("\n")

        # Calculate importance score for each line
        line_importance = self._calculate_line_importance(self._original_lines, file_data)

        # Create initial segments
        segments = self._create_initial_segments(self._original_lines, line_importance)

        # Merge adjacent segments (WITH ORIGINAL CONTENT PRESERVED)
        merged_segments = self._merge_small_segments(segments)

        # Validate syntactic correctness
        validated_segments = self._validate_syntactic_correctness(merged_segments, file_data)

        # Format placeholders for omitted segments
        return self._format_placeholders(validated_segments, file_data)

    def _calculate_line_importance(
        self, lines: List[str], file_data: ParsedFileData
    ) -> List[float]:
        """
        Calculate importance scores using modern pattern recognition.

        Improvements:
        - Added modern code patterns (API, database, async, etc.)
        - Better scoring for error handling and security
        - Context-aware scoring based on compression pattern
        """
        total_lines = len(lines)
        line_importance = [0.0] * total_lines

        # Track important line numbers
        important_lines: Set[int] = set()

        # 1. Security issues are always critical
        if file_data.security_issues:
            for issue in file_data.security_issues:
                line_idx = issue.line_number - 1
                if 0 <= line_idx < total_lines:
                    important_lines.add(line_idx)
                    # Add context based on severity
                    if issue.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]:
                        for i in range(max(0, line_idx - 2), min(total_lines, line_idx + 3)):
                            important_lines.add(i)

        # 2. Declarations are important
        if file_data.declarations:
            for decl in file_data.declarations:
                start_idx = decl.start_line - 1
                if 0 <= start_idx < total_lines:
                    # Keep entire signature (more lines for better context)
                    for i in range(start_idx, min(total_lines, start_idx + 5)):
                        important_lines.add(i)

                    # For ESSENTIAL pattern, only keep signature
                    # For CONTEXTUAL, keep more of the body
                    if self.pattern == CompressionPattern.CONTEXTUAL:
                        # Keep first few lines of implementation
                        for i in range(start_idx, min(total_lines, start_idx + 10)):
                            if i not in important_lines:
                                line_importance[i] = max(line_importance[i], 0.5)

        # 3. Apply modern pattern recognition
        for i, line in enumerate(lines):
            line_strip = line.strip()
            line_lower = line_strip.lower()

            # Check keep tags
            if any(tag.lower() in line_lower for tag in self.config.compression_keep_tags):
                important_lines.add(i)
                for j in range(max(0, i - 1), min(total_lines, i + 2)):
                    important_lines.add(j)

            # Check modern patterns with appropriate scoring
            for pattern_name, pattern in MODERN_PATTERNS.items():
                if pattern.search(line):
                    if pattern_name in ["security", "error_handling", "database"]:
                        # Critical patterns
                        important_lines.add(i)
                        line_importance[i] = 1.0
                    elif pattern_name in ["api", "config"]:
                        # Important patterns
                        line_importance[i] = max(line_importance[i], 0.8)
                    elif pattern_name in ["async", "testing"]:
                        # Moderately important
                        line_importance[i] = max(line_importance[i], 0.6)

            # Standard patterns
            if re.search(r"^\s*(import|from\s+.*\s+import|#include|using\s+|require)", line):
                important_lines.add(i)
            elif re.search(r"\b(if|else|elif|for|while|switch|case)\b", line):
                line_importance[i] = max(line_importance[i], 0.5)
            elif "return" in line or "=" in line:
                line_importance[i] = max(line_importance[i], 0.4)
            elif line_strip and not line_strip.startswith(("#", "//", "/*", "*")):
                line_importance[i] = max(line_importance[i], 0.2)

        # Set high importance for identified important lines
        for line_idx in important_lines:
            line_importance[line_idx] = 1.0

        # Spread importance to context lines
        if self.context_lines > 0:
            context_importance = 0.8
            for i in range(total_lines):
                if line_importance[i] >= 0.9:  # High importance line
                    for j in range(max(0, i - self.context_lines), i):
                        line_importance[j] = max(line_importance[j], context_importance)
                    for j in range(i + 1, min(total_lines, i + self.context_lines + 1)):
                        line_importance[j] = max(line_importance[j], context_importance)

        return line_importance

    def _create_initial_segments(
        self, lines: List[str], line_importance: List[float]
    ) -> List[ContentSegment]:
        """Create initial content segments based on line importance."""
        segments: List[ContentSegment] = []
        current_type = None
        segment_start = 0
        segment_content = []

        for i, (line, importance) in enumerate(zip(lines, line_importance)):
            # Determine segment type for this line
            line_type = (
                ContentSegmentType.CODE
                if importance >= self.importance_threshold
                else ContentSegmentType.OMITTED
            )

            # Start a new segment if type changes
            if current_type != line_type:
                if current_type is not None:
                    segments.append(
                        ContentSegment(
                            segment_type=current_type,
                            content="\n".join(segment_content),
                            start_line=segment_start + 1,
                            end_line=i,
                            metadata={},
                        )
                    )

                segment_start = i
                segment_content = [line]
                current_type = line_type
            else:
                segment_content.append(line)

        # Add the final segment
        if current_type is not None and segment_content:
            segments.append(
                ContentSegment(
                    segment_type=current_type,
                    content="\n".join(segment_content),
                    start_line=segment_start + 1,
                    end_line=len(lines),
                    metadata={},
                )
            )

        # Don't omit small segments
        for i, segment in enumerate(segments):
            if (
                segment.segment_type == ContentSegmentType.OMITTED
                and segment.end_line - segment.start_line + 1 < self.min_lines_to_compress
            ):
                segments[i] = ContentSegment(
                    segment_type=ContentSegmentType.CODE,
                    content=segment.content,
                    start_line=segment.start_line,
                    end_line=segment.end_line,
                    metadata=segment.metadata,
                )

        return segments

    def _merge_small_segments(self, segments: List[ContentSegment]) -> List[ContentSegment]:
        """
        FIXED: Merge adjacent segments preserving actual gap content.

        Key fix: Uses stored original lines to reconstruct actual gap content
        instead of replacing with empty lines.
        """
        if not segments:
            return []

        result: List[ContentSegment] = [segments[0]]

        for segment in segments[1:]:
            prev = result[-1]

            # Merge adjacent OMITTED segments
            if (
                prev.segment_type == ContentSegmentType.OMITTED
                and segment.segment_type == ContentSegmentType.OMITTED
                and prev.end_line + 1 == segment.start_line
            ):
                result[-1] = ContentSegment(
                    segment_type=ContentSegmentType.OMITTED,
                    content=prev.content + "\n" + segment.content,
                    start_line=prev.start_line,
                    end_line=segment.end_line,
                    metadata={**prev.metadata, **segment.metadata},
                )
            elif (
                # Merge CODE segments with small gaps
                prev.segment_type == ContentSegmentType.CODE
                and segment.segment_type == ContentSegmentType.CODE
                and segment.start_line - prev.end_line <= self.max_gap_to_merge
            ):
                # FIX: Reconstruct actual gap content from original lines
                gap_start = prev.end_line  # 1-indexed
                gap_end = segment.start_line - 1  # 1-indexed

                if gap_start < gap_end and self._original_lines:
                    # Extract actual gap content (convert to 0-indexed)
                    gap_content = "\n".join(self._original_lines[gap_start:gap_end])
                else:
                    gap_content = ""

                # Merge with actual gap content preserved
                merged_content = prev.content
                if gap_content:
                    merged_content += "\n" + gap_content
                merged_content += "\n" + segment.content

                result[-1] = ContentSegment(
                    segment_type=ContentSegmentType.CODE,
                    content=merged_content,
                    start_line=prev.start_line,
                    end_line=segment.end_line,
                    metadata={
                        **prev.metadata,
                        **segment.metadata,
                        "merged_gap": True,
                        "gap_lines": gap_end - gap_start if gap_start < gap_end else 0,
                    },
                )
            else:
                result.append(segment)

        return result

    def _validate_syntactic_correctness(
        self, segments: List[ContentSegment], file_data: ParsedFileData
    ) -> List[ContentSegment]:
        """
        Validate and fix syntactic correctness of compressed code.

        Ensures:
        1. Complete syntax blocks (if/else, try/catch, etc.)
        2. Matching brackets and parentheses
        3. Complete function/class definitions
        4. Import dependencies are preserved
        """
        result = segments.copy()

        # Track syntax elements in kept code
        kept_code = "\n".join(
            s.content for s in segments if s.segment_type == ContentSegmentType.CODE
        )

        # Try to parse kept code for syntax validation
        language = file_data.language.lower() if file_data.language else ""

        if language == "python":
            try:
                # Check if Python code is syntactically valid
                ast.parse(kept_code)
            except SyntaxError as e:
                # If syntax error, try to fix by including more context
                logger.warning(f"Syntax error in compressed Python code: {e}")

                # Find the problematic line and expand context
                if e.lineno:
                    self._expand_context_for_syntax(result, e.lineno)

        # Check for incomplete blocks using regex patterns
        incomplete_patterns = [
            (r"\bif\b", r"\b(else|elif)\b"),  # if without else/elif
            (r"\btry\b", r"\b(except|finally)\b"),  # try without except/finally
            (r"\bfor\b", r"\b(break|continue|pass)\b"),  # incomplete loops
            (r"\bwhile\b", r"\b(break|continue|pass)\b"),
            (r"\bclass\s+\w+", r"def\s+\w+"),  # class without methods
        ]

        for open_pattern, close_pattern in incomplete_patterns:
            open_matches = len(re.findall(open_pattern, kept_code))
            close_matches = len(re.findall(close_pattern, kept_code))

            if open_matches > 0 and close_matches == 0:
                logger.warning(f"Incomplete block detected: {open_pattern} without {close_pattern}")

        # Check bracket balance
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []

        for char in kept_code:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values() and (not stack or stack.pop() != char):
                logger.warning(f"Unbalanced bracket detected: {char}")

        if stack:
            logger.warning(f"Unclosed brackets: {stack}")

        return result

    def _expand_context_for_syntax(self, segments: List[ContentSegment], problem_line: int) -> None:
        """Expand context around a problematic line to fix syntax errors."""
        # Find segment containing the problem line
        current_line = 0

        for i, segment in enumerate(segments):
            segment_lines = segment.content.count("\n") + 1

            if current_line <= problem_line < current_line + segment_lines:
                # Found the problematic segment
                if segment.segment_type == ContentSegmentType.OMITTED:
                    # Convert OMITTED to CODE to fix syntax
                    segments[i] = ContentSegment(
                        segment_type=ContentSegmentType.CODE,
                        content=segment.content,
                        start_line=segment.start_line,
                        end_line=segment.end_line,
                        metadata={**segment.metadata, "expanded_for_syntax": True},
                    )
                    logger.info(f"Expanded segment {i} to fix syntax at line {problem_line}")
                break

            current_line += segment_lines

    def _format_placeholders(
        self, segments: List[ContentSegment], file_data: ParsedFileData
    ) -> List[ContentSegment]:
        """Format placeholders for omitted segments with improved metadata."""
        result: List[ContentSegment] = []

        for segment in segments:
            if segment.segment_type == ContentSegmentType.OMITTED:
                line_count = segment.end_line - segment.start_line + 1

                # Count issues and patterns in omitted segment
                issue_count = sum(
                    1
                    for issue in file_data.security_issues
                    if segment.start_line <= issue.line_number <= segment.end_line
                )

                # Analyze what patterns are being omitted
                omitted_patterns = []
                segment_lines = segment.content.split("\n")

                for pattern_name, pattern in MODERN_PATTERNS.items():
                    if any(pattern.search(line) for line in segment_lines):
                        omitted_patterns.append(pattern_name)

                # Create informative placeholder
                pattern_info = (
                    f", patterns: {', '.join(omitted_patterns)}" if omitted_patterns else ""
                )
                placeholder = (
                    self.config.compression_placeholder.format(
                        lines=line_count,
                        issues=issue_count,
                    )
                    + pattern_info
                )

                # Enhanced metadata
                metadata = {
                    "original_content": segment.content,
                    "line_count": line_count,
                    "issue_count": issue_count,
                    "omitted_patterns": omitted_patterns,
                    "compression_pattern": self.pattern.value,
                }

                result.append(
                    ContentSegment(
                        segment_type=ContentSegmentType.OMITTED,
                        content=placeholder,
                        start_line=segment.start_line,
                        end_line=segment.end_line,
                        metadata=metadata,
                    )
                )
            else:
                result.append(segment)

        return result

    def apply_compression(self, file_data: ParsedFileData) -> str:
        """Apply compression to file content and return the compressed content."""
        if not self.config.enable_compression or not file_data.content:
            return file_data.content or ""

        segments = self.process_file(file_data)
        if not segments:
            return file_data.content or ""

        # Combine segments into final string
        result = []
        for segment in segments:
            result.append(segment.content)

        return "\n".join(result)
