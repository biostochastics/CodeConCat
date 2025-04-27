import os
import random
import re
from typing import List
from halo import Halo
import tiktoken
import logging  # Added import
from tqdm import tqdm  # Added import

from ..base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    ParsedDocData,
    ParsedFileData,
    Declaration,
    PROGRAMMING_QUOTES,
)
from codeconcat.processor.content_processor import (
    generate_file_summary,
    process_file_content,
)
from codeconcat.writer.ai_context import generate_ai_preamble

logger = logging.getLogger(__name__)  # Initialized logger


def count_tokens(text: str) -> int:
    """Count tokens using GPT-4 tokenizer (cl100k_base)."""
    try:
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception as e:
        logger.info(
            f"Warning: Tiktoken encoding failed ({str(e)}), falling back to word count"
        )
        return len(text.split())


def print_quote_with_ascii(total_output_tokens: int = None):
    """Print a random programming quote with ASCII art frame."""
    quote = random.choice(PROGRAMMING_QUOTES)
    quote_tokens = count_tokens(quote)

    # Calculate width for the ASCII art frame
    width = max(len(line) for line in quote.split("\n")) + 4

    # ASCII art frame
    top_border = "+" + "=" * (width - 2) + "+"
    empty_line = "|" + " " * (width - 2) + "|"

    # Build the complete output string
    output_lines = ["\n[CodeConCat] Meow:", top_border, empty_line]

    # Word wrap the quote to fit in the frame
    words = quote.split()
    current_line = "|  "
    for word in words:
        if len(current_line) + len(word) + 1 > width - 2:
            output_lines.append(
                current_line + " " * (width - len(current_line) - 1) + "|"
            )
            current_line = "|  " + word
        else:
            if current_line == "|  ":
                current_line += word
            else:
                current_line += " " + word
    output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")

    output_lines.extend([empty_line, top_border])

    # Print everything
    logger.info("\n".join(output_lines))
    logger.info(f"\nQuote tokens (GPT-4): {quote_tokens:,}")
    if total_output_tokens:
        logger.info(f"Total CodeConcat output tokens (GPT-4): {total_output_tokens:,}")


def is_test_or_config_file(file_path: str) -> bool:
    """Check if a file is a test or configuration file."""
    file_name = os.path.basename(file_path).lower()
    return (
        file_name.startswith("test_")
        or file_name == "setup.py"
        or file_name == "conftest.py"
        or file_name.endswith("config.py")
        or "tests/" in file_path
    )


def _generate_anchor_name(file_path: str, decl: Declaration) -> str:
    """Generate a sanitized, unique anchor name for a declaration."""
    # Normalize file path: remove leading './', replace slashes and dots
    norm_path = file_path.lstrip("./").replace("/", "_").replace(".", "_")
    # Sanitize declaration name: keep alphanumeric, hyphen, underscore
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "", decl.name)
    # Combine parts
    anchor = f"symbol-{norm_path}-{decl.kind}-{safe_name}".lower()
    return anchor


