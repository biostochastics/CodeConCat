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
        all_files_for_index = sorted(
            [ann.file_path for ann in annotated_files] + [d.file_path for d in docs]
        )
        for file_path in all_files_for_index:
            ET.SubElement(file_index, "file", path=file_path)

    # --- Files Section --- #
    files_section = ET.SubElement(root, "files")

    # Add code files
    if annotated_files:
        code_files_elem = ET.SubElement(files_section, "code_files")
        # Sort files if requested
        files_to_process = (
            sorted(annotated_files, key=lambda x: x.file_path)
            if config.sort_files
            else annotated_files
        )
        for file in files_to_process:
            file_elem = ET.SubElement(code_files_elem, "file")
            ET.SubElement(file_elem, "path").text = file.file_path
            if file.language:
                ET.SubElement(file_elem, "language").text = file.language

            # Content
            if config.include_code_content and file.content:
                content_elem = ET.SubElement(file_elem, "content")
                # Use CDATA for code content
                content_elem.text = f"<![CDATA[{file.content}]]>"

            # Summary
            if config.include_file_summary and file.summary:
                summary_elem = ET.SubElement(file_elem, "summary")
                # Use CDATA for summary
                summary_elem.text = f"<![CDATA[{file.summary}]]>"

            # Declarations
            if config.include_declarations_in_summary and file.declarations:
                decls_elem = ET.SubElement(file_elem, "declarations")
                for decl in file.declarations:
                    ET.SubElement(
                        decls_elem,
                        "declaration",
                        kind=decl.kind,
                        name=decl.name,
                        start_line=str(decl.start_line),
                        end_line=str(decl.end_line),
                    )

            # Imports
            if config.include_imports_in_summary and file.imports:
                imports_elem = ET.SubElement(file_elem, "imports")
                for imp in sorted(file.imports):
                    ET.SubElement(imports_elem, "import", name=imp)

            # Token Stats
            if config.include_tokens_in_summary and file.token_stats:
                stats_elem = ET.SubElement(file_elem, "token_stats")
                ET.SubElement(stats_elem, "input_tokens").text = str(
                    file.token_stats.input_tokens
                )
                ET.SubElement(stats_elem, "output_tokens").text = str(
                    file.token_stats.output_tokens
                )
                ET.SubElement(stats_elem, "total_tokens").text = str(
                    file.token_stats.total_tokens
                )

            # Security Issues
            if config.include_security_in_summary and file.security_issues:
                sec_issues_elem = ET.SubElement(file_elem, "security_issues")
                for issue in file.security_issues:
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
                    # Use CDATA for description
                    desc_elem.text = f"<![CDATA[{issue.description}]]>"

            # Tags
            if file.tags:
                tags_elem = ET.SubElement(file_elem, "tags")
                for tag in sorted(file.tags):
                    ET.SubElement(tags_elem, "tag", name=tag)

    # Add doc files
    if docs:
        docs_section = ET.SubElement(files_section, "doc_files")
        docs_to_process = (
            sorted(docs, key=lambda x: x.file_path) if config.sort_files else docs
        )
        for doc in docs_to_process:
            doc_elem = ET.SubElement(docs_section, "file")
            ET.SubElement(doc_elem, "path").text = doc.file_path
            if doc.doc_type:
                ET.SubElement(doc_elem, "type").text = doc.doc_type

            # Content
            if config.include_doc_content and doc.content:
                content_elem = ET.SubElement(doc_elem, "content")
                # Use CDATA for documentation content
                content_elem.text = f"<![CDATA[{doc.content}]]>"

    # Convert ElementTree to a pretty-printed string
    # Note: Using CDATA manually bypasses standard escaping, which is intended here
    # for content fields, but means we need to be careful.
    # minidom can sometimes struggle with CDATA during pretty printing, but let's try.
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
