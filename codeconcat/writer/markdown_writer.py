from typing import List, Dict
import random
import tiktoken
from halo import Halo
from codeconcat.base_types import (
    AnnotatedFileData, ParsedDocData, CodeConCatConfig, 
    ParsedFileData, PROGRAMMING_QUOTES
)
from codeconcat.writer.ai_context import generate_ai_preamble
from codeconcat.processor.content_processor import process_file_content, generate_file_summary, generate_directory_structure

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
    width = max(len(line) for line in quote.split('\n')) + 4
    
    # ASCII art frame
    top_border = "+" + "=" * (width - 2) + "+"
    empty_line = "|" + " " * (width - 2) + "|"
    
    # Build the complete output string
    output_lines = [
        "\n[CodeConCat] Meow:",
        top_border,
        empty_line
    ]
    
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
    
    output_lines.extend([
        empty_line,
        top_border
    ])
    
    # Print everything
    print("\n".join(output_lines))
    print(f"\nQuote tokens (GPT-4): {quote_tokens:,}")
    if total_output_tokens:
        print(f"Total CodeConcat output tokens (GPT-4): {total_output_tokens:,}")

def write_markdown(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = ""
) -> str:
    spinner = Halo(text='Generating CodeConcat output', spinner='dots')
    spinner.start()
    
    output_chunks = []
    output_chunks.append("# CodeConCat Output\n\n")

    # Add AI-friendly preamble
    spinner.text = 'Generating AI preamble'
    parsed_files = [ParsedFileData(
        file_path=ann.file_path,
        language=ann.language,
        content=ann.content,
        declarations=[]
    ) for ann in annotated_files]
    output_chunks.append(generate_ai_preamble(parsed_files, docs, {}))

    # Add directory structure if configured
    if config.include_directory_structure:
        spinner.text = 'Generating directory structure'
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
        spinner.text = 'Processing code files'
        output_chunks.append("## Code Files\n\n")
        for i, ann in enumerate(annotated_files, 1):
            spinner.text = f'Processing code file {i}/{len(annotated_files)}: {ann.file_path}'
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
        spinner.text = 'Processing documentation files'
        output_chunks.append("## Documentation\n\n")
        for i, doc in enumerate(docs, 1):
            spinner.text = f'Processing doc file {i}/{len(docs)}: {doc.file_path}'
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

    spinner.text = 'Finalizing output'
    final_str = "".join(output_chunks)

    # Count tokens for the entire output
    spinner.text = 'Counting tokens'
    output_tokens = count_tokens(final_str)
    
    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_str)
        # Add token count information at the end
        f.write("\n\n## Token Statistics\n")
        f.write(f"Total CodeConcat output tokens (GPT-4): {output_tokens:,}\n")

    spinner.succeed('CodeConcat output generated successfully')
    print(f"[CodeConCat] Markdown output written to: {config.output}")
    
    # Print quote with ASCII art, passing the total output tokens
    print_quote_with_ascii(output_tokens)
    
    return final_str