def write_markdown(
    annotated_files: List[AnnotatedFileData],
    parsed_files: List[ParsedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Write the concatenated code and docs to a markdown file, respecting config flags."""
    spinner = Halo(text="Generating Markdown output", spinner="dots")
    spinner.start()

    # Create a map for easy lookup of parsed_files by path for summaries
    parsed_files_map = {pf.file_path: pf for pf in parsed_files}

    output_chunks = []
    output_chunks.append("# CodeConCat Output\n\n")

    # --- Section: Repository Overview --- #
    # This includes AI preamble and potentially the folder tree
    if config.include_repo_overview:
        spinner.text = "Generating repository overview"
        # Generate AI preamble (if not disabled implicitly by preset/flag)
        # We might need a more specific flag like 'include_ai_preamble' later
        # For now, tie it to repo overview
        if not config.disable_ai_context:
            # Pass parsed_files instead of annotated_files if preamble needs parsed data
            ai_preamble = generate_ai_preamble(parsed_files, docs, config)
            if ai_preamble:
                output_chunks.append(ai_preamble)
                output_chunks.append("\n")

        # Add directory structure if configured and provided
        if config.include_directory_structure and folder_tree_str:
            spinner.text = "Adding directory structure"
            output_chunks.append("## Directory Structure\n")
            output_chunks.append(f"```\n{folder_tree_str}\n```\n\n")
        output_chunks.append("---\n\n")

    # --- Section: File Index --- #
    if config.include_file_index:
        spinner.text = "Generating file index"
        output_chunks.append("## File Index\n")
        # Sort files if requested
        files_to_index = (
            sorted(annotated_files, key=lambda x: x.file_path)
            if config.sort_files
            else annotated_files
        )
        for ann_file in files_to_index:
            # Simple link to the file section using basename as anchor (needs improvement for uniqueness)
            base_name = os.path.basename(ann_file.file_path)
            anchor = f"#{base_name.replace('.', '')}"
            output_chunks.append(f"- [{ann_file.file_path}]({anchor})\n")
        output_chunks.append("\n---\n\n")

    # --- Section: Documentation (If not merged) --- #
    merged_docs = set()
    if not config.merge_docs and docs:
        spinner.text = "Adding documentation files"
        output_chunks.append("## Documentation Files\n\n")
        doc_iterator = tqdm(
            docs,
            desc="Processing docs",
            unit="doc",
            disable=config.disable_progress_bar,
        )
        for doc in doc_iterator:
            output_chunks.append(f"### `{doc.file_path}`\n")
            # Optionally include summary for docs if flag allows
            if config.include_file_summary:
                # Create temporary ParsedFileData for summary generation
                temp_parsed_doc = ParsedFileData(
                    file_path=doc.file_path,
                    language="markdown",
                    content=doc.content,
                    declarations=[],
                    imports=[],
                    token_stats=None,
                    security_issues=[],
                )
                summary = generate_file_summary(temp_parsed_doc, config)
                if summary:
                    output_chunks.append("**Summary:**\n")
                    output_chunks.append(summary)
                    output_chunks.append("\n")

            output_chunks.append(f"```markdown\n{doc.content}\n```\n\n")
            merged_docs.add(doc.file_path)
        output_chunks.append("---\n\n")

    # --- Section: Code Files --- #
    output_chunks.append("## Code Files\n\n")
    # Sort files if requested
    files_to_process = (
        sorted(annotated_files, key=lambda x: x.file_path)
        if config.sort_files
        else annotated_files
    )

    file_iterator = tqdm(
        files_to_process,
        desc="Processing code files",
        unit="file",
        disable=config.disable_progress_bar,
    )
    for i, ann in enumerate(file_iterator, 1):
        spinner.text = (
            f"Processing code file {i}/{len(files_to_process)}: {ann.file_path}"
        )

        # Create a file-specific anchor (simple version)
        base_name = os.path.basename(ann.file_path)
        file_anchor = base_name.replace(".", "")
        output_chunks.append(f"### `{ann.file_path}` {{#{file_anchor}}}\n")

        # --- File Summary Section --- #
        if config.include_file_summary:
            spinner.text = f"Generating summary: {ann.file_path}"
            # Retrieve the corresponding ParsedFileData for full details
            current_parsed_file = parsed_files_map.get(ann.file_path)
            if current_parsed_file:
                summary = generate_file_summary(current_parsed_file, config)
                if summary:
                    # Indent summary slightly or use blockquote?
                    output_chunks.append("> **File Summary:**\n")
                    # Indent each line of the summary for blockquote effect
                    indented_summary = "\n".join(
                        [f"> {line}" for line in summary.splitlines()]
                    )
                    output_chunks.append(indented_summary)
                    output_chunks.append("\n\n")
            else:
                logger.warning(
                    f"Could not find parsed data to generate summary for {ann.file_path}"
                )

        # --- Code Block Section --- #
        if ann.content:
            spinner.text = f"Processing content: {ann.file_path}"
            # Process content based on config (remove comments, add line numbers etc.)
            # Note: process_file_content itself needs to be aware of config flags
            processed_content = process_file_content(ann.content, config)

            output_chunks.append(f"```{ann.language}\n{processed_content}\n```\n\n")
        else:
            output_chunks.append("_(File content is empty or not included)_\n\n")

        # --- Analysis Section (Legacy/Optional?) --- #
        # This used to hold declaration lists etc. - decide if needed alongside structured summary
        # if not config.disable_annotations and ann.annotated_content and config.output_preset == 'full':
        #     output_chunks.append("\n#### Analysis\n")
        #     output_chunks.append(ann.annotated_content)
        #     output_chunks.append("\n")

        # --- Merged Documentation Section --- #
        if config.merge_docs:
            # Find associated doc based on file name (needs robust matching)
            base_name = os.path.splitext(os.path.basename(ann.file_path))[0].lower()
            related_doc = None
            for doc in docs:
                doc_base_name = os.path.splitext(os.path.basename(doc.file_path))[
                    0
                ].lower()
                # Simple matching logic, improve later
                if base_name == doc_base_name and doc.file_path not in merged_docs:
                    related_doc = doc
                    break

            if related_doc:
                spinner.text = f"Merging doc: {related_doc.file_path}"
                output_chunks.append("#### Associated Documentation\n")
                output_chunks.append(f"**Source:** `{related_doc.file_path}`\n")
                output_chunks.append(f"```markdown\n{related_doc.content}\n```\n\n")
                merged_docs.add(related_doc.file_path)

        output_chunks.append("---\n")

    # --- Section: Remaining Unmerged Docs (if merging was enabled) --- #
    if config.merge_docs:
        remaining_docs = [doc for doc in docs if doc.file_path not in merged_docs]
        if remaining_docs:
            spinner.text = "Adding remaining documentation files"
            output_chunks.append("## Remaining Documentation\n\n")
            doc_iterator = tqdm(
                remaining_docs,
                desc="Processing remaining docs",
                unit="doc",
                disable=config.disable_progress_bar,
            )
            for doc in doc_iterator:
                output_chunks.append(f"### `{doc.file_path}`\n")
                if config.include_file_summary:
                    temp_parsed_doc = ParsedFileData(
                        file_path=doc.file_path,
                        language="markdown",
                        content=doc.content,
                        declarations=[],
                        imports=[],
                        token_stats=None,
                        security_issues=[],
                    )
                    summary = generate_file_summary(temp_parsed_doc, config)
                    if summary:
                        output_chunks.append("> **File Summary:**\n")
                        indented_summary = "\n".join(
                            [f"> {line}" for line in summary.splitlines()]
                        )
                        output_chunks.append(indented_summary)
                        output_chunks.append("\n\n")

                output_chunks.append(f"```markdown\n{doc.content}\n```\n\n")
            output_chunks.append("---\n")

    spinner.text = "Finalizing output"
    final_str = "".join(output_chunks)

    # Count tokens for the entire output
    spinner.text = "Counting tokens"
    output_tokens = count_tokens(final_str)

    # Add token count information at the end of the string
    final_str += "\n\n<!-- Token Count -->\n"
    final_str += (
        f"<!-- Total CodeConCat output tokens (cl100k_base): {output_tokens:,} -->\n"
    )

    spinner.succeed("Markdown generation complete")
    # Logging is handled by the caller (e.g., run_codeconcat)

    # Print quote with ASCII art, passing the total output tokens
    print_quote_with_ascii(output_tokens)

    return final_str
