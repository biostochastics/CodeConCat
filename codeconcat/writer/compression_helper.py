"""Compression helper module for CodeConCat writers.

This module provides unified compression functionality for all writer modules,
enabling transparent compression of output files using gzip or bz2 algorithms.
It also manages compression segments for intelligent content reduction.

The compression helper serves two main purposes:
1. File compression: Transparent gzip/bz2 compression of output files
2. Content segmentation: Managing compressed segments within documents

Key Features:
- Transparent file compression with gzip and bz2
- Backward-compatible segment extraction
- Format-agnostic compression (works with JSON, XML, text, markdown)
- Memory-efficient streaming compression
- Type-safe file handle management

Architecture:
    The module provides a static utility class that:
    1. Opens files with optional compression
    2. Extracts compression segments from configuration
    3. Formats segments for different output formats
    4. Maintains backward compatibility with legacy formats

Example:
    >>> from codeconcat.writer.compression_helper import CompressionHelper
    >>> # Open a gzip-compressed file for writing
    >>> with CompressionHelper.get_compression_stream('output.json.gz', 'gzip') as f:
    ...     f.write(json_content)
    >>> # Extract segments for a specific file
    >>> segments = CompressionHelper.extract_compressed_segments(config, 'main.py')
"""

import bz2
import gzip
from pathlib import Path
from typing import Any, Optional, Union


