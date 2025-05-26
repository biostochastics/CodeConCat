"""XML writer for CodeConcat output."""

import xml.etree.ElementTree as ET
from typing import List
from xml.dom import minidom

from codeconcat.base_types import (
    CodeConCatConfig,
    WritableItem,
)


def write_xml(
    items: List[WritableItem],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Write the concatenated code and docs to an XML file, respecting config flags."""

    root = ET.Element("codeconcat_output")

    # --- Repository Overview --- #
    if config.include_repo_overview:
        repo_overview = ET.SubElement(root, "repository_overview")
        # Add directory structure if configured and available
        if config.include_directory_structure and folder_tree_str:
            tree_elem = ET.SubElement(repo_overview, "directory_structure")
            # Use CDATA for potentially complex tree string
            tree_elem.text = f"<![CDATA[{folder_tree_str}]]>"

    # --- File Index --- #
    if config.include_file_index:
        file_index = ET.SubElement(root, "file_index")
        # Sort items if needed for index consistency with file section
        items_for_index = sorted(items, key=lambda x: x.file_path) if config.sort_files else items
        for item in items_for_index:
            ET.SubElement(file_index, "file", path=item.file_path)

    # --- Files Section --- #
    files_section = ET.SubElement(root, "files")

    # Sort items if requested before processing
    items_to_process = sorted(items, key=lambda x: x.file_path) if config.sort_files else items

    # Single loop processing all items polymorphically
    for item in items_to_process:
        item_element = item.render_xml_element(config)

        # Add compression information if available
        if (
            config.enable_compression
            and hasattr(config, "_compressed_segments")
            and hasattr(item, "file_path")
        ):
            # Find segments related to this file
            compressed_segments = getattr(config, "_compressed_segments", None)
            if compressed_segments:
                # Handle both dict and list formats for backward compatibility
                if isinstance(compressed_segments, dict):
                    file_segments = compressed_segments.get(item.file_path, [])
                else:
                    # Legacy format: list of segments (assume all belong to current file)
                    file_segments = compressed_segments

                if file_segments:
                    # Add compression attribute
                    item_element.set("compression_applied", "true")

                    # Create segments container
                    segments_element = ET.SubElement(item_element, "content_segments")

                    # Add each segment
                    for segment in file_segments:
                        seg_element = ET.SubElement(
                            segments_element,
                            "segment",
                            {
                                "type": segment.segment_type.value,
                                "start_line": str(segment.start_line),
                                "end_line": str(segment.end_line),
                            },
                        )

                        # Add content as CDATA to preserve formatting
                        content_element = ET.SubElement(seg_element, "content")
                        content_element.text = f"<![CDATA[{segment.content}]]>"

                        # Add metadata if present
                        if segment.metadata:
                            metadata_element = ET.SubElement(seg_element, "metadata")
                            for key, value in segment.metadata.items():
                                if isinstance(value, (str, int, float, bool)):
                                    meta_item = ET.SubElement(
                                        metadata_element, "item", {"key": key}
                                    )
                                    meta_item.text = str(value)

        # Append the generated element (either <file> or <doc>) directly
        files_section.append(item_element)

    # Convert the ElementTree to a string
    # Use minidom for pretty printing if indent is configured
    try:
        rough_string = ET.tostring(root, "utf-8")
        reparsed = minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    except Exception:
        # Fallback if minidom fails (e.g., with complex CDATA)
        xml_str = ET.tostring(root, encoding="unicode")

    # Writing to file is handled by the caller
    # import logging
    # logger = logging.getLogger(__name__)
    # logger.info(f"XML data generated (will be written to: {config.output})")

    return xml_str
