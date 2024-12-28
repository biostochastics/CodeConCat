"""
markdown_writer.py

Writes annotated code plus doc files into a single Markdown file if merge_docs is True.
Otherwise, you could adapt it to write separate doc files.
"""

from typing import List
from codeconcat.types import AnnotatedFileData, ParsedDocData, CodeConCatConfig

def write_markdown(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig
) -> None:
    with open(config.output, "w", encoding="utf-8") as f:
        f.write("# CodeConCat Output\n\n")

        # Write annotated code
        for ann in annotated_files:
            f.write(ann.annotated_content)
            f.write("\n---\n")

        if config.docs and config.merge_docs and docs:
            f.write("\n## Documentation\n\n")
            for doc in docs:
                f.write(f"### Doc File: {doc.file_path}\n")
                # For readability, wrap doc content in triple backticks or blockquotes
                f.write(f"```\n{doc.content}\n```\n\n")
                f.write("---\n")

    print(f"[CodeConCat] Markdown output written to: {config.output}")