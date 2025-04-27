import json
from typing import List

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData


def write_json(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Generate JSON output, conditionally including fields based on config."""
    output_data = {}

    # --- Top Level: Repository Overview --- #
    # Includes folder tree
    if (
        config.include_repo_overview
        and config.include_directory_structure
        and folder_tree_str
    ):
        output_data["repository_overview"] = {"directory_structure": folder_tree_str}

    # --- Files Section --- #
    # Always include the 'files' list, but its contents depend on flags
    output_data["files"] = []

    # Process Annotated Code Files
    if annotated_files:
        for ann in annotated_files:
            file_entry = {"type": "code"}  # Always include type

            # Always include file_path
            file_entry["file_path"] = ann.file_path

            # Include language if available (usually always is)
            if ann.language:
                file_entry["language"] = ann.language

            # Include content based on flag (consider raw vs processed based on config?)
            # For JSON, raw content is often more useful unless specifically processed for JSON
            if config.include_code_content and ann.content:
                # Using ann.content (raw) for now. Could use ann.annotated_content if preferred.
                file_entry["content"] = ann.content

            # Include summary if flag is set and summary exists
            if config.include_file_summary and ann.summary:
                # The summary in AnnotatedFileData might just be the basic string one.
                # We might need to regenerate it here using ParsedFileData or store richer summary.
                # For now, use the existing ann.summary
                file_entry["summary"] = (
                    ann.summary
                )  # Or regenerate based on parsed_data?

            # Include declarations if flag is set
            if config.include_declarations_in_summary and ann.declarations:
                # Convert Declaration objects to simple dicts
                file_entry["declarations"] = [
                    decl.model_dump() for decl in ann.declarations
                ]

            # Include imports if flag is set
            if config.include_imports_in_summary and ann.imports:
                file_entry["imports"] = sorted(ann.imports)

            # Include token stats if flag is set
            if config.include_tokens_in_summary and ann.token_stats:
                file_entry["token_stats"] = ann.token_stats.model_dump()

            # Include security issues if flag is set
            if config.include_security_in_summary and ann.security_issues:
                file_entry["security_issues"] = [
                    issue.model_dump() for issue in ann.security_issues
                ]

            # Include tags if flag is set
            if ann.tags:  # Always include tags if they exist?
                file_entry["tags"] = sorted(ann.tags)

            # Add the constructed file entry to the list
            output_data["files"].append(file_entry)

    # Process Documentation Files
    if docs:
        for doc in docs:
            doc_entry = {"type": "documentation"}  # Always include type
            doc_entry["file_path"] = doc.file_path

            if doc.doc_type:
                doc_entry["doc_type"] = doc.doc_type

            # Include content based on flag
            if config.include_doc_content and doc.content:
                doc_entry["content"] = doc.content

            # Add doc entry if it contains more than just type/path
            if len(doc_entry) > 2:
                output_data["files"].append(doc_entry)

    # Generate final JSON string
    # Use model_dump_json for Pydantic objects if applicable, else default encoder
    final_json = json.dumps(
        output_data, indent=config.json_indent, default=str
    )  # Use default=str for non-serializable

    # Writing to file is handled by the caller (e.g., cli_entry_point)
    # logger = logging.getLogger(__name__)
    # logger.info(f"JSON data generated (will be written to: {config.output})")

    return final_json
