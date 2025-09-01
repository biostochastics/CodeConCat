"""
CodeConCat Reconstruction Tool

Reconstructs original files from CodeConCat output (markdown, XML, or JSON).
"""

import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional, cast

logger = logging.getLogger(__name__)


class CodeConcatReconstructor:
    """Base class for reconstructing files from CodeConCat output."""

    def __init__(self, output_dir: str, verbose: bool = False):
        """Initialize with target output directory."""
        self.output_dir = Path(output_dir)
        self.files_processed = 0
        self.files_created = 0
        self.errors = 0
        self.verbose = verbose

    def reconstruct(self, input_file: str, format_type: Optional[str] = None) -> Dict[str, int]:
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

    def _parse_markdown(self, input_path: Path) -> Dict[str, str]:
        """Parse markdown output and extract files."""
        files = {}

        with open(input_path, encoding="utf-8") as f:
            content = f.read()

        # Try different markdown header patterns to be robust against variations
        patterns = [
            # Standard format: ## `path/to/file.ext`
            r"##\s+(?:File:)?\s*`([^`]+)`",
            # Alternative format: ## path/to/file.ext
            r"##\s+(?:File:)?\s*([^\s]+\.[^\s]+)",
            # H3 format: ### `path/to/file.ext`
            r"###\s+(?:File:)?\s*`([^`]+)`",
        ]

        # Try each pattern until we find one that works
        file_sections = []
        for pattern in patterns:
            file_sections = re.split(pattern, content)
            if len(file_sections) > 1:
                # Found a working pattern
                break

        if len(file_sections) <= 1:
            logger.warning(
                "No file sections found in markdown input. Trying alternative approaches..."
            )
            # Try to find code blocks with file paths in code info string
            code_blocks = re.finditer(r"```([^\n]+)\n(.*?)\n```", content, re.DOTALL)
            for match in code_blocks:
                file_info = match.group(1).strip()
                # Look for file path patterns in the code info string
                if "/" in file_info or "\\" in file_info or "." in file_info:
                    # This might be a file path or language with file path
                    possible_path = file_info.split(" ")[-1]  # Take last part if space-separated
                    if "." in possible_path:  # Simple check for file extension
                        files[possible_path] = match.group(2)
                        self.files_processed += 1
                        if self.verbose:
                            logger.debug(f"Found file from code block: {possible_path}")

            if not files:  # Still no files found
                logger.warning(
                    "Could not detect file sections in markdown using any known pattern."
                )
                return files
            return files

        # First element is pre-content, skip it
        file_sections = file_sections[1:]

        # Process file sections
        for i in range(0, len(file_sections), 2):
            if i + 1 >= len(file_sections):
                break

            file_path = file_sections[i].strip()
            file_content_with_meta = file_sections[i + 1]

            # Try multiple code block patterns
            # 1. Standard code blocks with language
            code_match: Optional[re.Match[str]] = re.search(
                r"```[\w-]*\n(.*?)\n```", file_content_with_meta, re.DOTALL
            )
            if not code_match:
                # 2. Code blocks without language
                code_match = re.search(r"```\n(.*?)\n```", file_content_with_meta, re.DOTALL)
            if not code_match:
                # 3. Code blocks with file path/language in first line
                code_match = re.search(
                    r"```.*?\n(?:.*?\n)?(.*?)\n```", file_content_with_meta, re.DOTALL
                )

            if code_match:
                # Get raw content
                raw_content = code_match.group(1)

                # Clean up file path (remove any markdown artifacts)
                file_path = file_path.strip("`").strip()

                # Clean up the extracted content - remove language identifier if present
                content_lines = raw_content.split("\n")
                # Check if first line might be a language specifier
                if (
                    len(content_lines) > 1
                    and len(content_lines[0]) < 20
                    and " " not in content_lines[0]
                ):
                    # If first line looks like a language identifier and isn't part of the code
                    if re.match(r"^[a-zA-Z0-9_+-]+$", content_lines[0]):
                        file_content = "\n".join(content_lines[1:])
                    else:
                        file_content = raw_content
                else:
                    file_content = raw_content

                files[file_path] = file_content
                self.files_processed += 1
                if self.verbose:
                    logger.debug(f"Parsed file: {file_path}")
            else:
                # One more attempt - try to find ANY code block
                match_any = re.search(r"```(.*?)```", file_content_with_meta, re.DOTALL)
                if match_any:
                    # Get raw content
                    raw_content = match_any.group(1).strip()

                    # Clean up the extracted content
                    content_lines = raw_content.split("\n")
                    # Check if first line might be a language specifier
                    if (
                        len(content_lines) > 1
                        and len(content_lines[0]) < 20
                        and " " not in content_lines[0]
                    ):
                        # If first line looks like a language identifier and isn't part of the code
                        if re.match(r"^[a-zA-Z0-9_+-]+$", content_lines[0]):
                            file_content = "\n".join(content_lines[1:])
                        else:
                            file_content = raw_content
                    else:
                        file_content = raw_content

                    files[file_path] = file_content
                    self.files_processed += 1
                    if self.verbose:
                        logger.debug(f"Parsed file using fallback method: {file_path}")
                else:
                    logger.warning(f"Could not extract content for {file_path}")
                    self.errors += 1

        return files

    def _parse_xml(self, input_path: Path) -> Dict[str, str]:
        """Parse XML output and extract files."""
        files = {}

        try:
            with open(input_path, encoding="utf-8") as f:
                xml_content = f.read()

            # Remove any XML declaration that might cause parsing issues
            xml_content = re.sub(r"<\?xml[^>]+\?>", "", xml_content)

            # Try parsing the XML
            try:
                root = ET.fromstring(xml_content)
            except ET.ParseError as e:
                # If parsing fails, try to clean the XML by removing problematic sections
                logger.warning(f"Initial XML parsing failed: {e}. Attempting cleanup...")
                # Remove CDATA sections that might be malformed
                xml_content = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", xml_content)
                # Fix unclosed tags
                xml_content = re.sub(r"<([^\s/>]+)[^>]*>[^<]*$", r"<\1></\1>", xml_content)
                try:
                    root = ET.fromstring(xml_content)
                except ET.ParseError as e2:
                    logger.error(f"XML parsing failed after cleanup: {e2}")
                    raise

            # Find all file elements using multiple patterns
            file_elements = []

            # Try standard pattern first
            file_elements = root.findall(".//file")

            # If no files found, try alternative patterns
            if not file_elements:
                # Try files inside a files container
                file_elements = root.findall(".//files/file")

            if not file_elements:
                # Try any element with a path attribute and content child
                for elem in root.findall(".//*[@path]"):
                    if elem.find("./content") is not None:
                        file_elements.append(elem)

            # Process all found file elements
            for file_elem in file_elements:
                # Try to get path from different attributes
                file_path: Optional[str] = None
                for attr_name in ["path", "name", "filename", "filepath"]:
                    file_path = file_elem.get(attr_name)
                    if file_path:
                        break

                if not file_path:
                    logger.warning("Found file element without path attribute")
                    continue

                # Look for content in different ways
                content: Optional[str] = None

                # 1. Standard content element
                content_elem = file_elem.find("./content")
                if content_elem is not None and content_elem.text is not None:
                    content = content_elem.text

                # 2. Content as direct text of file element
                if content is None and file_elem.text and file_elem.text.strip():
                    content = file_elem.text

                # 3. Content in CDATA section
                if content is None:
                    cdata_match = re.search(
                        r"<!\[CDATA\[(.*?)\]\]>",
                        ET.tostring(file_elem, encoding="unicode"),
                        re.DOTALL,
                    )
                    if cdata_match:
                        content = cdata_match.group(1)

                # 4. Content in code element
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

    def _parse_json(self, input_path: Path) -> Dict[str, str]:
        """Parse JSON output and extract files."""
        files = {}

        try:
            with open(input_path, encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
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
                        raise

            # Try multiple approaches to find files in the JSON structure

            # Approach 1: Standard files array
            if "files" in data and isinstance(data["files"], list):
                file_array = data["files"]

                for file_data in file_array:
                    # Different file path keys
                    file_path: Optional[str] = None
                    for key in ["path", "filepath", "name", "filename"]:
                        if key in file_data:
                            file_path = file_data[key]
                            break

                    # Different content keys
                    file_content: Optional[str] = None
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
            elif len(data) > 0 and all(isinstance(v, (str, dict)) for v in data.values()):
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

    def _find_files_in_nested_json(self, data: Any, files: Dict[str, str]) -> None:
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
        """Write content to a file, creating directories as needed."""
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

        # Create full output path
        output_path = self.output_dir / norm_path

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
    format_type: Optional[str] = None,
    verbose: bool = False,
) -> Dict:
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
    reconstructor = CodeConcatReconstructor(output_dir, verbose)
    return reconstructor.reconstruct(input_file, format_type)