class CompressionHelper:
    """Unified compression utilities for CodeConCat writers.

    This class provides static methods for managing both file-level compression
    (gzip/bz2) and content-level compression (segment extraction). All methods
    are static to allow easy access without instantiation.

    The class handles:
    - Opening files with transparent compression
    - Extracting compression segments from configuration
    - Formatting segments for different output formats
    - Maintaining backward compatibility with legacy formats

    Note:
        All methods are static as this is a utility class with no state.
        The class serves as a namespace for compression-related functions.
    """

    @staticmethod
    def get_compression_stream(
        file_path: Union[str, Path], compression: Optional[str] = None, mode: str = "wt"
    ) -> Any:
        """Open a file with optional transparent compression.

        Creates a file handle that automatically compresses data on write using
        the specified compression algorithm. Supports both text and binary modes
        with automatic encoding handling.

        Args:
            file_path: Path to the output file. Can be string or Path object.
                      File extension is not automatically adjusted.
            compression: Compression algorithm to use. Options:
                        - 'gzip': GNU zip compression (.gz files)
                        - 'bz2': Bzip2 compression (.bz2 files)
                        - None or 'none': No compression (plain file)
            mode: File open mode. Common modes:
                  - 'wt': Write text (default, with UTF-8 encoding)
                  - 'wb': Write binary (no encoding)
                  - 'rt': Read text (with UTF-8 encoding)
                  - 'rb': Read binary (no encoding)

        Returns:
            An open file handle with transparent compression if specified.
            The handle supports standard file operations (write, read, etc.)
            and automatically compresses/decompresses data.

        Raises:
            ValueError: If compression type is not 'gzip', 'bz2', None, or 'none'.
            OSError: If the file cannot be opened (permissions, disk full, etc.).

        Complexity:
            O(1) for opening the file handle.
            Compression itself is O(n) where n is the data size.

        Flow:
            Called by: write_json(), write_xml(), write_markdown(), write_text()
            Calls: gzip.open(), bz2.open(), or built-in open()

        Example:
            >>> # Write compressed JSON
            >>> with CompressionHelper.get_compression_stream('data.json.gz', 'gzip') as f:
            ...     f.write(json.dumps(data))
            >>> # Write uncompressed text
            >>> with CompressionHelper.get_compression_stream('output.txt', None) as f:
            ...     f.write("Hello, world!")

        See Also:
            - gzip.open: Python's gzip compression module
            - bz2.open: Python's bz2 compression module
        """
        # Convert to Path object for consistent handling
        path = Path(file_path)

        # Determine encoding based on mode (text modes need UTF-8)
        encoding = "utf-8" if "t" in mode else None

        if compression == "gzip":
            # Use gzip compression with automatic encoding for text mode
            return gzip.open(path, mode, encoding=encoding)
        elif compression == "bz2":
            # Use bz2 compression with automatic encoding for text mode
            return bz2.open(path, mode, encoding=encoding)
        elif compression is None or compression == "none":
            # No compression - use standard file open
            return open(path, mode, encoding=encoding)  # noqa: SIM115
        else:
            # Unsupported compression type - fail fast with clear error
            raise ValueError(f"Unsupported compression type: {compression}")

    @staticmethod
    def extract_compressed_segments(config, item_file_path):
        """Extract compression segments for a specific file from configuration.

        Retrieves the list of compressed segments (code sections marked for
        omission or compression) for a specific file. Maintains backward
        compatibility with both modern dict format and legacy list format.

        Args:
            config: CodeConCatConfig instance containing compression settings.
                   Should have _compressed_segments attribute if compression
                   is enabled.
            item_file_path: Path of the file to retrieve segments for.
                          Should match the path used when segments were created.

        Returns:
            List of segment objects for the specified file. Each segment contains:
            - segment_type: Enum value (CODE, OMITTED, METADATA)
            - start_line: Starting line number
            - end_line: Ending line number
            - content: The segment content
            - metadata: Optional metadata dict
            Returns empty list if no segments found or compression disabled.

        Complexity:
            O(1) for dict format (hash lookup).
            O(n) for legacy list format where n is total segments.

        Flow:
            Called by: write_xml() when adding compression segments
            Calls: getattr() for safe attribute access

        Note:
            - Internal method using private _compressed_segments attribute
            - Handles both dict format (file_path -> segments) and list format
            - Legacy format requires filtering by file_path attribute
            - Returns empty list rather than None for consistency

        Example:
            >>> segments = CompressionHelper.extract_compressed_segments(config, 'main.py')
            >>> for segment in segments:
            ...     print(f"{segment.segment_type}: lines {segment.start_line}-{segment.end_line}")
        """
        # Safely retrieve the private compression segments attribute
        compressed_segments = getattr(config, "_compressed_segments", None)
        if not compressed_segments:
            # No compression data available
            return []

        # Modern format: dict mapping file paths to segment lists
        if isinstance(compressed_segments, dict):
            # Direct O(1) lookup by file path
            return compressed_segments.get(item_file_path, [])

        # Legacy format: flat list of all segments across all files
        # Must filter to find segments for the requested file
        # O(n) operation where n is total number of segments
        return [
            segment
            for segment in compressed_segments
            if hasattr(segment, "file_path") and segment.file_path == item_file_path
        ]

    @staticmethod
    def format_segment_for_json(segment) -> dict:
        """Format a compression segment for JSON serialization.

        Converts a segment object into a dictionary suitable for JSON output.
        Extracts all relevant fields and ensures they are JSON-serializable.

        Args:
            segment: The segment object to format. Expected to have:
                    - segment_type: Enum with a .value attribute
                    - start_line: Integer line number
                    - end_line: Integer line number
                    - content: String content
                    - metadata: Optional dict of additional data

        Returns:
            Dictionary with the following structure:
            {
                "type": str,        # Segment type value (CODE/OMITTED/METADATA)
                "start_line": int,  # Starting line number
                "end_line": int,    # Ending line number
                "content": str,     # Segment content
                "metadata": dict    # Optional metadata
            }

        Raises:
            AttributeError: If segment is missing required attributes
            TypeError: If segment attributes have incorrect types

        Complexity:
            O(1) - Simple field extraction and dictionary creation.

        Flow:
            Called by: write_json() when formatting compression segments
            Calls: segment_type.value to get enum string value

        Note:
            - Validates segment has all required attributes
            - segment_type must be an Enum with .value attribute
            - metadata can be None or any JSON-serializable dict
            - Falls back to safe defaults if attributes are invalid

        Example:
            >>> segment = CompressionSegment(
            ...     segment_type=SegmentType.CODE,
            ...     start_line=10,
            ...     end_line=20,
            ...     content="def foo():\\n    pass",
            ...     metadata={"complexity": 1}
            ... )
            >>> formatted = CompressionHelper.format_segment_for_json(segment)
            >>> assert formatted["type"] == "CODE"
            >>> assert formatted["start_line"] == 10

        See Also:
            - write_json(): Uses this for JSON output formatting
            - extract_compressed_segments(): Retrieves segments to format
        """
        try:
            # Validate and extract segment type
            segment_type = getattr(segment, "segment_type", None)
            if segment_type and hasattr(segment_type, "value"):
                type_value = segment_type.value
            else:
                type_value = str(segment_type) if segment_type else "UNKNOWN"

            # Safely extract line numbers with validation
            start_line = getattr(segment, "start_line", 0)
            end_line = getattr(segment, "end_line", 0)

            # Ensure line numbers are integers
            try:
                start_line = int(start_line)
                end_line = int(end_line)
            except (TypeError, ValueError):
                start_line = 0
                end_line = 0

            # Get content, default to empty string
            content = getattr(segment, "content", "")
            if not isinstance(content, str):
                content = str(content)

            # Get metadata, ensure it's dict or None
            metadata = getattr(segment, "metadata", None)
            if metadata and not isinstance(metadata, dict):
                metadata = None

            return {
                "type": type_value,
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "metadata": metadata,
            }
        except Exception as e:
            # Log error and return minimal valid structure
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error formatting segment for JSON: {e}")
            return {
                "type": "ERROR",
                "start_line": 0,
                "end_line": 0,
                "content": "",
                "metadata": {"error": str(e)},
            }
