from typing import List
from codeconcat.types import AnnotatedFileData, ParsedDocData, CodeConCatConfig

def write_markdown(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = ""
) -> str:
    output_chunks = []
    output_chunks.append("# CodeConCat Output\n\n")

    if folder_tree_str:
        output_chunks.append("## Folder Tree\n")
        output_chunks.append("```\n")
        output_chunks.append(folder_tree_str)
        output_chunks.append("\n```\n\n")

    for ann in annotated_files:
        output_chunks.append(ann.annotated_content)
        output_chunks.append("\n---\n")

    if config.docs and config.merge_docs and docs:
        output_chunks.append("\n## Documentation\n\n")
        for doc in docs:
            output_chunks.append(f"### Doc File: {doc.file_path}\n")
            output_chunks.append(f"```\n{doc.content}\n```\n\n")
            output_chunks.append("---\n")

    final_str = "".join(output_chunks)

    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_str)

    print(f"[CodeConCat] Markdown output written to: {config.output}")
    return final_str
