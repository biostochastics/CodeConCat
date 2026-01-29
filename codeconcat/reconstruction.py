"""
CodeConCat Reconstruction Tool

Reconstructs original files from CodeConCat output (markdown, XML, or JSON).

Format Support (v2.0):
    - Markdown: ### N. file.py {#anchor}
    - XML: <file_entry><file_metadata><path>...</path></file_metadata><file_content>...</file_content></file_entry>
    - JSON: {"files": [{"file_path": "...", "content": "..."}]}

Security:
    All file writes are protected against path traversal attacks using validate_safe_path()
    from codeconcat.utils.path_security.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, cast

from codeconcat.utils.path_security import PathTraversalError, validate_safe_path

try:
    import defusedxml.ElementTree as ET

    _DEFUSEDXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET

    _DEFUSEDXML_AVAILABLE = False

logger = logging.getLogger(__name__)

_FENCE_LINE_RE = re.compile(r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


class CodeConcatReconstructor:
    """Base class for reconstructing files from CodeConCat output."""

    def __init__(self, output_dir: str, verbose: bool = False, strict: bool = True):
        """Initialize with target output directory."""
        self.output_dir = Path(output_dir)
        self.files_processed = 0
        self.files_created = 0
        self.errors = 0
        self.verbose = verbose
        self.strict = strict

        if not _DEFUSEDXML_AVAILABLE:
            logger.warning(
                "defusedxml is not installed; XML parsing may be unsafe for untrusted inputs."
            )

    def reconstruct(self, input_file: str, format_type: str | None = None) -> dict[str, int]:
        """
        Reconstruct files from a CodeConCat output file.

        Args:
            input_file: Path to the CodeConCat output file
            format_type: Format type ('markdown', 'xml', 'json', or None for auto-detection)
        """
        input_path = Path(input_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Auto-detect format if not specified
        if format_type is None:
            extension = input_path.suffix.lower()
            if extension == ".md" or extension == ".markdown":
                format_type = "markdown"
            elif extension == ".xml":
                format_type = "xml"
            elif extension == ".json":
                format_type = "json"
            else:
                raise ValueError(f"Unable to determine format from extension: {extension}")

        logger.info(f"Processing {input_file} as {format_type}...")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Process based on format
        if format_type == "markdown":
            files = self._parse_markdown(input_path)
        elif format_type == "xml":
            files = self._parse_xml(input_path)
        elif format_type == "json":
            files = self._parse_json(input_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        # Write files
        for file_path, content in files.items():
            self._write_file(file_path, content)

        logger.info("\nReconstruction complete!")
        logger.info(f"Files processed: {self.files_processed}")
        logger.info(f"Files created: {self.files_created}")
        logger.info(f"Errors: {self.errors}")

        return {
            "files_processed": self.files_processed,
            "files_created": self.files_created,
            "errors": self.errors,
        }

    def _is_diff_fence(self, info: str) -> bool:
        token = info.strip().split(" ", 1)[0].lower() if info else ""
        return token in {"diff", "patch"}

    def _strip_leading_language_line(self, content: str) -> str:
        content_lines = content.split("\n")
        if (
            len(content_lines) > 1
            and len(content_lines[0]) < 20
            and " " not in content_lines[0]
            and re.match(r"^[a-zA-Z0-9_+-]+$", content_lines[0])
        ):
            return "\n".join(content_lines[1:])
        return content

    def _extract_section_fence(self, text: str) -> tuple[str, str] | None:
        lines = text.splitlines()
        fence_lines: list[tuple[int, str, str]] = []

        for index, line in enumerate(lines):
            match = _FENCE_LINE_RE.match(line)
            if match:
                fence_lines.append((index, match.group("fence"), match.group("info").strip()))

        if not fence_lines:
            return None

        start_index, start_fence, info = fence_lines[0]
        fence_char = start_fence[0]
        min_len = len(start_fence)
        end_index = None

        for index, fence, _ in fence_lines[1:]:
            if fence[0] == fence_char and len(fence) >= min_len:
                end_index = index

        if end_index is None or end_index <= start_index:
            return None

        content = "\n".join(lines[start_index + 1 : end_index])
        return info, content

    def _find_fenced_blocks(self, text: str) -> list[tuple[str, str]]:
        blocks: list[tuple[str, str]] = []
        lines = text.splitlines()
        index = 0

        while index < len(lines):
            match = _FENCE_LINE_RE.match(lines[index])
            if not match:
                index += 1
                continue

            fence = match.group("fence")
            info = match.group("info").strip()
            fence_char = fence[0]
            min_len = len(fence)
            end_index = None

            for next_index in range(index + 1, len(lines)):
                end_match = _FENCE_LINE_RE.match(lines[next_index])
                if end_match:
                    end_fence = end_match.group("fence")
                    if end_fence[0] == fence_char and len(end_fence) >= min_len:
                        end_index = next_index
                        break

            if end_index is None:
                break

            content = "\n".join(lines[index + 1 : end_index])
            blocks.append((info, content))
            index = end_index + 1

        return blocks

    def _parse_markdown(self, input_path: Path) -> dict[str, str]:
        """Parse markdown output and extract files.

        Supports current format (v2.0):
            ### 1. path/to/file.ext {#anchor}

        This parser includes security validation to prevent path traversal attacks.
        """
        files: dict[str, str] = {}

        with open(input_path, encoding="utf-8") as f:
            content = f.read()

        header_patterns = [re.compile(r"^###\s+\d+\.\s+(.+?)(?:\s+\{#[^}]+\})?\s*$", re.MULTILINE)]

        matches: list[re.Match[str]] = []
        for pattern in header_patterns:
            matches = list(pattern.finditer(content))
            if matches:
                break

        if not matches:
            logger.warning(
                "No file sections found in markdown input. Trying alternative approaches..."
            )
            for info, block_content in self._find_fenced_blocks(content):
                file_info = info.strip()
                if "/" in file_info or "\\" in file_info or "." in file_info:
                    possible_path = file_info.split(" ")[-1]
                    if "." in possible_path:
                        files[possible_path] = self._strip_leading_language_line(block_content)
                        self.files_processed += 1
                        if self.verbose:
                            logger.debug(f"Found file from code block: {possible_path}")

            if not files:
                logger.warning(
                    "Could not detect file sections in markdown using any known pattern."
                )
                return files
            return files

        for index, match in enumerate(matches):
            file_path = match.group(1).strip()
            section_start = match.end()
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            file_content_with_meta = content[section_start:section_end]

            fence = self._extract_section_fence(file_content_with_meta)
            if fence is None:
                blocks = self._find_fenced_blocks(file_content_with_meta)
                fence = blocks[0] if blocks else None

            if fence is None:
                logger.warning(f"Could not extract content for {file_path}")
                self.errors += 1
                continue

            info, raw_content = fence

            if self._is_diff_fence(info):
                non_diff_blocks = [
                    block
                    for block in self._find_fenced_blocks(file_content_with_meta)
                    if not self._is_diff_fence(block[0])
                ]
                if non_diff_blocks:
                    info, raw_content = non_diff_blocks[0]
                else:
                    logger.warning(
                        f"Diff-only block found for {file_path}; skipping reconstruction"
                    )
                    self.errors += 1
                    continue

            file_path = file_path.strip("`").strip()
            file_content = self._strip_leading_language_line(raw_content)
            files[file_path] = file_content
            self.files_processed += 1
            if self.verbose:
                logger.debug(f"Parsed file: {file_path}")

        return files

    def _parse_xml(self, input_path: Path) -> dict[str, str]:
        """Parse XML output and extract files.

        Supports current format (v2.0):
            <file_entry>
              <file_metadata>
                <path>file.py</path>
                <language>python</language>
              </file_metadata>
              <file_content>...</file_content>
            </file_entry>

        This parser includes security validation to prevent path traversal attacks.
        """
        files: dict[str, str] = {}

        try:
            with open(input_path, encoding="utf-8") as f:
                xml_content = f.read()

            # Remove any XML declaration that might cause parsing issues
            xml_content = re.sub(r"<\?xml[^>]+\?>", "", xml_content)

            # Try parsing the XML
            try:
                root = ET.fromstring(xml_content)
            except ET.ParseError as e:
                if self.strict:
                    logger.error(f"XML parsing failed in strict mode: {e}")
                    self.errors += 1
                    return files
                logger.warning(f"Initial XML parsing failed: {e}. Attempting cleanup...")
                # Remove CDATA sections that might be malformed
                xml_content = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", xml_content)
                # Fix unclosed tags
                xml_content = re.sub(r"<([^\s/>]+)[^>]*>[^<]*$", r"<\1></\1>", xml_content)
                try:
                    root = ET.fromstring(xml_content)
                except ET.ParseError as e2:
                    logger.error(f"XML parsing failed after cleanup: {e2}")
                    self.errors += 1
                    return files

            # Find all file elements using multiple patterns
            file_elements = []

            # Try current format first (v2.0): <file_entry> elements
            file_elements = root.findall(".//file_entry")

            # If no files found, try legacy patterns
            if not file_elements:
                # Legacy: files inside a files container
                file_elements = root.findall(".//files/file")

            if not file_elements:
                # Legacy: standard <file> elements
                file_elements = root.findall(".//file")

            if not file_elements:
                # Legacy: any element with a path attribute and content child
                for elem in root.findall(".//*[@path]"):
                    if elem.find("./content") is not None:
                        file_elements.append(elem)

            # Process all found file elements
            for file_elem in file_elements:
                # Try to get path - first from nested element (current format)
                file_path: str | None = None

                # Current format (v2.0): <file_metadata><path>
                path_elem = file_elem.find(".//file_metadata/path")
                if path_elem is not None and path_elem.text:
                    file_path = path_elem.text

                # Legacy: try attributes if nested element not found
                if not file_path:
                    for attr_name in ["path", "name", "filename", "filepath"]:
                        file_path = file_elem.get(attr_name)
                        if file_path:
                            break

                if not file_path:
                    logger.warning("Found file element without path")
                    continue

                # Look for content in different ways
                content: str | None = None

                # 1. Current format (v2.0): <file_content> element
                content_elem = file_elem.find(".//file_content")
                if content_elem is not None and content_elem.text is not None:
                    content = content_elem.text

                # 2. Legacy: Standard content element
                if content is None:
                    content_elem = file_elem.find("./content")
                    if content_elem is not None and content_elem.text is not None:
                        content = content_elem.text

                # 3. Legacy: Content as direct text of file element
                if content is None and file_elem.text and file_elem.text.strip():
                    content = file_elem.text

                # 4. Legacy: Content in CDATA section
                if content is None:
                    cdata_match = re.search(
                        r"<!\[CDATA\[(.*?)\]\]>",
                        ET.tostring(file_elem, encoding="unicode"),
                        re.DOTALL,
                    )
                    if cdata_match:
                        content = cdata_match.group(1)

                # 5. Legacy: Content in code element
                if content is None:
                    code_elem = file_elem.find("./code")
                    if code_elem is not None and code_elem.text is not None:
                        content = code_elem.text

                if content is None:
                    logger.warning(f"No content found for {file_path}")
                    self.errors += 1
                    continue

                files[file_path] = content
                self.files_processed += 1
                if self.verbose:
                    logger.debug(f"Parsed file: {file_path}")

            if not files and self.verbose:
                logger.warning(f"No files found in XML. Root tag: {root.tag}")
                for child in root:
                    logger.debug(f"Child tag: {child.tag}")

            return files

        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            self.errors += 1
            return files

    def _parse_json(self, input_path: Path) -> dict[str, str]:
        """Parse JSON output and extract files.

        Supports current format (v2.0):
            {"files": [{"file_path": "...", "content": "..."}]}

        This parser includes security validation to prevent path traversal attacks.
        """
        files: dict[str, str] = {}

        try:
            with open(input_path, encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    if self.strict:
                        logger.error(f"JSON parsing failed in strict mode: {e}")
                        self.errors += 1
                        return files
                    # Try to fix common JSON issues
                    logger.warning(f"JSON parsing failed: {e}. Attempting to fix...")
                    f.seek(0)  # Go back to start of file
                    json_content = f.read()

                    # Fix unquoted keys
                    json_content = re.sub(
                        r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', json_content
                    )
                    # Fix trailing commas
                    json_content = re.sub(r",\s*([}\]])", r"\1", json_content)
                    # Fix single quotes
                    json_content = re.sub(r"'([^']*)'\s*:", r'"\1":', json_content)

                    try:
                        data = json.loads(json_content)
                    except json.JSONDecodeError as e2:
                        logger.error(f"JSON parsing failed after fixes: {e2}")
                        self.errors += 1
                        return files

            # Try multiple approaches to find files in the JSON structure

            # Approach 1: Standard files array
            if "files" in data and isinstance(data["files"], list):
                file_array = data["files"]

                for file_data in file_array:
                    # Different file path keys (prioritize current format)
                    file_path: str | None = None
                    # Current format (v2.0): "file_path"
                    # Legacy formats: "path", "filepath", "name", "filename"
                    for key in ["file_path", "path", "filepath", "name", "filename"]:
                        if key in file_data:
                            file_path = file_data[key]
                            break

                    # Different content keys
                    file_content: str | None = None
                    for key in ["content", "code", "text", "source"]:
                        if key in file_data:
                            file_content = file_data[key]
                            break

                    if not file_path or file_content is None:
                        continue

                    # Type narrowing: at this point file_path is guaranteed to be str
                    assert file_path is not None
                    files[file_path] = file_content
                    self.files_processed += 1
                    if self.verbose:
                        logger.debug(f"Parsed file: {file_path}")

            # Approach 2: Files as a dictionary with paths as keys
            elif "files" in data and isinstance(data["files"], dict):
                for file_path, file_data in data["files"].items():
                    # Cast to ensure type safety - JSON keys are always strings
                    file_path = cast(str, file_path)
                    # Check if the value is a string (content) or a dictionary
                    if isinstance(file_data, str):
                        dict_content = file_data
                    elif isinstance(file_data, dict):
                        # Try different content keys
                        dict_content = None
                        for key in ["content", "code", "text", "source"]:
                            if key in file_data:
                                dict_content = file_data[key]
                                break
                    else:
                        continue

                    if dict_content is not None:
                        files[file_path] = dict_content
                        self.files_processed += 1
                        if self.verbose:
                            logger.debug(f"Parsed file from dictionary: {file_path}")

            # Approach 3: Direct file content mapping at root level
            elif len(data) > 0 and all(isinstance(v, str | dict) for v in data.values()):
                # This might be a direct mapping of file paths to content
                for file_path, value in data.items():
                    # Cast to ensure type safety - JSON keys are always strings
                    file_path = cast(str, file_path)
                    # Only consider keys that look like file paths
                    if (
                        "/" in file_path or "\\" in file_path or "." in file_path
                    ) and not file_path.startswith("_"):
                        root_content = value if isinstance(value, str) else None
                        if isinstance(value, dict) and "content" in value:
                            root_content = value["content"]

                        if root_content is not None:
                            files[file_path] = root_content
                            self.files_processed += 1
                            if self.verbose:
                                logger.debug(f"Parsed file from root level: {file_path}")

            # Approach 4: Nested structure with file lists
            if not files:
                self._find_files_in_nested_json(data, files)

            return files

        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            self.errors += 1
            return files

    def _find_files_in_nested_json(self, data: Any, files: dict[str, str]) -> None:
        """Recursively search for files in nested JSON structures."""
        if isinstance(data, dict):
            # Check if this object looks like a file
            if "path" in data and "content" in data:
                file_path = data["path"]
                content = data["content"]
                if file_path and content is not None:
                    files[file_path] = content
                    self.files_processed += 1
                    if self.verbose:
                        logger.debug(f"Parsed file from nested structure: {file_path}")

            # Recursively search in all values
            for value in data.values():
                self._find_files_in_nested_json(value, files)

        elif isinstance(data, list):
            # Recursively search in all items
            for item in data:
                self._find_files_in_nested_json(item, files)

    def _handle_compressed_content(self, content: str) -> str:
        """Process content that may contain compression placeholders
        to ensure they are properly formatted in reconstructed files."""
        # We need to preserve compression placeholders but ensure they're properly formatted
        # The compression placeholders look like: "[...code omitted: 15 lines]"

        if not content or "[...code omitted" not in content:
            return content

        # The content contains compression markers - make sure they're properly formatted
        # Compression markers should be on their own line with proper indentation

        # Find all compression placeholders and their indentation
        compressed_segments = re.finditer(
            r"^(\s*)\[\.\.\.(code|lines) omitted[^\]]*\]", content, re.MULTILINE
        )

        # Create a new string with properly formatted compression placeholders
        new_content = content
        for match in compressed_segments:
            indentation = match.group(1)  # Capture the indentation
            placeholder = match.group(0)  # The entire placeholder

            # Ensure the placeholder is properly formatted (on its own line)
            # Check if there's content before or after the placeholder on the same line
            line_pattern = re.compile(r"^.*?" + re.escape(placeholder) + r".*?$", re.MULTILINE)
            line_match = line_pattern.search(new_content)

            if line_match and line_match.group(0) != placeholder:
                # The placeholder isn't on its own line - fix it
                line = line_match.group(0)
                fixed_line = line.replace(
                    placeholder, f"\n{indentation}{placeholder}\n{indentation}"
                )
                new_content = new_content.replace(line, fixed_line)

        return new_content

    def _write_file(self, file_path: str, content: str) -> None:
        """Write content to a file, creating directories as needed.

        Security: This method includes path traversal protection using validate_safe_path()
        to ensure all file writes remain within the output directory boundary.
        """
        # Normalize path to handle different path formats

        # Special handling for citationSloth paths - extract the relative portion
        if "citationSloth/" in file_path:
            # Find the last occurrence of "citationSloth/"
            index = file_path.rfind("citationSloth/")
            norm_path = file_path[index + len("citationSloth/") :] if index >= 0 else file_path
        else:
            # For all other paths, keep the structure but ensure it's relative
            norm_path = file_path

        # Remove any leading slashes to ensure path is relative
        norm_path = norm_path.lstrip("/")

        # SECURITY: Validate path before any file operations
        try:
            validated_path = validate_safe_path(
                norm_path, base_path=self.output_dir, allow_symlinks=False
            )
            output_path = validated_path
        except (PathTraversalError, ValueError) as e:
            logger.error(f"Security: Path validation failed for '{file_path}': {e}")
            self.errors += 1
            return

        # Process the content for proper handling of compressed segments
        processed_content = self._handle_compressed_content(content)

        try:
            # Create parent directories
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(processed_content)

            self.files_created += 1
            logger.info(f"Created: {output_path}")

        except Exception as e:
            logger.error(f"Error writing {output_path}: {e}")
            self.errors += 1


def reconstruct_from_file(
    input_file: str,
    output_dir: str = "./reconstructed",
    format_type: str | None = None,
    verbose: bool = False,
    strict: bool = True,
) -> dict:
    """
    Reconstruct files from a CodeConCat output file.

    Args:
        input_file: Path to the CodeConCat output file
        output_dir: Directory to output reconstructed files
        format_type: Format type ('markdown', 'xml', 'json', or None for auto-detection)
        verbose: Whether to output verbose logs

    Returns:
        Dict with statistics about the reconstruction
    """
    reconstructor = CodeConcatReconstructor(output_dir, verbose=verbose, strict=strict)
    return reconstructor.reconstruct(input_file, format_type)
