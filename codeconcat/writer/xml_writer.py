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
