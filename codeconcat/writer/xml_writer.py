"""XML writer for CodeConcat output."""

import xml.etree.ElementTree as ET
from typing import List
from xml.dom import minidom

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData


def write_xml(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Write the concatenated code and docs to an XML file."""

    root = ET.Element("codeconcat")

    # Add metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "total_files").text = str(len(annotated_files) + len(docs))
    ET.SubElement(metadata, "code_files").text = str(len(annotated_files))
    ET.SubElement(metadata, "doc_files").text = str(len(docs))

    # Add folder tree if present
    if folder_tree_str:
        tree_elem = ET.SubElement(root, "folder_tree")
        tree_elem.text = folder_tree_str

    # Add code files
    code_section = ET.SubElement(root, "code_files")
    for file in annotated_files:
        file_elem = ET.SubElement(code_section, "file")
        ET.SubElement(file_elem, "path").text = file.file_path
        ET.SubElement(file_elem, "language").text = file.language

        # Add code content with CDATA to preserve formatting
        content_elem = ET.SubElement(file_elem, "content")
        content_elem.text = f"<![CDATA[{file.annotated_content}]]>"

    # Add doc files
    docs_section = ET.SubElement(root, "doc_files")
    for doc in docs:
        doc_elem = ET.SubElement(docs_section, "file")
        ET.SubElement(doc_elem, "path").text = doc.file_path
        ET.SubElement(doc_elem, "type").text = doc.doc_type
        content_elem = ET.SubElement(doc_elem, "content")
        content_elem.text = f"<![CDATA[{doc.content}]]>"

    # Convert to string with pretty printing
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

    # Write to file
    with open(config.output, "w", encoding="utf-8") as f:
        f.write(xml_str)

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[CodeConCat] XML output written to: {config.output}")
    return xml_str
