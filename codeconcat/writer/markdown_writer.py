from typing import List, Dict
from codeconcat.types import AnnotatedFileData, ParsedDocData, CodeConCatConfig, ParsedFileData
from codeconcat.writer.ai_context import generate_ai_preamble
from codeconcat.processor.content_processor import process_file_content, generate_file_summary, generate_directory_structure

def write_markdown(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = ""
) -> str:
    output_chunks = []
    output_chunks.append("# CodeConCat Output\n\n")

    # Add AI-friendly preamble
    parsed_files = [ParsedFileData(
        file_path=ann.file_path,
        language=ann.language,
        content=ann.content,
        declarations=[]
    ) for ann in annotated_files]
    output_chunks.append(generate_ai_preamble(parsed_files, docs, {}))

    # Add directory structure if configured
    if config.include_directory_structure:
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

    # Write code files if any
    if annotated_files:
        output_chunks.append("## Code Files\n\n")
        for ann in annotated_files:
            if config.include_file_summary:
                summary = generate_file_summary(ParsedFileData(
                    file_path=ann.file_path,
                    language=ann.language,
                    content=ann.content,
                    declarations=[]
                ))
                output_chunks.append(f"### File Summary\n```\n{summary}\n```\n\n")
            
            processed_content = process_file_content(ann.content, config)
            output_chunks.append(processed_content)
            output_chunks.append("\n---\n")

    # Write docs if any
    if docs:
        output_chunks.append("## Documentation\n\n")
        for doc in docs:
            output_chunks.append(f"### Doc File: {doc.file_path}\n")
            if config.include_file_summary:
                summary = generate_file_summary(ParsedFileData(
                    file_path=doc.file_path,
                    language=doc.doc_type,
                    content=doc.content,
                    declarations=[]
                ))
                output_chunks.append(f"### File Summary\n```\n{summary}\n```\n\n")
                
            processed_content = process_file_content(doc.content, config)
            output_chunks.append(f"```{doc.doc_type}\n{processed_content}\n```\n\n")
            output_chunks.append("---\n")

    final_str = "".join(output_chunks)

    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_str)

    print(f"[CodeConCat] Markdown output written to: {config.output}")
    return final_str
