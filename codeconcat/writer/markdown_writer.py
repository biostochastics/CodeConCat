import os
import random
from typing import Dict, List

import tiktoken
from halo import Halo

from codeconcat.base_types import (
    PROGRAMMING_QUOTES,
    AnnotatedFileData,
    CodeConCatConfig,
    ParsedDocData,
    ParsedFileData,
)
from codeconcat.processor.content_processor import (
    generate_directory_structure,
    generate_file_summary,
    process_file_content,
)
from codeconcat.writer.ai_context import generate_ai_preamble


def count_tokens(text: str) -> int:
    """Count tokens using GPT-4 tokenizer (cl100k_base)."""
    try:
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception as e:
        print(f"Warning: Tiktoken encoding failed ({str(e)}), falling back to word count")
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
            output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")
            current_line = "|  " + word
        else:
            if current_line == "|  ":
                current_line += word
            else:
                current_line += " " + word
    output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")

    output_lines.extend([empty_line, top_border])

    # Print everything
    print("\n".join(output_lines))
    print(f"\nQuote tokens (GPT-4): {quote_tokens:,}")
    if total_output_tokens:
        print(f"Total CodeConcat output tokens (GPT-4): {total_output_tokens:,}")


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


def write_markdown(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Write the concatenated code and docs to a markdown file."""
    spinner = Halo(text="Generating CodeConcat output", spinner="dots")
    spinner.start()

    output_chunks = []
    output_chunks.append("# CodeConCat Output\n\n")

    # Add AI-friendly preamble only if enabled
    if not config.disable_ai_context:
        spinner.text = "Generating AI preamble"
        parsed_files = [
            ParsedFileData(
                file_path=ann.file_path, language=ann.language, content=ann.content, declarations=[]
            )
            for ann in annotated_files
        ]
        output_chunks.append(generate_ai_preamble(parsed_files, docs, {}))

    # Add directory structure if configured
    if config.include_directory_structure:
        spinner.text = "Generating directory structure"
        output_chunks.append("## Directory Structure\n")
        output_chunks.append("```\n")
        all_files = [f.file_path for f in annotated_files] + [d.file_path for d in docs]
        dir_structure = generate_directory_structure(all_files)
        output_chunks.append(dir_structure)
        output_chunks.append("\n```\n\n")
    elif folder_tree_str:  # Fallback to provided folder tree
        output_chunks.append("## Folder Tree\n")
        output_chunks.append("```\n")
        output_chunks.append(folder_tree_str)
        output_chunks.append("\n```\n\n")

    # Create a map of doc files by base name for merging
    doc_map = {}
    merged_docs = set()  # Track which docs have been merged
    if config.merge_docs:
        for doc in docs:
            base_name = os.path.splitext(os.path.basename(doc.file_path))[0].lower()
            doc_map[base_name] = doc

    # Process code files
    if annotated_files:
        spinner.text = "Processing code files"
        output_chunks.append("## Code Files\n\n")
        for i, ann in enumerate(annotated_files, 1):
            spinner.text = f"Processing code file {i}/{len(annotated_files)}: {ann.file_path}"
            output_chunks.append(f"### File: {ann.file_path}\n")

            is_test_config = is_test_or_config_file(ann.file_path)

            # Add file summary if enabled or if it's a test/config file
            if config.include_file_summary or is_test_config:
                spinner.text = "Generating file summary"
                summary = generate_file_summary(
                    ParsedFileData(
                        file_path=ann.file_path,
                        language=ann.language,
                        content=ann.content,
                        declarations=[],
                    )
                )
                output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")

            # For test/config files, only show summary
            # For implementation files, show full content
            if not is_test_config and ann.content:
                spinner.text = "Processing file content"
                processed_content = process_file_content(ann.content, config)
                output_chunks.append(f"```{ann.language}\n{processed_content}\n```\n")

                # Add annotated content only if it provides additional analysis
                if ann.annotated_content:
                    # Extract only the analysis parts that aren't in the original content
                    analysis_lines = []
                    for line in ann.annotated_content.split("\n"):
                        # Skip lines that are just code snippets
                        if not line.strip() or line.strip() in ann.content:
                            continue
                        # Keep analysis comments and insights
                        if (
                            line.startswith("#")
                            or "TODO" in line
                            or "NOTE" in line
                            or "FIXME" in line
                        ):
                            analysis_lines.append(line)

                    if analysis_lines:
                        output_chunks.append("\n#### Analysis Notes\n")
                        output_chunks.append("\n".join(analysis_lines))
                        output_chunks.append("\n")

            # If merge_docs is enabled, try to find and merge related doc content
            if config.merge_docs:
                base_name = os.path.splitext(os.path.basename(ann.file_path))[0].lower()
                if base_name in doc_map:
                    doc = doc_map[base_name]
                    output_chunks.append("\n### Associated Documentation\n")
                    output_chunks.append(doc.content)
                    output_chunks.append("\n")
                    merged_docs.add(doc.file_path)

            output_chunks.append("\n---\n")

    # Add remaining docs section if there are unmerged docs
    remaining_docs = [doc for doc in docs if doc.file_path not in merged_docs]
    if remaining_docs:
        spinner.text = "Processing documentation files"
        output_chunks.append("## Documentation\n\n")
        for i, doc in enumerate(remaining_docs, 1):
            spinner.text = f"Processing doc file {i}/{len(remaining_docs)}: {doc.file_path}"
            output_chunks.append(f"### File: {doc.file_path}\n")
            if config.include_file_summary:
                spinner.text = "Generating file summary"
                summary = generate_file_summary(
                    ParsedFileData(
                        file_path=doc.file_path,
                        language="markdown",
                        content=doc.content,
                        declarations=[],
                    )
                )
                output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
            output_chunks.append(doc.content)
            output_chunks.append("\n---\n")

    spinner.text = "Finalizing output"
    final_str = "".join(output_chunks)

    # Count tokens for the entire output
    spinner.text = "Counting tokens"
    output_tokens = count_tokens(final_str)

    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_str)
        # Add token count information at the end
        f.write("\n\n## Token Statistics\n")
        f.write(f"Total CodeConcat output tokens (GPT-4): {output_tokens:,}\n")

    spinner.succeed("CodeConcat output generated successfully")
    print(f"[CodeConCat] Markdown output written to: {config.output}")

    # Print quote with ASCII art, passing the total output tokens
    print_quote_with_ascii(output_tokens)

    return final_str
