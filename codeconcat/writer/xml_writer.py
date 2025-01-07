"""XML writer for CodeConcat output."""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from xml.dom import minidom

from codeconcat.base_types import AnnotatedFileData, ParsedDocData, ParsedFileData


def write_xml(
    code_files: List[ParsedFileData],
    doc_files: List[ParsedDocData],
    file_annotations: Dict[str, AnnotatedFileData],
    folder_tree: Optional[str] = None,
) -> str:
    """Write the concatenated code and docs to an XML file."""

    root = ET.Element("codeconcat")

    # Add metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "total_files").text = str(len(code_files) + len(doc_files))
    ET.SubElement(metadata, "code_files").text = str(len(code_files))
    ET.SubElement(metadata, "doc_files").text = str(len(doc_files))

    # Add folder tree if present
    if folder_tree:
        tree_elem = ET.SubElement(root, "folder_tree")
        tree_elem.text = folder_tree

    # Add code files
    code_section = ET.SubElement(root, "code_files")
    for file in code_files:
        file_elem = ET.SubElement(code_section, "file")
        ET.SubElement(file_elem, "path").text = file.file_path
        ET.SubElement(file_elem, "language").text = file.language

        # Add annotations if available
        annotation = file_annotations.get(file.file_path)
        if annotation:
            annotations_elem = ET.SubElement(file_elem, "annotations")
            if annotation.summary:
                ET.SubElement(annotations_elem, "summary").text = annotation.summary
            if annotation.tags:
                tags_elem = ET.SubElement(annotations_elem, "tags")
                for tag in annotation.tags:
                    ET.SubElement(tags_elem, "tag").text = tag

        # Add code content with CDATA to preserve formatting
        content_elem = ET.SubElement(file_elem, "content")
        content_elem.text = f"<![CDATA[{file.content}]]>"

    # Add doc files
    if doc_files:
        docs_section = ET.SubElement(root, "doc_files")
        for doc in doc_files:
            doc_elem = ET.SubElement(docs_section, "file")
            ET.SubElement(doc_elem, "path").text = doc.file_path
            ET.SubElement(doc_elem, "format").text = doc.format
            content_elem = ET.SubElement(doc_elem, "content")
            content_elem.text = f"<![CDATA[{doc.content}]]>"

    # Convert to string with pretty printing
    xml_str = ET.tostring(root, encoding="unicode")
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

    return pretty_xml
