from typing import List, Dict
import random
import tiktoken
from codeconcat.base_types import (
    AnnotatedFileData, ParsedDocData, CodeConCatConfig, 
    ParsedFileData, PROGRAMMING_QUOTES
)
from codeconcat.writer.ai_context import generate_ai_preamble
from codeconcat.processor.content_processor import process_file_content, generate_file_summary, generate_directory_structure

def count_tokens(text: str) -> Dict[str, int]:
    """Count tokens for different models."""
    try:
        gpt4_enc = tiktoken.encoding_for_model("gpt-4")
        gpt3_enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        return {
            "GPT-4": len(gpt4_enc.encode(text)),
            "GPT-3.5": len(gpt3_enc.encode(text)),
        }
    except:
        # Fallback if tiktoken fails
        return {
            "GPT-4": len(text.split()),
            "GPT-3.5": len(text.split()),
        }

def print_quote_with_ascii():
    """Print a random programming quote with ASCII art frame."""
    quote = random.choice(PROGRAMMING_QUOTES)
    tokens = count_tokens(quote)
    
    # Calculate width for the ASCII art frame
    width = max(len(line) for line in quote.split('\n')) + 4
    
    # ASCII art frame
    top_border = "+" + "=" * (width - 2) + "+"
    empty_line = "|" + " " * (width - 2) + "|"
    
    # Print the quote in a nice ASCII frame
    print("\n[CodeConCat] Meow:")
    print(top_border)
    print(empty_line)
    
    # Word wrap the quote to fit in the frame
    words = quote.split()
    current_line = "|  "
    for word in words:
        if len(current_line) + len(word) + 1 > width - 2:
            print(current_line + " " * (width - len(current_line) - 1) + "|")
            current_line = "|  " + word
        else:
            if current_line == "|  ":
                current_line += word
            else:
                current_line += " " + word
    print(current_line + " " * (width - len(current_line) - 1) + "|")
    
    print(empty_line)
    print(top_border)
    
    # Print token counts
    print(f"\nToken counts: {', '.join(f'{model}: {count}' for model, count in tokens.items())}")


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
            output_chunks.append(f"### File: {ann.file_path}\n")
            if config.include_file_summary:
                summary = generate_file_summary(ParsedFileData(
                    file_path=ann.file_path,
                    language=ann.language,
                    content=ann.content,
                    declarations=[]
                ))
                output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
            
            processed_content = process_file_content(ann.content, config)
            output_chunks.append(f"```{ann.language}\n{processed_content}\n```\n")
            output_chunks.append("\n---\n")

    # Write docs if any
    if docs:
        output_chunks.append("## Documentation\n\n")
        for doc in docs:
            output_chunks.append(f"### File: {doc.file_path}\n")
            if config.include_file_summary:
                summary = generate_file_summary(ParsedFileData(
                    file_path=doc.file_path,
                    language=doc.doc_type,
                    content=doc.content,
                    declarations=[]
                ))
                output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
                
            processed_content = process_file_content(doc.content, config)
            output_chunks.append(f"```{doc.doc_type}\n{processed_content}\n```\n")
            output_chunks.append("\n---\n")

    final_str = "".join(output_chunks)

    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_str)

    print(f"[CodeConCat] Markdown output written to: {config.output}")
    
    # Print quote with ASCII art
    print_quote_with_ascii()
    
    return final_str
