"""
Compression processor for CodeConCat.

This module implements a content compression system that identifies and filters
out less important code segments while preserving metadata about what was omitted.
It breaks source code into segments that can be kept, omitted (with placeholder),
or treated as metadata.
"""

import logging
import re
from typing import Dict, List, Set

from codeconcat.base_types import (
    CodeConCatConfig,
    ContentSegment,
    ContentSegmentType,
    ParsedFileData,
    SecuritySeverity,
)
from codeconcat.constants import COMPRESSION_SETTINGS

logger = logging.getLogger(__name__)


class CompressionProcessor:
    """
    Processor that compresses code content by removing less important segments.

    It analyzes code content and creates a list of segments that can be:
    - CODE: Important code that should be preserved
    - OMITTED: Less important code that can be replaced with a placeholder
    - METADATA: Summaries, headers, or other metadata about the content
    """

    def __init__(self, config: CodeConCatConfig):
        """Initialize the compression processor with configuration settings."""
        self.config = config
        self._setup_compression_settings()

    def _setup_compression_settings(self) -> None:
        """Configure compression settings based on the compression level."""
        # Default settings
        self.min_lines_to_compress = self.config.compression_keep_threshold
        self.max_gap_to_merge = 3

        # Set thresholds based on compression level
        level = self.config.compression_level.lower()

        if level not in COMPRESSION_SETTINGS:
            logger.warning(f"Unknown compression level: {level}, using 'medium'")
            level = "medium"

        settings = COMPRESSION_SETTINGS[level]
        self.importance_threshold = settings["importance_threshold"]
        self.context_lines = settings["context_lines"]

        # Override min_lines for aggressive compression
        if level == "aggressive":
            self.min_lines_to_compress = 1

    def process_file(self, file_data: ParsedFileData) -> List[ContentSegment]:
        """
        Process a file and create a list of content segments based on importance.

        Args:
            file_data: The parsed file data containing code content and metadata

        Returns:
            A list of ContentSegment objects representing the file's content
        """
        if not file_data.content or not self.config.enable_compression:
            # If compression is disabled or no content, return a single CODE segment
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

        # Get content as lines for processing
        lines = file_data.content.split("\n")

        # Calculate importance score for each line
        line_importance = self._calculate_line_importance(lines, file_data)

        # Create initial segments
        segments = self._create_initial_segments(lines, line_importance)

        # Merge adjacent segments that are small
        merged_segments = self._merge_small_segments(segments)

        # Finally, format placeholders for omitted segments
        return self._format_placeholders(merged_segments, file_data)

    def _calculate_line_importance(
        self, lines: List[str], file_data: ParsedFileData
    ) -> List[float]:
        """
        Calculate importance scores for each line (0.0 to 1.0).
        Higher scores mean the line is more important to keep.

        Args:
            lines: The content as a list of lines
            file_data: The parsed file data containing declarations and issues

        Returns:
            A list of importance scores (0.0 to 1.0) for each line
        """
        total_lines = len(lines)
        line_importance = [0.0] * total_lines

        # Track important line numbers
        important_lines: Set[int] = set()

        # Lines with security issues are very important
        if file_data.security_issues:
            for issue in file_data.security_issues:
                # Convert 1-indexed line numbers to 0-indexed
                line_idx = issue.line_number - 1
                if 0 <= line_idx < total_lines:
                    important_lines.add(line_idx)

                    # High/Critical severity issues make surrounding code important too
                    if issue.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]:
                        for i in range(max(0, line_idx - 2), min(total_lines, line_idx + 3)):
                            important_lines.add(i)

        # Declarations are important - especially their signatures
        if file_data.declarations:
            for decl in file_data.declarations:
                # Add declaration start lines (signature)
                start_idx = decl.start_line - 1
                if 0 <= start_idx < total_lines:
                    important_lines.add(start_idx)

                    # Add a few more lines for the signature
                    for i in range(start_idx + 1, min(total_lines, start_idx + 3)):
                        important_lines.add(i)

                # Function/method end lines sometimes have important return statements
                end_idx = decl.end_line - 1
                if 0 <= end_idx < total_lines and end_idx != start_idx:
                    important_lines.add(end_idx)

        # Check for keep tags in comments
        keep_tags = self.config.compression_keep_tags
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Check for special keep tags in comments
            if any(tag.lower() in line_lower for tag in keep_tags):
                important_lines.add(i)
                # Also mark nearby lines as important
                for j in range(max(0, i - 1), min(total_lines, i + 2)):
                    important_lines.add(j)

            # Imports are usually important
            if re.search(r"^\s*(import|from\s+.*\s+import|#include|using\s+|require)", line):
                important_lines.add(i)

            # Assign some default importance based on line content
            if "=" in line or "return" in line:
                line_importance[i] = max(line_importance[i], 0.3)  # Assignments and returns
            elif re.search(r"\b(if|else|for|while|switch|case)\b", line):
                line_importance[i] = max(line_importance[i], 0.4)  # Control flow
            elif line.strip() and not line.strip().startswith(("#", "//", "/*", "*")):
                line_importance[i] = max(line_importance[i], 0.1)  # Non-empty, non-comment lines

        # Set high importance for identified important lines
        for line_idx in important_lines:
            line_importance[line_idx] = 1.0

        # Spread importance to context lines
        if self.context_lines > 0:
            context_importance = 0.8  # High but not maximum
            for i in range(total_lines):
                if line_importance[i] == 1.0:  # Found an important line
                    # Mark surrounding lines as context (before)
                    for j in range(max(0, i - self.context_lines), i):
                        line_importance[j] = max(line_importance[j], context_importance)
                    # Mark surrounding lines as context (after)
                    for j in range(i + 1, min(total_lines, i + self.context_lines + 1)):
                        line_importance[j] = max(line_importance[j], context_importance)

        return line_importance

    def _create_initial_segments(
        self, lines: List[str], line_importance: List[float]
    ) -> List[ContentSegment]:
        """
        Create initial content segments based on line importance.

        Args:
            lines: Content as a list of lines
            line_importance: Importance score for each line

        Returns:
            List of initial content segments
        """
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
                            start_line=segment_start + 1,  # 1-indexed
                            end_line=i,  # 1-indexed
                            metadata={},
                        )
                    )

                # Start a new segment
                segment_start = i
                segment_content = [line]
                current_type = line_type
            else:
                # Continue current segment
                segment_content.append(line)

        # Add the final segment
        if current_type is not None and segment_content:
            segments.append(
                ContentSegment(
                    segment_type=current_type,
                    content="\n".join(segment_content),
                    start_line=segment_start + 1,  # 1-indexed
                    end_line=len(lines),  # 1-indexed
                    metadata={},
                )
            )

        # Don't omit segments that are too small
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
        Merge adjacent segments if they're small to avoid excessive fragmentation.

        Args:
            segments: Initial content segments

        Returns:
            Merged content segments
        """
        if not segments:
            return []

        result: List[ContentSegment] = [segments[0]]

        for segment in segments[1:]:
            prev = result[-1]

            # Check if we should merge with previous segment
            if (
                # Small CODE segments surrounded by OMITTED can become OMITTED
                prev.segment_type == ContentSegmentType.OMITTED
                and segment.segment_type == ContentSegmentType.OMITTED
                and prev.end_line + 1 == segment.start_line
            ):
                # Merge OMITTED segments
                result[-1] = ContentSegment(
                    segment_type=ContentSegmentType.OMITTED,
                    content=prev.content + "\n" + segment.content,
                    start_line=prev.start_line,
                    end_line=segment.end_line,
                    metadata={**prev.metadata, **segment.metadata},
                )
            elif (
                # Small gap between CODE segments can be kept as CODE
                prev.segment_type == ContentSegmentType.CODE
                and segment.segment_type == ContentSegmentType.CODE
                and segment.start_line - prev.end_line <= self.max_gap_to_merge
            ):
                # Need to reconstruct the gap content (we don't have it)
                # This approximation assumes the gap is empty lines
                gap_lines = "\n" * (segment.start_line - prev.end_line - 1)

                # Merge CODE segments with the gap
                result[-1] = ContentSegment(
                    segment_type=ContentSegmentType.CODE,
                    content=prev.content + gap_lines + segment.content,
                    start_line=prev.start_line,
                    end_line=segment.end_line,
                    metadata={**prev.metadata, **segment.metadata},
                )
            else:
                # Otherwise add as a new segment
                result.append(segment)

        return result

    def _format_placeholders(
        self, segments: List[ContentSegment], file_data: ParsedFileData
    ) -> List[ContentSegment]:
        """
        Format placeholders for omitted segments with metadata.

        Args:
            segments: Content segments to process
            file_data: The parsed file data for context

        Returns:
            Content segments with formatted placeholders
        """
        result: List[ContentSegment] = []

        for segment in segments:
            if segment.segment_type == ContentSegmentType.OMITTED:
                # Count lines in this segment
                line_count = segment.end_line - segment.start_line + 1

                # Count security issues in this segment
                issue_count = 0
                issue_severities: Dict[str, int] = {}

                for issue in file_data.security_issues:
                    if segment.start_line <= issue.line_number <= segment.end_line:
                        issue_count += 1
                        severity_key = (
                            issue.severity.name
                            if hasattr(issue.severity, "name")
                            else str(issue.severity)
                        )
                        issue_severities[severity_key] = issue_severities.get(severity_key, 0) + 1

                # Create placeholder text
                placeholder = self.config.compression_placeholder.format(
                    lines=line_count,
                    issues=issue_count,
                )

                # Add metadata
                metadata = {
                    "original_content": segment.content,
                    "line_count": line_count,
                    "issue_count": issue_count,
                    "issue_severities": issue_severities,
                }

                # Replace content with placeholder
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
                # Keep other segments as is
                result.append(segment)

        return result

    def apply_compression(self, file_data: ParsedFileData) -> str:
        """
        Apply compression to file content and return the compressed content.

        Args:
            file_data: The parsed file data to compress

        Returns:
            The compressed content as a string
        """
        if not self.config.enable_compression or not file_data.content:
            return file_data.content or ""

        segments = self.process_file(file_data)
        if not segments:
            return file_data.content or ""

        # Combine segments into a final string
        result = []
        for segment in segments:
            result.append(segment.content)

        return "\n".join(result)
