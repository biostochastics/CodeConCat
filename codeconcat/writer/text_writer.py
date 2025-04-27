"""Plain text writer for CodeConcat output."""

import logging
from typing import List, Union

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    ParsedDocData,
)

logger = logging.getLogger(__name__)


def write_text(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Write the concatenated code and docs to a plain text string, respecting config flags."""
    output_lines = []

    # --- Repository Overview --- #
    if config.include_repo_overview:
        output_lines.append("#" * 80)
        output_lines.append("# Repository Overview")
        output_lines.append("#" * 80)
        if config.include_directory_structure and folder_tree_str:
            output_lines.append("\n## Directory Structure:")
            output_lines.append(folder_tree_str)
        output_lines.append("\n")

    # --- File Index --- #
    if config.include_file_index:
        output_lines.append("#" * 80)
        output_lines.append("# File Index")
        output_lines.append("#" * 80)
        all_files_for_index = sorted(
            [ann.file_path for ann in annotated_files] + [d.file_path for d in docs]
        )
        for i, file_path in enumerate(all_files_for_index):
            output_lines.append(f"{i + 1}. {file_path}")
        output_lines.append("\n")

    # --- Files Section --- #
    output_lines.append("#" * 80)
    output_lines.append("# File Content")
    output_lines.append("#" * 80)
    output_lines.append("\n")

    files_to_process: List[Union[AnnotatedFileData, ParsedDocData]] = []
    if annotated_files:
        files_to_process.extend(annotated_files)
    if docs:
        files_to_process.extend(docs)

    if config.sort_files:
        files_to_process.sort(key=lambda x: x.file_path)

    for i, file_data in enumerate(files_to_process):
        output_lines.append("-" * 80)
        output_lines.append(f"File: {file_data.file_path}")
        output_lines.append("-" * 80)

        if isinstance(file_data, AnnotatedFileData):
            if file_data.language:
                output_lines.append(f"Language: {file_data.language}")

            # Summary
            if config.include_file_summary and file_data.summary:
                output_lines.append("\n## Summary:")
                output_lines.append(file_data.summary)

            # Declarations
            if config.include_declarations_in_summary and file_data.declarations:
                output_lines.append("\n## Declarations:")
                for decl in file_data.declarations:
                    output_lines.append(
                        f"  - {decl.kind}: {decl.name} (Lines: {decl.start_line}-{decl.end_line})"
                    )

            # Imports
            if config.include_imports_in_summary and file_data.imports:
                output_lines.append("\n## Imports:")
                for imp in sorted(file_data.imports):
                    output_lines.append(f"  - {imp}")

            # Token Stats
            if config.include_tokens_in_summary and file_data.token_stats:
                output_lines.append("\n## Token Stats:")
                output_lines.append(
                    f"  - Input Tokens: {file_data.token_stats.input_tokens}"
                )
                output_lines.append(
                    f"  - Output Tokens: {file_data.token_stats.output_tokens}"
                )
                output_lines.append(
                    f"  - Total Tokens: {file_data.token_stats.total_tokens}"
                )

            # Security Issues
            if config.include_security_in_summary and file_data.security_issues:
                output_lines.append("\n## Security Issues:")
                for issue in file_data.security_issues:
                    severity_val = (
                        issue.severity.value
                        if hasattr(issue.severity, "value")
                        else str(issue.severity)
                    )
                    output_lines.append(
                        f"  - Severity: {severity_val}, Line: {issue.line_number}, Description: {issue.description}"
                    )

            # Tags
            if file_data.tags:
                output_lines.append("\n## Tags:")
                output_lines.append(f"  - {', '.join(sorted(file_data.tags))}")

            # Content
            if config.include_code_content and file_data.content:
                output_lines.append("\n## Content:")
                output_lines.append(file_data.content)

        elif isinstance(file_data, ParsedDocData):
            if file_data.doc_type:
                output_lines.append(f"Type: {file_data.doc_type}")
            if config.include_doc_content and file_data.content:
                output_lines.append("\n## Content:")
                output_lines.append(file_data.content)

        output_lines.append("\n")  # Add a newline after each file section

    output_string = "\n".join(output_lines)
    logger.debug(f"Generated text output string of length {len(output_string)}")
    return output_string
