# CodeConCat Output

# CodeConcat AI-Friendly Code Summary

This document contains a structured representation of a codebase, organized for AI analysis.

## Repository Structure
```
Total code files: 39
Documentation files: 0

File types:
- py: 38 files
- toml: 1 files
```

## Code Organization
The code is organized into sections, each prefixed with clear markers:
- Directory markers show file organization
- File headers contain metadata and imports
- Annotations provide context about code purpose
- Documentation sections contain project documentation

## Navigation
- Each file begins with '---FILE:' followed by its path
- Each section is clearly delimited with markdown headers
- Code blocks are formatted with appropriate language tags

## Content Summary

---
Begin code content below:
## Folder Tree
```
./
    __init__.py
    base_types.py
    main.py
    pyproject.toml
    types.py
    version.py
    collector/
        __init__.py
        github_collector.py
        local_collector.py
    config/
        __init__.py
        config_loader.py
    parser/
        __init__.py
        doc_extractor.py
        file_parser.py
        language_parsers/
            __init__.py
            base_parser.py
            c_parser.py
            cpp_parser.py
            csharp_parser.py
            go_parser.py
            java_parser.py
            js_ts_parser.py
            julia_parser.py
            php_parser.py
            python_parser.py
            r_parser.py
            rust_parser.py
    processor/
        __init__.py
        content_processor.py
        security_processor.py
        security_types.py
        token_counter.py
    transformer/
        __init__.py
        annotator.py
    writer/
        __init__.py
        ai_context.py
        json_writer.py
        markdown_writer.py
        xml_writer.py
```

## Code Files

__version__ = "0.4.1"

---
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "codeconcat"
version = "1.0.0"  # Alternatively keep version in codeconcat/version.py
description = "An LLM-friendly code aggregator and doc extractor"
authors = [
  { name = "Your Name", email = "you@example.com" }
]
license = "MIT"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
  "pyyaml >= 5.0",
]

[project.scripts]
codeconcat = "codeconcat.main:cli_entry_point"

---

---
"""
types.py

Holds data classes and typed structures used throughout CodeConCat.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from codeconcat.processor.security_types import SecurityIssue


@dataclass
class Declaration:
    """
    Represents a top-level construct in a code file, e.g. a function, class, or symbol.
    Kinds can be: 'function', 'class', 'struct', 'symbol'
    """
    kind: str
    name: str
    start_line: int
    end_line: int


@dataclass
class TokenStats:
    """Token statistics for a file."""
    gpt3_tokens: int
    gpt4_tokens: int
    davinci_tokens: int
    claude_tokens: int


@dataclass
class ParsedFileData:
    """
    Parsed output of a single code file.
    """
    file_path: str
    language: str
    content: str
    declarations: List[Declaration] = field(default_factory=list)
    token_stats: Optional[TokenStats] = None
    security_issues: List[SecurityIssue] = field(default_factory=list)


@dataclass
class AnnotatedFileData:
    """
    A file's annotated content, ready to be written (Markdown/JSON).
    """
    file_path: str
    language: str
    annotated_content: str
    content: str = ""
    summary: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ParsedDocData:
    """
    Represents a doc file, storing raw text + file path + doc type (md, rst, etc.).
    """
    file_path: str
    doc_type: str
    content: str


@dataclass
class CodeConCatConfig:
    """
    Global configuration object. Merged from CLI args + .codeconcat.yml.

    Fields:
      - target_path: local directory or placeholder for GitHub
      - github_url: optional GitHub repository URL
      - github_token: personal access token for private repos
      - github_ref: optional GitHub reference (branch/tag)
      - include_languages / exclude_languages
      - include_paths / exclude_paths: patterns for including/excluding
      - extract_docs: whether to parse docs
      - merge_docs: whether to merge doc content into the same output
      - doc_extensions: list of recognized doc file extensions
      - custom_extension_map: user-specified extension→language
      - output: final file name
      - format: 'markdown' or 'json'
      - max_workers: concurrency
      - disable_tree: whether to disable directory structure
      - disable_copy: whether to disable copying output
      - disable_annotations: whether to disable annotations
      - disable_symbols: whether to disable symbol extraction
      - include_file_summary: whether to include file summaries
      - include_directory_structure: whether to show directory structure
      - remove_comments: whether to remove comments from output
      - remove_empty_lines: whether to remove empty lines
      - show_line_numbers: whether to show line numbers
    """

    # Basic path or GitHub info
    target_path: str = "."
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    github_ref: Optional[str] = None

    # Language filtering
    include_languages: List[str] = field(default_factory=list)
    exclude_languages: List[str] = field(default_factory=list)

    # Path filtering
    include_paths: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)

    # Doc extraction toggles
    extract_docs: bool = False
    merge_docs: bool = False
    doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])

    # Custom extension→language
    custom_extension_map: Dict[str, str] = field(default_factory=dict)

    # Output
    output: str = "code_concat_output.md"
    format: str = "markdown"
    max_workers: int = 4

    # Feature toggles
    disable_tree: bool = False
    disable_copy: bool = False
    disable_annotations: bool = False
    disable_symbols: bool = False

    # Display options
    include_file_summary: bool = False
    include_directory_structure: bool = False
    remove_comments: bool = False
    remove_empty_lines: bool = False
    show_line_numbers: bool = False

---
"""Base types used throughout CodeConcat."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Declaration:
    """
    Represents a top-level construct in a code file, e.g. a function, class, or symbol.
    Kinds can be: 'function', 'class', 'struct', 'symbol'
    """
    kind: str
    name: str
    start_line: int
    end_line: int

@dataclass
class ParsedFileData:
    """
    Parsed output of a single code file.
    """
    file_path: str
    language: str
    content: str
    declarations: List[Declaration] = field(default_factory=list)
    token_stats: Optional['TokenStats'] = None  # Forward reference
    security_issues: List['SecurityIssue'] = field(default_factory=list)  # Forward reference

@dataclass
class CodeConCatConfig:
    """Global configuration object."""
    target_path: str = "."
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    github_ref: Optional[str] = None
    include_languages: List[str] = field(default_factory=list)
    exclude_languages: List[str] = field(default_factory=list)
    include_paths: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)
    extract_docs: bool = False
    merge_docs: bool = False
    doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])
    custom_extension_map: Dict[str, str] = field(default_factory=dict)
    output: str = "code_concat_output.md"
    format: str = "markdown"
    max_workers: int = 4
    disable_tree: bool = False
    disable_copy: bool = False
    disable_annotations: bool = False
    disable_symbols: bool = False
    include_file_summary: bool = False
    include_directory_structure: bool = False
    remove_comments: bool = False
    remove_empty_lines: bool = False
    show_line_numbers: bool = False

---
import argparse
import sys
from typing import List
import os
import logging

from codeconcat.config.config_loader import load_config
from codeconcat.collector.local_collector import collect_local_files, should_skip_dir, should_include_file
from codeconcat.collector.github_collector import collect_github_files
from codeconcat.parser.file_parser import parse_code_files
from codeconcat.parser.doc_extractor import extract_docs
from codeconcat.transformer.annotator import annotate
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.xml_writer import write_xml

from codeconcat.types import CodeConCatConfig, AnnotatedFileData, ParsedDocData


def cli_entry_point():
    parser = argparse.ArgumentParser(
        prog="codeconcat",
        description="CodeConCat - An LLM-friendly code aggregator and doc extractor."
    )

    parser.add_argument("target_path", nargs="?", default=".")
    parser.add_argument("--github", help="GitHub URL or shorthand (e.g., 'owner/repo')", default=None)
    parser.add_argument("--github-token", help="GitHub personal access token", default=None)
    parser.add_argument("--ref", help="Branch, tag, or commit hash for GitHub repo", default=None)

    parser.add_argument("--docs", action="store_true", help="Enable doc extraction")
    parser.add_argument("--merge-docs", action="store_true", help="Merge doc content with code output")

    parser.add_argument("--output", default="code_concat_output.md", help="Output file name")
    parser.add_argument("--format", choices=["markdown", "json", "xml"], default="markdown", help="Output format")

    parser.add_argument("--include", nargs="*", default=[], help="Glob patterns to include")
    parser.add_argument("--exclude", nargs="*", default=[], help="Glob patterns to exclude")
    parser.add_argument("--include-languages", nargs="*", default=[], help="Only include these languages")
    parser.add_argument("--exclude-languages", nargs="*", default=[], help="Exclude these languages")

    parser.add_argument("--max-workers", type=int, default=4, help="Number of worker threads")
    parser.add_argument("--init", action="store_true", help="Initialize default configuration file")

    parser.add_argument("--no-tree", action="store_true", help="Disable folder tree generation (enabled by default)")
    parser.add_argument("--no-copy", action="store_true", help="Disable copying output to clipboard (enabled by default)")
    parser.add_argument("--no-annotations", action="store_true", help="Disable code annotations (enabled by default)")
    parser.add_argument("--no-symbols", action="store_true", help="Disable symbol extraction (enabled by default)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Initialize logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Handle initialization request
    if args.init:
        create_default_config()
        print("[CodeConCat] Created default configuration file: .codeconcat.yml")
        sys.exit(0)

    # Load config, with CLI args taking precedence
    cli_args = vars(args)
    logging.debug("CLI args: %s", cli_args)  # Debug print
    config = load_config(cli_args)

    try:
        run_codeconcat(config)
    except Exception as e:
        print(f"[CodeConCat] Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def create_default_config():
    """Create a default .codeconcat.yml configuration file."""
    if os.path.exists(".codeconcat.yml"):
        print("Configuration file already exists. Remove it first to create a new one.")
        return

    config_content = """# CodeConCat Configuration

# Path filtering
include_paths:
  # Add glob patterns to include specific files/directories
  # Example: - "src/**/*.py"

exclude_paths:
  # Configuration Files
  - "**/*.{yml,yaml}"
  - "**/.codeconcat.yml"
  - "**/.github/*.{yml,yaml}"

  # Test files
  - "**/tests/**"
  - "**/test_*.py"
  - "**/*_test.py"

  # Build and cache files
  - "**/build/**"
  - "**/dist/**"
  - "**/__pycache__/**"
  - "**/*.{pyc,pyo,pyd}"
  - "**/.pytest_cache/**"
  - "**/.coverage"
  - "**/htmlcov/**"

  # Documentation files
  - "**/*.{md,rst,txt}"
  - "**/LICENSE*"
  - "**/README*"

# Language filtering
include_languages:
  # Add languages to include
  # Example: - python

exclude_languages:
  # Add languages to exclude
  # Example: - javascript

# Output options
output: code_concat_output.md
format: markdown  # or json, xml

# Feature toggles
extract_docs: false
merge_docs: false
disable_tree: false
disable_copy: false
disable_annotations: false
disable_symbols: false

# Display options
include_file_summary: true
include_directory_structure: true
remove_comments: true
remove_empty_lines: true
show_line_numbers: true

# Advanced options
max_workers: 4
custom_extension_map:
  # Map file extensions to languages
  # Example: .jsx: javascript
"""
    
    with open(".codeconcat.yml", "w") as f:
        f.write(config_content)
    
    print("[CodeConCat] Created default configuration file: .codeconcat.yml")


def generate_folder_tree(root_path: str, config: CodeConCatConfig) -> str:
    """
    Walk the directory tree starting at root_path and return a string that represents the folder structure.
    Respects exclusion patterns from the config.
    """
    from codeconcat.collector.local_collector import should_skip_dir, should_include_file
    
    lines = []
    for root, dirs, files in os.walk(root_path):
        # Check if we should skip this directory
        if should_skip_dir(root, config.exclude_paths):
            dirs[:] = []  # Clear dirs to prevent descending into this directory
            continue
            
        level = root.replace(root_path, "").count(os.sep)
        indent = "    " * level
        folder_name = os.path.basename(root) or root_path
        lines.append(f"{indent}{folder_name}/")
        
        # Filter files based on exclusion patterns
        included_files = [f for f in files if should_include_file(os.path.join(root, f), config)]
        
        sub_indent = "    " * (level + 1)
        for f in sorted(included_files):
            lines.append(f"{sub_indent}{f}")
            
        # Filter directories for the next iteration
        dirs[:] = [d for d in dirs if not should_skip_dir(os.path.join(root, d), config.exclude_paths)]
        dirs.sort()  # Sort directories for consistent output
        
    return "\n".join(lines)


def run_codeconcat(config: CodeConCatConfig):
    """Main execution function for CodeConCat."""
    
    # Collect files
    if config.github_url:
        code_files = collect_github_files(config)
    else:
        code_files = collect_local_files(config.target_path, config)

    # Generate folder tree if enabled
    folder_tree_str = ""
    if not config.disable_tree:
        folder_tree_str = generate_folder_tree(config.target_path, config)

    # Parse code files
    parsed_files = parse_code_files([f.file_path for f in code_files], config)

    # Extract docs if requested
    docs = []
    if config.extract_docs:
        docs = extract_docs([f.file_path for f in code_files], config)

    # Annotate files if enabled
    annotated_files = []
    if not config.disable_annotations:
        # Create annotations for each file
        for file in parsed_files:
            annotated = annotate(file, config)
            annotated_files.append(annotated)
    else:
        # Create basic annotations without AI analysis
        for file in parsed_files:
            annotated_files.append(AnnotatedFileData(
                file_path=file.file_path,
                language=file.language,
                content=file.content,
                annotated_content=file.content,
                summary="",
                tags=[]
            ))

    # Write output in requested format
    if config.format == "markdown":
        output = write_markdown(annotated_files, docs, config, folder_tree_str)
    elif config.format == "json":
        output = write_json(annotated_files, docs, config, folder_tree_str)
    elif config.format == "xml":
        output = write_xml(parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str)

    # Copy to clipboard if enabled
    if not config.disable_copy:
        try:
            import pyperclip
            pyperclip.copy(output)
            print("[CodeConCat] Output copied to clipboard")
        except ImportError:
            print("[CodeConCat] Warning: pyperclip not installed, skipping clipboard copy")
        except Exception as e:
            print(f"[CodeConCat] Warning: Failed to copy to clipboard: {str(e)}")


def main():
    cli_entry_point()


if __name__ == "__main__":
    main()

---
import os
import yaml
import logging
from typing import Dict, Any
from codeconcat.types import CodeConCatConfig


def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
    """
    Load and merge configuration from .codeconcat.yml (if exists) and CLI args.
    CLI args take precedence over the config file.
    """
    config_data = {}

    # Try to load .codeconcat.yml if it exists
    target_path = cli_args.get("target_path", ".")
    config_path = os.path.join(target_path, ".codeconcat.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[CodeConCat] Warning: Failed to load .codeconcat.yml: {e}")

    # CLI-only arguments that shouldn't be passed to config
    cli_only_args = {"init", "debug"}

    # Filter out CLI-only arguments
    filtered_args = {k: v for k, v in cli_args.items() if k not in cli_only_args}

    # Merge CLI args with config file (CLI takes precedence)
    merged = {**config_data, **filtered_args}

    # Map CLI arg names to config field names
    field_mapping = {
        "include": "include_paths",
        "exclude": "exclude_paths",
        "docs": "extract_docs",
        "no_tree": "disable_tree",
        "no_copy": "disable_copy",
        "no_annotations": "disable_annotations",
        "no_symbols": "disable_symbols",
        "github": "github_url",
        "ref": "github_ref"
    }

    # Rename fields to match CodeConCatConfig
    for cli_name, config_name in field_mapping.items():
        if cli_name in merged:
            merged[config_name] = merged.pop(cli_name)

    # Ensure target_path is set
    merged["target_path"] = target_path

    logging.debug("Merged config data before creating config: %s", merged)

    # Create config object
    try:
        return CodeConCatConfig(**merged)
    except TypeError as e:
        logging.error("Failed to create config: %s", e)
        logging.error("Available fields in CodeConCatConfig: %s", CodeConCatConfig.__dataclass_fields__.keys())
        logging.error("Attempted fields: %s", merged.keys())
        raise


def read_config_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def apply_dict_to_config(data: Dict[str, Any], config: CodeConCatConfig) -> None:
    for key, value in data.items():
        if hasattr(config, key):
            if key == "custom_extension_map" and isinstance(value, dict):
                config.custom_extension_map.update(value)
            else:
                setattr(config, key, value)

---

---

---
from codeconcat.types import ParsedFileData, AnnotatedFileData, CodeConCatConfig

def annotate(parsed_data: ParsedFileData, config: CodeConCatConfig) -> AnnotatedFileData:
    pieces = []
    pieces.append(f"## File: {parsed_data.file_path}\n")

    # Group declarations by kind
    functions = []
    classes = []
    structs = []
    symbols = []

    for decl in parsed_data.declarations:
        if decl.kind == "function":
            functions.append(decl.name)
        elif decl.kind == "class":
            classes.append(decl.name)
        elif decl.kind == "struct":
            structs.append(decl.name)
        elif decl.kind == "symbol":
            symbols.append(decl.name)

    # Add headers for each kind if they exist
    if functions:
        pieces.append("### Functions\n")
        for name in functions:
            pieces.append(f"- {name}\n")

    if classes:
        pieces.append("### Classes\n")
        for name in classes:
            pieces.append(f"- {name}\n")

    if structs:
        pieces.append("### Structs\n")
        for name in structs:
            pieces.append(f"- {name}\n")

    if symbols:
        pieces.append("### Symbols\n")
        for name in symbols:
            pieces.append(f"- {name}\n")

    pieces.append(f"```{parsed_data.language}\n{parsed_data.content}\n```\n")

    # Generate summary
    summary_parts = []
    if functions:
        summary_parts.append(f"{len(functions)} functions")
    if classes:
        summary_parts.append(f"{len(classes)} classes")
    if structs:
        summary_parts.append(f"{len(structs)} structs")
    if symbols:
        summary_parts.append(f"{len(symbols)} symbols")
    
    summary = f"Contains {', '.join(summary_parts)}" if summary_parts else "No declarations found"

    # Generate tags
    tags = []
    if functions:
        tags.append("has_functions")
    if classes:
        tags.append("has_classes")
    if structs:
        tags.append("has_structs")
    if symbols:
        tags.append("has_symbols")
    tags.append(parsed_data.language)

    return AnnotatedFileData(
        file_path=parsed_data.file_path,
        language=parsed_data.language,
        content=parsed_data.content,
        annotated_content="".join(pieces),
        summary=summary,
        tags=tags
    )

---
"""Types for security processing."""

from dataclasses import dataclass

@dataclass
class SecurityIssue:
    """Represents a detected security issue in the code."""
    line_number: int
    line_content: str
    issue_type: str
    severity: str
    description: str

---
"""Content processing module for CodeConcat."""

import os
from typing import List
from codeconcat.base_types import ParsedFileData, CodeConCatConfig
from codeconcat.processor.token_counter import TokenStats
from codeconcat.processor.security_types import SecurityIssue

def process_file_content(content: str, config: CodeConCatConfig) -> str:
    """Process file content according to configuration options."""
    lines = content.split('\n')
    processed_lines = []
    
    for i, line in enumerate(lines):
        # Skip if it's an empty line and we're removing empty lines
        if config.remove_empty_lines and not line.strip():
            continue
            
        # Skip if it's a comment and we're removing comments
        if config.remove_comments:
            stripped = line.strip()
            if (stripped.startswith('#') or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or 
                stripped.startswith('*') or 
                stripped.startswith('"""') or 
                stripped.startswith("'''") or 
                stripped.endswith('*/')):
                continue
                
        # Add line number if configured
        if config.show_line_numbers:
            line = f"{i+1:4d} | {line}"
            
        processed_lines.append(line)
        
    return '\n'.join(processed_lines)

def generate_file_summary(file_data: ParsedFileData) -> str:
    """Generate a summary for a file."""
    summary = []
    summary.append(f"File: {os.path.basename(file_data.file_path)}")
    summary.append(f"Language: {file_data.language}")
    
    if file_data.token_stats:
        summary.append("Token Counts:")
        summary.append(f"  - GPT-3.5: {file_data.token_stats.gpt3_tokens:,}")
        summary.append(f"  - GPT-4: {file_data.token_stats.gpt4_tokens:,}")
        summary.append(f"  - Davinci: {file_data.token_stats.davinci_tokens:,}")
        summary.append(f"  - Claude: {file_data.token_stats.claude_tokens:,}")
    
    if file_data.security_issues:
        summary.append("\nSecurity Issues:")
        for issue in file_data.security_issues:
            summary.append(f"  - {issue.issue_type} (Line {issue.line_number})")
            summary.append(f"    {issue.line_content}")
    
    if file_data.declarations:
        summary.append("\nDeclarations:")
        for decl in file_data.declarations:
            summary.append(f"  - {decl.kind}: {decl.name} (lines {decl.start_line}-{decl.end_line})")
    
    return '\n'.join(summary)

def generate_directory_structure(file_paths: List[str]) -> str:
    """Generate a tree-like directory structure."""
    structure = {}
    for path in file_paths:
        parts = path.split(os.sep)
        current = structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = None
    
    def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> List[str]:
        lines = []
        if node is None:
            return lines
            
        items = list(node.items())
        for i, (name, subtree) in enumerate(items):
            is_last_item = i == len(items) - 1
            lines.append(f"{prefix}{'└── ' if is_last_item else '├── '}{name}")
            if subtree is not None:
                extension = "    " if is_last_item else "│   "
                lines.extend(print_tree(subtree, prefix + extension, is_last_item))
        return lines
    
    return '\n'.join(print_tree(structure))

---
"""Token counting functionality using tiktoken."""

import tiktoken
from dataclasses import dataclass
from typing import Dict

@dataclass
class TokenStats:
    """Token statistics for a file."""
    gpt3_tokens: int
    gpt4_tokens: int
    davinci_tokens: int
    claude_tokens: int

# Cache for encoders to avoid recreating them
_ENCODER_CACHE: Dict[str, tiktoken.Encoding] = {}

def get_encoder(model: str = "gpt-3.5-turbo") -> tiktoken.Encoding:
    """Get or create a tiktoken encoder for the specified model."""
    if model not in _ENCODER_CACHE:
        _ENCODER_CACHE[model] = tiktoken.encoding_for_model(model)
    return _ENCODER_CACHE[model]

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count the number of tokens in a text string using the specified model's tokenizer."""
    encoder = get_encoder(model)
    return len(encoder.encode(text))

def get_token_stats(text: str) -> TokenStats:
    """Get token statistics for different models."""
    return TokenStats(
        gpt3_tokens=count_tokens(text, "gpt-3.5-turbo"),
        gpt4_tokens=count_tokens(text, "gpt-4"),
        davinci_tokens=count_tokens(text, "text-davinci-003"),
        claude_tokens=int(len(text.encode('utf-8')) / 4)  # Rough approximation for Claude
    )

---
"""Content processing package for CodeConcat."""

from codeconcat.processor.content_processor import (
    process_file_content,
    generate_file_summary,
    generate_directory_structure
)

__all__ = [
    'process_file_content',
    'generate_file_summary',
    'generate_directory_structure'
]

---
"""Security processor for detecting potential secrets and sensitive information."""

import re
from typing import List, Dict, Any, Tuple
from codeconcat.processor.security_types import SecurityIssue

class SecurityProcessor:
    """Processor for detecting security issues in code."""
    
    # Common patterns for sensitive information
    PATTERNS = {
        'aws_key': (r'(?i)aws[_\-\s]*(?:access)?[_\-\s]*key[_\-\s]*(?:id)?["\'\s:=]+[A-Za-z0-9/\+=]{20,}',
                   'AWS Key'),
        'aws_secret': (r'(?i)aws[_\-\s]*secret[_\-\s]*(?:access)?[_\-\s]*key["\'\s:=]+[A-Za-z0-9/\+=]{40,}',
                      'AWS Secret Key'),
        'github_token': (r'(?i)(?:github|gh)[_\-\s]*(?:token|key)["\'\s:=]+[A-Za-z0-9_\-]{36,}',
                        'GitHub Token'),
        'generic_api_key': (r'(?i)api[_\-\s]*key["\'\s:=]+[A-Za-z0-9_\-]{16,}',
                           'API Key'),
        'generic_secret': (r'(?i)(?:secret|token|key|password|pwd)["\'\s:=]+[A-Za-z0-9_\-]{16,}',
                          'Generic Secret'),
        'private_key': (r'(?i)-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY[^-]*-----.*?-----END',
                       'Private Key'),
        'basic_auth': (r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*basic\s+[A-Za-z0-9+/=]+["\']*',
                      'Basic Authentication'),
        'bearer_token': (r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*bearer\s+[A-Za-z0-9._\-]+["\']*',
                        'Bearer Token'),
    }

    # Patterns for common test/sample values that should be ignored
    IGNORE_PATTERNS = [
        r'(?i)example|sample|test|dummy|fake|mock',
        r'your.*key.*here',
        r'xxx+',
        r'[A-Za-z0-9]{16,}\.example\.com',
    ]

    @classmethod
    def scan_content(cls, content: str, file_path: str) -> List[SecurityIssue]:
        """
        Scan content for potential security issues.
        
        Args:
            content: The content to scan
            file_path: Path to the file being scanned (for context)
            
        Returns:
            List of SecurityIssue instances
        """
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines
            if not line.strip():
                continue
                
            # Skip if line matches ignore patterns
            if any(re.search(pattern, line) for pattern in cls.IGNORE_PATTERNS):
                continue
            
            # Check each security pattern
            for pattern_name, (pattern, issue_type) in cls.PATTERNS.items():
                if re.search(pattern, line):
                    # Mask the potential secret in the line content
                    masked_line = cls._mask_sensitive_data(line, pattern)
                    
                    issues.append(SecurityIssue(
                        line_number=line_num,
                        line_content=masked_line,
                        issue_type=issue_type,
                        severity='HIGH',
                        description=f'Potential {issue_type} found in {file_path}'
                    ))
        
        return issues

    @staticmethod
    def _mask_sensitive_data(line: str, pattern: str) -> str:
        """Mask sensitive data in the line with asterisks."""
        def mask_match(match):
            return match.group()[:4] + '*' * (len(match.group()) - 8) + match.group()[-4:]
        
        return re.sub(pattern, mask_match, line)

    @classmethod
    def format_issues(cls, issues: List[SecurityIssue]) -> str:
        """Format security issues into a readable string."""
        if not issues:
            return "No security issues found."
            
        formatted = ["Security Scan Results:", "=" * 20]
        for issue in issues:
            formatted.extend([
                f"\nIssue Type: {issue.issue_type}",
                f"Severity: {issue.severity}",
                f"Line {issue.line_number}: {issue.line_content}",
                f"Description: {issue.description}",
                "-" * 20
            ])
        
        return "\n".join(formatted)

---
import os
import tempfile
import shutil
import subprocess
import re
from typing import List, Optional, Tuple
from codeconcat.types import CodeConCatConfig
from codeconcat.collector.local_collector import collect_local_files
from github import Github
from github.Repository import Repository
from github.ContentFile import ContentFile


def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
    """Parse GitHub URL or shorthand into owner, repo, and ref."""
    # Handle shorthand notation (owner/repo)
    if '/' in url and not url.startswith('http'):
        parts = url.split('/')
        owner = parts[0]
        repo = parts[1]
        ref = parts[2] if len(parts) > 2 else None
        return owner, repo, ref
    
    # Handle full URLs
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?', url)
    if match:
        return match.group(1), match.group(2), match.group(3)
    
    raise ValueError(
        "Invalid GitHub URL or shorthand. Use format 'owner/repo', 'owner/repo/branch', "
        "or 'https://github.com/owner/repo'"
    )


def collect_github_files(
    github_url: str,
    config: CodeConCatConfig
) -> List[str]:
    owner, repo_name, url_ref = parse_github_url(github_url)
    
    # Use explicit ref if provided, otherwise use ref from URL
    target_ref = config.ref or url_ref or 'main'
    
    g = Github(config.github_token) if config.github_token else Github()
    repo = g.get_repo(f"{owner}/{repo_name}")
    
    try:
        # Verify ref exists
        repo.get_commit(target_ref)
    except:
        try:
            # Try as a branch/tag name
            branches = [b.name for b in repo.get_branches()]
            tags = [t.name for t in repo.get_tags()]
            if target_ref not in branches + tags:
                raise ValueError(
                    f"Reference '{target_ref}' not found. Available branches: {branches}, "
                    f"tags: {tags}"
                )
        except Exception as e:
            raise ValueError(f"Error accessing repository: {str(e)}")
    
    contents = []
    for content in repo.get_contents("", ref=target_ref):
        if content.type == "file":
            contents.append(content.decoded_content.decode('utf-8'))
        elif content.type == "dir":
            contents.extend(_collect_dir_contents(repo, content.path, target_ref))
    
    return contents


def _collect_dir_contents(
    repo: Repository,
    path: str,
    ref: str
) -> List[str]:
    """Recursively collect contents from a directory."""
    contents = []
    for content in repo.get_contents(path, ref=ref):
        if content.type == "file":
            contents.append(content.decoded_content.decode('utf-8'))
        elif content.type == "dir":
            contents.extend(_collect_dir_contents(repo, content.path, ref))
    return contents


def collect_github_files_legacy(github_url: str, config: CodeConCatConfig) -> List[str]:
    temp_dir = tempfile.mkdtemp(prefix="codeconcat_github_")
    try:
        clone_url = build_clone_url(github_url, config.github_token)
        print(f"[CodeConCat] Cloning from {clone_url} into {temp_dir}")
        subprocess.run(["git", "clone", "--depth=1", clone_url, temp_dir], check=True)

        file_paths = collect_local_files(temp_dir, config)
        return file_paths

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone GitHub repo: {e}") from e
    finally:
        # Optionally remove the temp directory
        # shutil.rmtree(temp_dir, ignore_errors=True)
        pass


def build_clone_url(github_url: str, token: str) -> str:
    if token and "https://" in github_url:
        parts = github_url.split("https://", 1)
        return f"https://{token}@{parts[1]}"
    return github_url

---

---
import os
import fnmatch
from typing import List
from concurrent.futures import ThreadPoolExecutor
import logging

from codeconcat.types import CodeConCatConfig, ParsedFileData


# Set up logging
logging.basicConfig(level=logging.WARNING)

DEFAULT_EXCLUDES = [
    # Version Control
    ".git/",  # Match the .git directory itself
    ".git/**",  # Match contents of .git directory
    "**/.git/",  # Match .git directory anywhere in tree
    "**/.git/**",  # Match contents of .git directory anywhere in tree
    ".gitignore",
    "**/.gitignore",
    
    # OS and Editor Files
    ".DS_Store",
    "**/.DS_Store",
    "Thumbs.db",
    "**/*.swp",
    "**/*.swo",
    ".idea/**",
    ".vscode/**",
    
    # Configuration Files
    "*.yml",
    "./*.yml",
    "**/*.yml",
    "*.yaml",
    "./*.yaml",
    "**/*.yaml",
    ".codeconcat.yml",
    "./.codeconcat.yml",
    "**/.codeconcat.yml",
    ".github/*.yml",
    ".github/*.yaml",
    "**/.github/*.yml",
    "**/.github/*.yaml",
    
    # Build and Compilation
    "__pycache__",
    "./__pycache__",
    "__pycache__/",
    "./__pycache__/",
    "__pycache__/**",
    "./__pycache__/**",
    "**/__pycache__",
    "**/__pycache__/",
    "**/__pycache__/**",
    "**/__pycache__/**/*",
    "*.pyc",
    "**/*.pyc",
    "*.pyo",
    "**/*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.dylib",
    "*.class",
    "*.exe",
    "*.bin",
    "build",
    "./build",
    "build/",
    "./build/",
    "build/**",
    "./build/**",
    "build/**/*",
    "./build/**/*",
    "**/build",
    "**/build/",
    "**/build/**",
    "**/build/**/*",
    "dist",
    "./dist",
    "dist/",
    "./dist/",
    "dist/**",
    "./dist/**",
    "**/dist",
    "**/dist/",
    "**/dist/**",
    "**/dist/**/*",
    "*.egg-info",
    "./*.egg-info",
    "*.egg-info/",
    "./*.egg-info/",
    "*.egg-info/**",
    "./*.egg-info/**",
    "*.egg-info/**/*",
    "./*.egg-info/**/*",
    "**/*.egg-info",
    "**/*.egg-info/",
    "**/*.egg-info/**",
    "**/*.egg-info/**/*",
    "**/codeconcat.egg-info",
    "**/codeconcat.egg-info/",
    "**/codeconcat.egg-info/**",
    "**/codeconcat.egg-info/**/*",
    
    # Test Files
    "tests",
    "./tests",
    "tests/",
    "./tests/",
    "tests/**",
    "./tests/**",
    "tests/**/*",
    "./tests/**/*",
    "**/tests",
    "**/tests/",
    "**/tests/**",
    "**/tests/**/*",
    "**/test_*.py",
    "**/*_test.py",
    "**/test_*.py[cod]",
    "test_*.py",
    "*_test.py",
    "./test_*.py",
    "./*_test.py",
    "**/test_*.py",
    "**/*_test.py",
    
    # Log Files
    "*.log",
    "./*.log",
    "**/*.log",
    "**/leap.log",
    "**/sqm.log",
    "**/timer.log",
    "**/build.log",
    "**/test.log",
    "**/debug.log",
    "**/error.log",
    "leap.log",
    "sqm.log",
    "timer.log",
    "build.log",
    "test.log",
    "debug.log",
    "error.log",
    "./leap.log",
    "./sqm.log",
    "./timer.log",
    "./build.log",
    "./test.log",
    "./debug.log",
    "./error.log",
    
    # Dependencies
    "node_modules/**",
    "**/node_modules/**",
    "vendor/**",
    "**/vendor/**",
    "env/**",
    "**/env/**",
    "venv/**",
    "**/venv/**",
    ".env/**",
    "**/.env/**",
    ".venv/**",
    "**/.venv/**",
    
    # Documentation
    "docs/**",
    "**/docs/**",
    "_build/**",
    "**/_build/**",
    "_static/**",
    "**/_static/**",
    "_templates/**",
    "**/_templates/**",
    
    # CodeConCat Output
    "code_concat_output.md",
    "./code_concat_output.md",
    "**/code_concat_output.md"
]


def collect_local_files(root_path: str, config: CodeConCatConfig):
    """Collect files from local filesystem."""
    
    logging.debug(f"[CodeConCat] Collecting files from: {root_path}")
    
    # Ensure root path exists
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"Path does not exist: {root_path}")
    
    # Collect files using thread pool
    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        futures = []
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Skip directories that match exclude patterns
            if should_skip_dir(dirpath, config.exclude_paths):
                dirnames.clear()  # Clear dirnames to skip subdirectories
                continue
            
            # Process files in parallel
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                futures.append(
                    executor.submit(process_file, file_path, config)
                )
        
        # Collect results, filtering out None values
        results = [f.result() for f in futures if f.result()]
        
    if not results:
        logging.warning("[CodeConCat] No files found matching the criteria")
    else:
        logging.info(f"[CodeConCat] Collected {len(results)} files")
    
    return results


def process_file(file_path: str, config: CodeConCatConfig):
    """Process a single file, reading its content if it should be included."""
    try:
        if not should_include_file(file_path, config):
            return None
            
        if is_binary_file(file_path):
            logging.debug(f"[CodeConCat] Skipping binary file: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        ext = os.path.splitext(file_path)[1].lstrip('.')
        language = ext_map(ext, config)
        
        logging.debug(f"[CodeConCat] Processed file: {file_path} ({language})")
        return ParsedFileData(
            file_path=file_path,
            language=language,
            content=content,
            declarations=[]  # We'll fill this in during parsing phase
        )
        
    except UnicodeDecodeError:
        logging.debug(f"[CodeConCat] Skipping non-text file: {file_path}")
        return None
    except Exception as e:
        logging.error(f"[CodeConCat] Error processing {file_path}: {str(e)}")
        return None


def should_skip_dir(dirpath: str, user_excludes: List[str]) -> bool:
    """Check if a directory should be skipped based on exclude patterns."""
    all_excludes = DEFAULT_EXCLUDES + (user_excludes or [])
    logging.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")
    
    # Convert to relative path for matching
    if os.path.isabs(dirpath):
        try:
            rel_path = os.path.relpath(dirpath, os.getcwd())
        except ValueError:
            rel_path = dirpath
    else:
        rel_path = dirpath
        
    # Check each exclude pattern
    for pattern in all_excludes:
        if matches_pattern(rel_path, pattern):
            logging.debug(f"Excluding directory {rel_path} due to pattern {pattern}")
            return True
    
    return False


def should_include_file(path_str: str, config: CodeConCatConfig) -> bool:
    """Determine if a file should be included based on patterns and configuration."""
    # Get all exclude patterns
    all_excludes = DEFAULT_EXCLUDES + (config.exclude_paths or [])
    logging.debug(f"Checking file: {path_str} against patterns: {all_excludes}")
    
    # Convert to relative path for matching
    if os.path.isabs(path_str):
        try:
            rel_path = os.path.relpath(path_str, os.getcwd())
        except ValueError:
            rel_path = path_str
    else:
        rel_path = path_str
        
    # Normalize path separators
    rel_path = rel_path.replace(os.sep, '/')
    
    # Check exclusions first for the file itself
    for pattern in all_excludes:
        if matches_pattern(rel_path, pattern):
            logging.debug(f"Excluding file {rel_path} due to pattern {pattern}")
            return False
            
    # Check exclusions for all parent directories
    path_parts = rel_path.split('/')
    for i in range(len(path_parts)):
        parent_path = '/'.join(path_parts[:i+1])
        if parent_path:  # Skip empty path
            for pattern in all_excludes:
                if matches_pattern(parent_path, pattern):
                    logging.debug(f"Excluding file {rel_path} due to parent directory {parent_path} matching pattern {pattern}")
                    return False
        
    # If we have includes, file must match at least one
    if config.include_languages:
        ext = os.path.splitext(path_str)[1].lower().lstrip(".")
        language_label = ext_map(ext, config)
        return language_label in config.include_languages
        
    return True


def matches_pattern(path_str: str, pattern: str) -> bool:
    """Match a path against a glob pattern, handling both relative and absolute paths."""
    # Convert absolute paths to relative for matching
    if os.path.isabs(path_str):
        try:
            path_str = os.path.relpath(path_str, os.getcwd())
        except ValueError:
            # If paths are on different drives, keep absolute path
            pass

    # Normalize path separators for consistent matching
    path_str = path_str.replace(os.sep, '/')
    pattern = pattern.replace(os.sep, '/')
    
    # Handle directory patterns
    if pattern.endswith('/**'):
        # For directory wildcard patterns, check if the path starts with the directory part
        dir_pattern = pattern[:-3]  # Remove '/**'
        # Remove leading ./ from both path and pattern for comparison
        if dir_pattern.startswith('./'):
            dir_pattern = dir_pattern[2:]
        if path_str.startswith('./'):
            path_str = path_str[2:]
        return path_str == dir_pattern or path_str.startswith(dir_pattern + '/')
    elif os.path.isdir(path_str) and not path_str.endswith('/'):
        # For directories, ensure they end with / for matching
        path_str += '/'
        if not pattern.endswith('/'):
            pattern += '/'
    
    # Remove leading ./ from both path and pattern for matching
    if pattern.startswith('./'):
        pattern = pattern[2:]
    if path_str.startswith('./'):
        path_str = path_str[2:]
    
    # Handle both glob patterns and direct matches
    return fnmatch.fnmatch(path_str, pattern)


def ext_map(ext: str, config: CodeConCatConfig) -> str:
    if ext in config.custom_extension_map:
        return config.custom_extension_map[ext]

    builtin = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "r": "r",
        "jl": "julia",
        "cpp": "cpp",
        "hpp": "cpp",
        "cxx": "cpp",
        "c": "c",
        "h": "c",
        "md": "doc",
        "rst": "doc",
        "txt": "doc",
        "rmd": "doc",
    }
    return builtin.get(ext, ext)


def is_binary_file(file_path: str) -> bool:
    """Check if a file is likely to be binary."""
    try:
        with open(file_path, 'tr') as check_file:
            check_file.readline()
            return False
    except UnicodeDecodeError:
        return True

---
import os
from typing import List
from concurrent.futures import ThreadPoolExecutor

from codeconcat.types import CodeConCatConfig, ParsedDocData


def extract_docs(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedDocData]:
    doc_paths = [fp for fp in file_paths if is_doc_file(fp, config.doc_extensions)]

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(lambda fp: parse_doc_file(fp), doc_paths))
    return results


def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in doc_exts


def parse_doc_file(file_path: str) -> ParsedDocData:
    ext = os.path.splitext(file_path)[1].lower()
    content = read_doc_content(file_path)
    doc_type = ext.lstrip(".")
    return ParsedDocData(file_path=file_path, doc_type=doc_type, content=content)


def read_doc_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

---
import os
from typing import List, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor

from codeconcat.types import CodeConCatConfig, ParsedFileData
from codeconcat.parser.language_parsers.python_parser import parse_python
from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
from codeconcat.parser.language_parsers.r_parser import parse_r
from codeconcat.parser.language_parsers.julia_parser import parse_julia
from codeconcat.parser.language_parsers.rust_parser import parse_rust_code
from codeconcat.parser.language_parsers.cpp_parser import parse_cpp_code
from codeconcat.parser.language_parsers.c_parser import parse_c_code
from codeconcat.parser.language_parsers.csharp_parser import parse_csharp_code
from codeconcat.parser.language_parsers.java_parser import parse_java
from codeconcat.parser.language_parsers.go_parser import parse_go
from codeconcat.parser.language_parsers.php_parser import parse_php


def parse_code_files(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedFileData]:
    code_paths = [fp for fp in file_paths if not is_doc_file(fp, config.doc_extensions)]

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(lambda fp: parse_single_file(fp, config), code_paths))
    return results


def parse_single_file(file_path: str, config: CodeConCatConfig) -> ParsedFileData:
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    content = read_file_content(file_path)

    parser_info = get_language_parser(file_path)
    if parser_info:
        language, parser_func = parser_info
        if parser_func == parse_javascript_or_typescript:
            return parser_func(file_path, content, language)
        return parser_func(file_path, content)
    else:
        return ParsedFileData(file_path=file_path, language=get_language_name(file_path), content=content)


def get_language_parser(file_path: str) -> Optional[Tuple[str, Callable]]:
    """Get the appropriate parser for a file based on its extension."""
    ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    extension_map = {
        # Existing parsers
        '.py': ("python", parse_python),
        '.js': ("javascript", parse_javascript_or_typescript),
        '.ts': ("typescript", parse_javascript_or_typescript),
        '.jsx': ("javascript", parse_javascript_or_typescript),
        '.tsx': ("typescript", parse_javascript_or_typescript),
        '.r': ("r", parse_r),
        '.jl': ("julia", parse_julia),
        
        # New parsers
        '.rs': ("rust", parse_rust_code),
        '.cpp': ("cpp", parse_cpp_code),
        '.cxx': ("cpp", parse_cpp_code),
        '.cc': ("cpp", parse_cpp_code),
        '.hpp': ("cpp", parse_cpp_code),
        '.hxx': ("cpp", parse_cpp_code),
        '.h': ("c", parse_c_code),  # Note: .h could be C or C++
        '.c': ("c", parse_c_code),
        '.cs': ("csharp", parse_csharp_code),
        '.java': ("java", parse_java),
        '.go': ("go", parse_go),
        '.php': ("php", parse_php),
    }
    
    ext_with_dot = f".{ext}" if not ext.startswith('.') else ext
    return extension_map.get(ext_with_dot)


def get_language_name(file_path: str) -> str:
    """Get the language name for a file based on its extension."""
    parser_info = get_language_parser(file_path)
    if parser_info:
        return parser_info[0]
    return "unknown"


def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in doc_exts


def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

---

---
"""C# code parser for CodeConcat."""

import re
from typing import List, Tuple

def parse_csharp_code(content: str) -> List[Tuple[str, int, int]]:
    """Parse C# code to identify classes, methods, properties, and other constructs.
    
    Returns:
        List of tuples (symbol_name, start_line, end_line)
    """
    symbols = []
    lines = content.split('\n')
    
    # Patterns for C# constructs
    patterns = {
        'class': r'^\s*(?:public|private|protected|internal)?\s*(?:static|abstract|sealed)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'interface': r'^\s*(?:public|private|protected|internal)?\s*interface\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'method': r'^\s*(?:public|private|protected|internal)?\s*(?:static|virtual|abstract|override)?\s*(?:async\s+)?(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',
        'property': r'^\s*(?:public|private|protected|internal)?\s*(?:static|virtual|abstract|override)?\s*(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*{\s*(?:get|set)',
        'enum': r'^\s*(?:public|private|protected|internal)?\s*enum\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'struct': r'^\s*(?:public|private|protected|internal)?\s*struct\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'delegate': r'^\s*(?:public|private|protected|internal)?\s*delegate\s+(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        'event': r'^\s*(?:public|private|protected|internal)?\s*event\s+(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)',
        'namespace': r'^\s*namespace\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
    }
    
    in_block = False
    block_start = 0
    block_name = ""
    brace_count = 0
    in_comment = False
    
    for i, line in enumerate(lines):
        # Handle multi-line comments
        if '/*' in line:
            in_comment = True
        if '*/' in line:
            in_comment = False
            continue
        if in_comment or line.strip().startswith('//'):
            continue
            
        # Skip attributes
        if line.strip().startswith('['):
            continue
            
        # Track braces and blocks
        if not in_block:
            for construct, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    block_name = match.group(1)
                    block_start = i
                    in_block = True
                    brace_count = line.count('{') - line.count('}')
                    # Handle auto-properties and one-line definitions
                    if brace_count == 0 and ';' in line:
                        symbols.append((block_name, i, i))
                        in_block = False
                    break
        else:
            brace_count += line.count('{') - line.count('}')
            
        # Check if block ends
        if in_block and brace_count == 0 and ('}' in line or ';' in line):
            symbols.append((block_name, block_start, i))
            in_block = False
            
    return symbols

---
"""C code parser for CodeConcat."""

import re
from typing import List, Tuple

def parse_c_code(content: str) -> List[Tuple[str, int, int]]:
    """Parse C code to identify functions, structs, unions, and enums.
    
    Returns:
        List of tuples (symbol_name, start_line, end_line)
    """
    symbols = []
    lines = content.split('\n')
    
    # Patterns for C constructs
    patterns = {
        'function': r'^\s*(?:static\s+)?(?:inline\s+)?(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^;]*$',
        'struct': r'^\s*struct\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'union': r'^\s*union\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'enum': r'^\s*enum\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'typedef': r'^\s*typedef\s+(?:struct|union|enum)?\s*(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*;',
        'define': r'^\s*#define\s+([A-Z_][A-Z0-9_]*)',
    }
    
    in_block = False
    block_start = 0
    block_name = ""
    brace_count = 0
    in_comment = False
    in_macro = False
    
    for i, line in enumerate(lines):
        # Handle multi-line comments
        if '/*' in line:
            in_comment = True
        if '*/' in line:
            in_comment = False
            continue
        if in_comment or line.strip().startswith('//'):
            continue
            
        # Handle multi-line macros
        if line.strip().endswith('\\'):
            in_macro = True
            continue
        if in_macro:
            if not line.strip().endswith('\\'):
                in_macro = False
            continue
            
        # Skip preprocessor directives except #define
        if line.strip().startswith('#') and not line.strip().startswith('#define'):
            continue
            
        # Track braces and blocks
        if not in_block:
            for construct, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    block_name = match.group(1)
                    block_start = i
                    in_block = True
                    brace_count = line.count('{') - line.count('}')
                    # Handle one-line definitions
                    if construct in ['typedef', 'define'] or (brace_count == 0 and ';' in line):
                        symbols.append((block_name, i, i))
                        in_block = False
                    break
        else:
            brace_count += line.count('{') - line.count('}')
            
        # Check if block ends
        if in_block and brace_count == 0 and ('}' in line or ';' in line):
            symbols.append((block_name, block_start, i))
            in_block = False
            
    return symbols

---
"""Julia code parser for CodeConcat."""

import re
from typing import List, Dict, Pattern
from codeconcat.types import ParsedFileData, Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

class JuliaParser(BaseParser):
    """Julia language parser."""
    
    def _setup_patterns(self):
        """Set up Julia-specific patterns."""
        self.patterns = {
            'function': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'function\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Function name
                r'\s*\((?P<parameters>[^)]*)\)'  # Parameters
                r'(?:\s*::\s*(?P<return_type>[^{;]+))?'  # Optional return type
            ),
            'struct': re.compile(
                r'^(?P<modifiers>(?:export\s+)?(?:mutable\s+)?)'  # Modifiers
                r'struct\s+(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Struct name
                r'(?:\s*<:\s*(?P<supertype>[^{]+))?'  # Optional supertype
            ),
            'abstract': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'abstract\s+type\s+(?P<type_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Type name
                r'(?:\s*<:\s*(?P<supertype>[^{]+))?'  # Optional supertype
            ),
            'module': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'module\s+(?P<module_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Module name
            ),
            'const': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'const\s+(?P<const_name>[A-Z][A-Z0-9_]*)'  # Constant name
                r'(?:\s*::\s*(?P<type>[^=]+))?'  # Optional type annotation
                r'\s*='  # Assignment
            ),
            'macro': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'macro\s+(?P<macro_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Macro name
                r'\s*\((?P<parameters>[^)]*)\)'  # Parameters
            ),
            'variable': re.compile(
                r'^(?P<var_name>[a-z][a-z0-9_]*)'  # Variable name
                r'(?:\s*::\s*(?P<type>[^=]+))?'  # Optional type annotation
                r'\s*=\s*(?!.*(?:function|struct|mutable|module|macro))'  # Assignment, not a definition
            )
        }
        
        self.modifiers = {'export', 'mutable'}
        self.block_start = 'begin'
        self.block_end = 'end'
        self.line_comment = '#'
        self.block_comment_start = '#='
        self.block_comment_end = '=#'
        
    def parse(self, content: str) -> List[Declaration]:
        """Parse Julia code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_module = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle block comments
            if line.startswith('#='):
                in_comment = True
                if '=#' in line[2:]:
                    in_comment = False
                i += 1
                continue
                
            if in_comment:
                if '=#' in line:
                    in_comment = False
                i += 1
                continue
                
            # Skip line comments
            if line.startswith('#'):
                i += 1
                continue
                
            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group(f'{kind}_name')
                    modifiers = set()
                    if 'modifiers' in match.groupdict() and match.group('modifiers'):
                        modifiers = {m.strip() for m in match.group('modifiers').split()}
                    
                    # Create symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=i,
                        modifiers=modifiers,
                        parent=current_module
                    )
                    
                    # Handle block-level constructs
                    if kind in ('function', 'struct', 'abstract', 'module', 'macro'):
                        j = i + 1
                        block_level = 1
                        while j < len(lines) and block_level > 0:
                            if 'begin' in lines[j] or kind in lines[j]:
                                block_level += 1
                            if 'end' in lines[j]:
                                block_level -= 1
                            j += 1
                        symbol.end_line = j - 1
                        i = j - 1
                        
                        # Update current module context
                        if kind == 'module':
                            current_module = symbol
                    
                    symbols.append(symbol)
                    break
            
            i += 1
        
        # Convert to Declarations for backward compatibility
        return [
            Declaration(
                symbol.kind,
                symbol.name,
                symbol.start_line + 1,
                symbol.end_line + 1
            ) for symbol in symbols
        ]

def parse_julia(file_path: str, content: str) -> ParsedFileData:
    """Parse Julia code and return ParsedFileData."""
    parser = JuliaParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="julia",
        content=content,
        declarations=declarations
    )

---

---
"""PHP language parser for CodeConcat."""

from typing import List
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.types import Declaration


class PhpParser(BaseParser):
    """PHP language parser."""

    def _setup_patterns(self):
        """Set up PHP-specific patterns."""
        # Namespace pattern
        self.namespace_pattern = self._create_pattern(
            r'namespace\s+([\w\\]+);'
        )

        # Use/import pattern
        self.use_pattern = self._create_pattern(
            r'use\s+([\w\\]+)(?:\s+as\s+(\w+))?;'
        )

        # Class pattern (including abstract, final, and traits)
        self.class_pattern = self._create_pattern(
            r'(?:abstract\s+|final\s+)?'
            r'(?:class|interface|trait)\s+'
            r'(\w+)'
            r'(?:\s+extends\s+[\w\\]+)?'
            r'(?:\s+implements\s+[\w\\,\s]+)?'
            r'\s*{'
        )

        # Method pattern
        self.method_pattern = self._create_pattern(
            r'(?:public\s+|protected\s+|private\s+)?'
            r'(?:static\s+|final\s+|abstract\s+)*'
            r'function\s+'
            r'(?:&\s*)?'  # Reference return
            r'(\w+)'  # Method name
            r'\s*\([^)]*\)'  # Parameters
            r'(?:\s*:\s*\??[\w\\|]+)?'  # Return type hint
            r'\s*(?:{|;)'  # Body or abstract method
        )

        # Property pattern
        self.property_pattern = self._create_pattern(
            r'(?:public\s+|protected\s+|private\s+)?'
            r'(?:static\s+|readonly\s+)*'
            r'(?:var\s+)?'
            r'\$(\w+)'  # Property name
            r'(?:\s*=\s*[^;]+)?;'  # Optional initialization
        )

        # Constant pattern
        self.const_pattern = self._create_pattern(
            r'const\s+'
            r'(\w+)'  # Constant name
            r'\s*=\s*[^;]+;'  # Value required
        )

    def parse(self, content: str) -> List[Declaration]:
        """Parse PHP code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_namespace = None
        current_class = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle block comments
            if line.startswith('/*'):
                in_comment = True
                if '*/' in line[2:]:
                    in_comment = False
                i += 1
                continue
            if in_comment:
                if '*/' in line:
                    in_comment = False
                i += 1
                continue
            
            # Skip line comments
            if line.startswith('//') or line.startswith('#'):
                i += 1
                continue

            # Track braces for scope
            brace_count += line.count('{') - line.count('}')
            
            # Check for namespace declaration
            if namespace_match := self.namespace_pattern.search(line):
                current_namespace = namespace_match.group(1)
                i += 1
                continue

            # Check for class/interface/trait declaration
            if class_match := self.class_pattern.search(line):
                class_name = class_match.group(1)
                qualified_name = f"{current_namespace}\\{class_name}" if current_namespace else class_name
                current_class = qualified_name
                symbols.append(Declaration(
                    kind="class",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for method declaration
            if method_match := self.method_pattern.search(line):
                method_name = method_match.group(1)
                qualified_name = f"{current_class}::{method_name}" if current_class else method_name
                symbols.append(Declaration(
                    kind="function",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for property declaration
            if property_match := self.property_pattern.search(line):
                property_name = property_match.group(1)
                qualified_name = f"{current_class}::{property_name}" if current_class else property_name
                symbols.append(Declaration(
                    kind="symbol",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))

            # Check for constant declaration
            if const_match := self.const_pattern.search(line):
                const_name = const_match.group(1)
                qualified_name = f"{current_class}::{const_name}" if current_class else const_name
                symbols.append(Declaration(
                    kind="symbol",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))

            i += 1

        return symbols


def parse_php(file_path: str, content: str) -> List[Declaration]:
    """Parse PHP code and return declarations."""
    parser = PhpParser()
    return parser.parse(content)

---
"""Rust code parser for CodeConcat."""

import re
from typing import List, Dict, Pattern
from codeconcat.types import ParsedFileData, Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

class RustParser(BaseParser):
    """Rust language parser."""
    
    def _setup_patterns(self):
        """Set up Rust-specific patterns."""
        self.patterns = {
            'function': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?(?:async\s+)?)'  # Visibility and async
                r'fn\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Function name
                r'\s*(?:<[^>]*>)?'  # Optional generic parameters
                r'\s*\((?P<parameters>[^)]*)\)'  # Parameters
                r'(?:\s*->\s*(?P<return_type>[^{;]+))?'  # Optional return type
            ),
            'struct': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?)'  # Visibility
                r'struct\s+(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Struct name
                r'(?:\s*<[^>]*>)?'  # Optional generic parameters
            ),
            'enum': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?)'  # Visibility
                r'enum\s+(?P<enum_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Enum name
                r'(?:\s*<[^>]*>)?'  # Optional generic parameters
            ),
            'trait': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?(?:unsafe\s+)?)'  # Visibility and safety
                r'trait\s+(?P<trait_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Trait name
                r'(?:\s*<[^>]*>)?'  # Optional generic parameters
                r'(?:\s*:\s*(?P<super_traits>[^{]+))?'  # Optional super traits
            ),
            'impl': re.compile(
                r'^(?P<modifiers>(?:unsafe\s+)?)'  # Safety
                r'impl(?:\s*<[^>]*>)?\s*'  # Optional generic parameters
                r'(?P<impl_trait>(?:[^{]+)\s+for\s+)?'  # Optional trait being implemented
                r'(?P<impl_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Type name
                r'(?:\s*<[^>]*>)?'  # Optional generic parameters
            ),
            'const': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?)'  # Visibility
                r'const\s+(?P<const_name>[A-Z_][A-Z0-9_]*)'  # Constant name
                r'(?::\s*(?P<type>[^=]+))?'  # Type annotation
                r'\s*='  # Assignment
            ),
            'static': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?)'  # Visibility
                r'static\s+(?:mut\s+)?'  # Mutability
                r'(?P<static_name>[A-Z_][A-Z0-9_]*)'  # Static name
                r'(?::\s*(?P<type>[^=]+))?'  # Type annotation
                r'\s*='  # Assignment
            ),
            'type': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?)'  # Visibility
                r'type\s+(?P<type_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Type alias name
                r'(?:\s*<[^>]*>)?'  # Optional generic parameters
                r'(?:\s*=\s*(?P<type_value>[^;]+))?'  # Type value
            ),
            'macro': re.compile(
                r'^(?P<modifiers>(?:#\[macro_export\]\s*)?)'  # Export attribute
                r'macro_rules!\s+(?P<macro_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Macro name
            ),
            'module': re.compile(
                r'^(?P<modifiers>(?:pub\s+)?)'  # Visibility
                r'mod\s+(?P<module_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Module name
            )
        }
        
        self.modifiers = {
            'pub', 'async', 'unsafe', 'mut', 'const', 'static', 
            'extern', 'default', '#[macro_export]'
        }
        self.block_start = '{'
        self.block_end = '}'
        self.line_comment = '//'
        self.block_comment_start = '/*'
        self.block_comment_end = '*/'
        
    def parse(self, content: str) -> List[Declaration]:
        """Parse Rust code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_impl = None
        pending_attributes = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle attributes
            if line.startswith('#['):
                pending_attributes.append(line)
                i += 1
                continue
                
            # Handle comments
            if line.startswith('//'):
                i += 1
                continue
                
            if '/*' in line and not in_comment:
                in_comment = True
                if '*/' in line[line.index('/*'):]:
                    in_comment = False
                i += 1
                continue
                
            if in_comment:
                if '*/' in line:
                    in_comment = False
                i += 1
                continue
                
            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name_group = f'{kind}_name'
                    name = match.group(name_group)
                    modifiers = set()
                    if 'modifiers' in match.groupdict() and match.group('modifiers'):
                        modifiers = {m.strip() for m in match.group('modifiers').split()}
                    modifiers.update(pending_attributes)
                    pending_attributes = []
                    
                    # Create symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=i,
                        modifiers=modifiers,
                        parent=current_impl if kind == 'function' else None
                    )
                    
                    # Handle block-level constructs
                    if '{' in line:
                        brace_count = line.count('{')
                        j = i + 1
                        while j < len(lines) and brace_count > 0:
                            line = lines[j].strip()
                            if not line.startswith('//'):
                                brace_count += line.count('{') - line.count('}')
                            j += 1
                        symbol.end_line = j - 1
                        i = j - 1
                        
                        # Update current impl context
                        if kind == 'impl':
                            current_impl = symbol
                    
                    symbols.append(symbol)
                    break
            
            i += 1
        
        # Convert to Declarations for backward compatibility
        return [
            Declaration(
                symbol.kind,
                symbol.name,
                symbol.start_line + 1,
                symbol.end_line + 1
            ) for symbol in symbols
        ]

def parse_rust_code(file_path: str, content: str) -> ParsedFileData:
    """Parse Rust code and return ParsedFileData."""
    parser = RustParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="rust",
        content=content,
        declarations=declarations
    )

---
"""JavaScript and TypeScript code parser for CodeConcat."""

import re
from typing import List, Dict, Pattern
from codeconcat.types import ParsedFileData, Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

class JstsParser(BaseParser):
    """JavaScript/TypeScript language parser."""
    
    def __init__(self, language: str = "javascript"):
        self.language = language  # Set language before calling super()
        super().__init__()
        self._setup_patterns()
        
    def _setup_patterns(self):
        """Set up JavaScript/TypeScript patterns."""
        # Common patterns for both JS and TS
        base_patterns = {
            'class': re.compile(
                r'^(?P<modifiers>(?:export\s+)?(?:default\s+)?)'  # Export/default modifiers
                r'class\s+(?P<class_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Class name
                r'(?:\s+extends\s+(?P<extends_name>[a-zA-Z_$][a-zA-Z0-9_$]*))?'  # Optional extends
                r'(?:\s+implements\s+(?P<implements_names>[a-zA-Z_$][a-zA-Z0-9_$]*(?:\s*,\s*[a-zA-Z_$][a-zA-Z0-9_$]*)*))?'  # Optional implements
            ),
            'function': re.compile(
                r'^(?P<modifiers>(?:export\s+)?(?:default\s+)?(?:async\s+)?)'  # Modifiers
                r'(?:function\s+)?(?P<function_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Function name
                r'\s*\((?P<parameters>[^)]*)\)'  # Parameters
                r'(?:\s*:\s*(?P<return_type>[^{;]+))?'  # Optional return type (TS)
            ),
            'method': re.compile(
                r'^(?P<modifiers>(?:public|private|protected|static|readonly|async)\s+)*'  # Method modifiers
                r'(?P<method_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Method name
                r'\s*\((?P<parameters>[^)]*)\)'  # Parameters
                r'(?:\s*:\s*(?P<return_type>[^{;]+))?'  # Optional return type (TS)
            ),
            'variable': re.compile(
                r'^(?P<modifiers>(?:export\s+)?(?:const|let|var)\s+)'  # Variable modifiers
                r'(?P<variable_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Variable name
                r'(?:\s*:\s*(?P<type_annotation>[^=;]+))?'  # Optional type annotation (TS)
                r'\s*=\s*'  # Assignment
            ),
            'interface': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Export modifier
                r'interface\s+(?P<interface_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Interface name
                r'(?:\s+extends\s+(?P<extends_names>[a-zA-Z_$][a-zA-Z0-9_$]*(?:\s*,\s*[a-zA-Z_$][a-zA-Z0-9_$]*)*))?'  # Optional extends
            ),
            'type': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Export modifier
                r'type\s+(?P<type_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Type name
                r'\s*=\s*(?P<type_value>.*)'  # Type assignment
            )
        }
        
        # TypeScript-specific patterns
        if self.language == "typescript":
            base_patterns.update({
                'enum': re.compile(
                    r'^(?P<modifiers>(?:export\s+)?(?:const\s+)?)'  # Modifiers
                    r'enum\s+(?P<enum_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Enum name
                ),
                'decorator': re.compile(
                    r'^@(?P<decorator_name>[a-zA-Z_$][a-zA-Z0-9_$]*)'  # Decorator name
                    r'(?:\s*\((?P<parameters>[^)]*)\))?'  # Optional parameters
                )
            })
        
        self.patterns = base_patterns
        self.modifiers = {
            'export', 'default', 'async', 'static', 'public', 'private', 
            'protected', 'readonly', 'abstract', 'declare'
        }
        self.block_start = '{'
        self.block_end = '}'
        self.line_comment = '//'
        self.block_comment_start = '/*'
        self.block_comment_end = '*/'
        
    def parse(self, content: str) -> List[Declaration]:
        """Parse JavaScript/TypeScript code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        in_template = False
        pending_decorators = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle comments
            if line.startswith('//'):
                i += 1
                continue
                
            if '/*' in line and not in_template:
                in_comment = True
                if '*/' in line[line.index('/*'):]:
                    in_comment = False
                i += 1
                continue
                
            if in_comment:
                if '*/' in line:
                    in_comment = False
                i += 1
                continue
                
            # Handle template literals
            if '`' in line:
                in_template = not in_template
                
            if in_template:
                i += 1
                continue
                
            # Handle decorators (TypeScript)
            if self.language == "typescript" and line.startswith('@'):
                pending_decorators.append(line)
                i += 1
                continue
                
            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    try:
                        name = match.group(f'{kind}_name')
                        modifiers = set()
                        if 'modifiers' in match.groupdict() and match.group('modifiers'):
                            modifiers = {m.strip() for m in match.group('modifiers').split()}
                        modifiers.update(pending_decorators)
                        pending_decorators = []
                        
                        # Track braces for block scope
                        brace_count += line.count('{') - line.count('}')
                        
                        symbol = CodeSymbol(
                            name=name,
                            kind=kind,
                            start_line=i,
                            end_line=i,
                            modifiers=modifiers,
                            parent=None
                        )
                        
                        # Find end of block
                        if '{' in line:
                            j = i + 1
                            while j < len(lines) and brace_count > 0:
                                brace_count += lines[j].count('{') - lines[j].count('}')
                                j += 1
                            symbol.end_line = j - 1
                            i = j - 1
                        
                        symbols.append(symbol)
                        break
                    except IndexError:
                        # Skip if the name group doesn't exist
                        continue
            
            i += 1
        
        # Convert to Declarations for backward compatibility
        return [
            Declaration(
                symbol.kind,
                symbol.name,
                symbol.start_line + 1,
                symbol.end_line + 1
            ) for symbol in symbols
        ]

def parse_javascript_or_typescript(file_path: str, content: str, language: str = "javascript") -> ParsedFileData:
    """Parse JavaScript or TypeScript code and return ParsedFileData."""
    parser = JstsParser(language)
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language=language,
        content=content,
        declarations=declarations
    )

---
"""Python code parser for CodeConcat."""

import re
from typing import List, Dict, Pattern
from codeconcat.types import ParsedFileData, Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

class PythonParser(BaseParser):
    """Python language parser."""
    
    def _setup_patterns(self):
        """Set up Python-specific patterns."""
        self.patterns = {
            'class': re.compile(
                r'^(?P<modifiers>(?:@\w+\s+)*)'  # Decorators
                r'class\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Class name
                r'\s*(?:\([^)]*\))?\s*:'  # Optional parent class
            ),
            'function': re.compile(
                r'^(?P<modifiers>(?:@\w+\s+)*)'  # Decorators
                r'(?:async\s+)?def\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Function name
                r'\s*\([^)]*\)\s*(?:->[^:]+)?:'  # Args and optional return type
            ),
            'constant': re.compile(
                r'^(?P<name>[A-Z][A-Z0-9_]*)\s*='  # Constants (UPPER_CASE)
            ),
            'variable': re.compile(
                r'^(?P<name>[a-z][a-z0-9_]*)\s*='  # Variables (lower_case)
                r'(?!.*(?:def|class)\s)'  # Not part of function/class definition
            )
        }
        
        self.modifiers = {'@classmethod', '@staticmethod', '@property', '@abstractmethod'}
        self.block_start = ':'
        self.block_end = None  # Python uses indentation
        self.line_comment = '#'
        self.block_comment_start = '"""'
        self.block_comment_end = '"""'
        
    def parse(self, content: str) -> List[Declaration]:
        """Parse Python code content."""
        lines = content.split('\n')
        symbols = []
        indent_stack = [0]
        current_indent = 0
        pending_decorators = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith(self.line_comment):
                i += 1
                continue
            
            # Handle docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                doc_end = self._find_docstring_end(lines, i)
                if doc_end > i:
                    if self.current_symbol and not self.current_symbol.docstring:
                        self.current_symbol.docstring = '\n'.join(lines[i:doc_end+1])
                    i = doc_end + 1
                    continue
            
            # Collect decorators
            if stripped.startswith('@'):
                pending_decorators.append(stripped)
                i += 1
                continue
            
            # Calculate indentation
            current_indent = len(line) - len(stripped)
            
            # Handle dedents
            while current_indent < indent_stack[-1]:
                indent_stack.pop()
                if self.symbol_stack:
                    symbol = self.symbol_stack.pop()
                    symbol.end_line = i - 1
                    symbols.append(symbol)
            
            # Look for new definitions
            for kind, pattern in self.patterns.items():
                match = pattern.match(stripped)
                if match:
                    name = match.group('name')
                    modifiers = set(pending_decorators)
                    pending_decorators = []  # Clear pending decorators
                    
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i - len(modifiers),  # Account for decorators
                        end_line=i,
                        modifiers=modifiers,
                        parent=self.symbol_stack[-1] if self.symbol_stack else None
                    )
                    
                    if kind in ('class', 'function'):
                        indent_stack.append(current_indent)
                        self.symbol_stack.append(symbol)
                    else:
                        symbols.append(symbol)
                    break
            else:
                # If no pattern matched, clear pending decorators
                pending_decorators = []
            
            i += 1
        
        # Close any remaining open symbols
        while self.symbol_stack:
            symbol = self.symbol_stack.pop()
            symbol.end_line = len(lines) - 1
            symbols.append(symbol)
        
        # Convert to Declarations for backward compatibility
        return [
            Declaration(
                symbol.kind,
                symbol.name,
                symbol.start_line + 1,
                symbol.end_line + 1
            ) for symbol in symbols
        ]
    
    def _find_docstring_end(self, lines: List[str], start: int) -> int:
        """Find the end of a docstring."""
        quote = '"""' if lines[start].strip().startswith('"""') else "'''"
        for i in range(start + 1, len(lines)):
            if quote in lines[i]:
                return i
        return start

def parse_python(file_path: str, content: str) -> ParsedFileData:
    """Parse Python code and return ParsedFileData."""
    parser = PythonParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="python",
        content=content,
        declarations=declarations
    )

---
"""Base parser class for language-specific parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Tuple, Set
import re

@dataclass
class CodeSymbol:
    """Represents a code symbol (function, class, etc.)."""
    name: str
    kind: str
    start_line: int
    end_line: int
    modifiers: Set[str]
    parent: Optional['CodeSymbol'] = None
    children: List['CodeSymbol'] = None
    docstring: Optional[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

class BaseParser(ABC):
    """Base class for all language parsers."""
    
    def __init__(self):
        self.symbols: List[CodeSymbol] = []
        self.current_symbol: Optional[CodeSymbol] = None
        self.symbol_stack: List[CodeSymbol] = []
        self._setup_patterns()

    @abstractmethod
    def _setup_patterns(self):
        """Set up regex patterns for the specific language."""
        self.patterns: Dict[str, Pattern] = {}
        self.modifiers: Set[str] = set()
        self.block_start: str = '{'
        self.block_end: str = '}'
        self.line_comment: str = '//'
        self.block_comment_start: str = '/*'
        self.block_comment_end: str = '*/'

    def parse(self, content: str) -> List[Tuple[str, int, int]]:
        """Parse code content and return symbols."""
        self.symbols = []
        self.current_symbol = None
        self.symbol_stack = []
        
        lines = content.split('\n')
        in_comment = False
        brace_count = 0
        comment_buffer = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Handle comments
            if self.block_comment_start in line and not in_comment:
                in_comment = True
                comment_start = line.index(self.block_comment_start)
                comment_buffer.append(line[comment_start + 2:])
                continue
                
            if in_comment:
                if self.block_comment_end in line:
                    in_comment = False
                    comment_end = line.index(self.block_comment_end)
                    comment_buffer.append(line[:comment_end])
                    if self.current_symbol and not self.current_symbol.docstring:
                        self.current_symbol.docstring = '\n'.join(comment_buffer).strip()
                    comment_buffer = []
                else:
                    comment_buffer.append(line)
                continue
                
            if stripped_line.startswith(self.line_comment):
                continue
                
            # Track braces for block detection
            if not self.current_symbol:
                # Look for new symbol definitions
                for kind, pattern in self.patterns.items():
                    match = pattern.match(line)
                    if match:
                        name = match.group('name')
                        modifiers = set(m.strip() for m in match.group('modifiers').split()) \
                                  if 'modifiers' in match.groupdict() else set()
                        
                        symbol = CodeSymbol(
                            name=name,
                            kind=kind,
                            start_line=i,
                            end_line=i,
                            modifiers=modifiers & self.modifiers
                        )
                        
                        if self.symbol_stack:
                            symbol.parent = self.symbol_stack[-1]
                            self.symbol_stack[-1].children.append(symbol)
                            
                        self.current_symbol = symbol
                        self.symbol_stack.append(symbol)
                        break
                        
            # Track block boundaries
            brace_count += line.count(self.block_start) - line.count(self.block_end)
            
            # Handle end of block
            if self.current_symbol and brace_count == 0:
                if self.block_end in line or ';' in line:
                    self.current_symbol.end_line = i
                    self.symbols.append(self.current_symbol)
                    self.symbol_stack.pop()
                    self.current_symbol = self.symbol_stack[-1] if self.symbol_stack else None
        
        # Convert to the expected tuple format for backward compatibility
        return [(s.name, s.start_line, s.end_line) for s in self.symbols]

    def _create_pattern(self, base_pattern: str, modifiers: Optional[List[str]] = None) -> Pattern:
        """Create a regex pattern with optional modifiers."""
        if modifiers:
            modifier_pattern = f"(?:(?:{' |'.join(modifiers)})\\s+)*"
            return re.compile(f"^\\s*{modifier_pattern}?{base_pattern}")
        return re.compile(f"^\\s*{base_pattern}")

    @staticmethod
    def extract_docstring(lines: List[str], start: int, end: int) -> Optional[str]:
        """Extract docstring from code lines."""
        for i in range(start, min(end + 1, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                doc_lines = []
                quote = line[:3]
                if line.endswith(quote) and len(line) > 3:
                    return line[3:-3].strip()
                doc_lines.append(line[3:])
                for j in range(i + 1, end + 1):
                    line = lines[j].strip()
                    if line.endswith(quote):
                        doc_lines.append(line[:-3])
                        return '\n'.join(doc_lines).strip()
                    doc_lines.append(line)
        return None

---
"""Java language parser for CodeConcat."""

from typing import List
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.types import Declaration


class JavaParser(BaseParser):
    """Java language parser."""

    def _setup_patterns(self):
        """Set up Java-specific patterns."""
        # Package pattern
        self.package_pattern = self._create_pattern(
            r'package\s+([\w.]+);'
        )

        # Import pattern
        self.import_pattern = self._create_pattern(
            r'import\s+(?:static\s+)?([\w.*]+);'
        )

        # Class pattern (including abstract, final, and visibility modifiers)
        self.class_pattern = self._create_pattern(
            r'(?:public\s+|protected\s+|private\s+)?'
            r'(?:abstract\s+|final\s+)?'
            r'(?:class|interface|enum)\s+'
            r'(\w+)'
            r'(?:\s+extends\s+\w+)?'
            r'(?:\s+implements\s+[\w,\s]+)?'
            r'\s*{'
        )

        # Method pattern (including constructors)
        self.method_pattern = self._create_pattern(
            r'(?:public\s+|protected\s+|private\s+)?'
            r'(?:static\s+|final\s+|abstract\s+|synchronized\s+)*'
            r'(?:<[\w\s,<>]+>\s+)?'  # Generic type parameters
            r'(?:[\w.<>[\],\s]+\s+)?'  # Return type (optional for constructors)
            r'(\w+)'  # Method name
            r'\s*\([^)]*\)'  # Parameters
            r'(?:\s+throws\s+[\w,\s]+)?'  # Throws clause
            r'\s*(?:{|;)'  # Body or abstract method
        )

        # Field pattern
        self.field_pattern = self._create_pattern(
            r'(?:public\s+|protected\s+|private\s+)?'
            r'(?:static\s+|final\s+|volatile\s+|transient\s+)*'
            r'[\w.<>[\],\s]+\s+'  # Type
            r'(\w+)'  # Field name
            r'(?:\s*=\s*[^;]+)?;'  # Optional initialization
        )

        # Annotation pattern
        self.annotation_pattern = self._create_pattern(
            r'@(\w+)(?:\s*\([^)]*\))?'
        )

    def parse(self, content: str) -> List[Declaration]:
        """Parse Java code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_package = None
        current_class = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle block comments
            if line.startswith('/*'):
                in_comment = True
                if '*/' in line[2:]:
                    in_comment = False
                i += 1
                continue
            if in_comment:
                if '*/' in line:
                    in_comment = False
                i += 1
                continue
            
            # Skip line comments
            if line.startswith('//'):
                i += 1
                continue

            # Track braces for scope
            brace_count += line.count('{') - line.count('}')
            
            # Check for package declaration
            if package_match := self.package_pattern.search(line):
                current_package = package_match.group(1)
                i += 1
                continue

            # Check for class/interface/enum declaration
            if class_match := self.class_pattern.search(line):
                class_name = class_match.group(1)
                qualified_name = f"{current_package}.{class_name}" if current_package else class_name
                current_class = qualified_name
                symbols.append(Declaration(
                    kind="class",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for method declaration
            if method_match := self.method_pattern.search(line):
                method_name = method_match.group(1)
                qualified_name = f"{current_class}.{method_name}" if current_class else method_name
                symbols.append(Declaration(
                    kind="function",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for field declaration
            if field_match := self.field_pattern.search(line):
                field_name = field_match.group(1)
                qualified_name = f"{current_class}.{field_name}" if current_class else field_name
                symbols.append(Declaration(
                    kind="symbol",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))

            i += 1

        return symbols


def parse_java(file_path: str, content: str) -> List[Declaration]:
    """Parse Java code and return declarations."""
    parser = JavaParser()
    return parser.parse(content)

---
"""C++ code parser for CodeConcat."""

import re
from typing import List, Tuple

def parse_cpp_code(content: str) -> List[Tuple[str, int, int]]:
    """Parse C++ code to identify classes, functions, namespaces, and templates.
    
    Returns:
        List of tuples (symbol_name, start_line, end_line)
    """
    symbols = []
    lines = content.split('\n')
    
    # Patterns for C++ constructs
    patterns = {
        'class': r'^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'function': r'^\s*(?:template\s*<[^>]*>\s*)?(?:[a-zA-Z_][a-zA-Z0-9_:]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*(?:default|delete))?\s*(?:{\s*)?$',
        'namespace': r'^\s*namespace\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'enum': r'^\s*enum(?:\s+class)?\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'typedef': r'^\s*typedef\s+[^;]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;',
        'using': r'^\s*using\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
    }
    
    in_block = False
    block_start = 0
    block_name = ""
    brace_count = 0
    in_comment = False
    
    for i, line in enumerate(lines):
        # Handle multi-line comments
        if '/*' in line:
            in_comment = True
        if '*/' in line:
            in_comment = False
            continue
        if in_comment or line.strip().startswith('//'):
            continue
            
        # Skip preprocessor directives
        if line.strip().startswith('#'):
            continue
            
        # Track braces and blocks
        if not in_block:
            for construct, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    block_name = match.group(1)
                    block_start = i
                    in_block = True
                    brace_count = line.count('{') - line.count('}')
                    # Handle one-line definitions
                    if brace_count == 0 and ';' in line:
                        symbols.append((block_name, i, i))
                        in_block = False
                    break
        else:
            brace_count += line.count('{') - line.count('}')
            
        # Check if block ends
        if in_block and brace_count == 0 and ('}' in line or ';' in line):
            symbols.append((block_name, block_start, i))
            in_block = False
            
    return symbols

---
"""R code parser for CodeConcat."""

import re
from typing import List, Dict, Pattern
from codeconcat.types import ParsedFileData, Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

class RParser(BaseParser):
    """R language parser."""
    
    def _setup_patterns(self):
        """Set up R-specific patterns."""
        self.patterns = {
            'function': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Function name
                r'\s*<?-\s*function\s*\('  # Assignment and function declaration
            ),
            'class': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'setClass\s*\(\s*["\'](?P<class_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']'  # S4 class definition
            ),
            'method': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'setMethod\s*\(\s*["\'](?P<method_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']'  # S4 method definition
            ),
            'constant': re.compile(
                r'^(?P<const_name>[A-Z][A-Z0-9_]*)'  # Constant name
                r'\s*<?-\s*'  # Assignment
            ),
            'variable': re.compile(
                r'^(?P<var_name>[a-z][a-z0-9_.]*)'  # Variable name
                r'\s*<?-\s*(?!function)'  # Assignment, not a function
            ),
            'package': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'(?:library|require)\s*\(\s*["\']?(?P<package_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']?\s*\)'  # Package import
            )
        }
        
        self.modifiers = {'export'}
        self.block_start = '{'
        self.block_end = '}'
        self.line_comment = '#'
        self.block_comment_start = None  # R doesn't have block comments
        self.block_comment_end = None
        
    def parse(self, content: str) -> List[Declaration]:
        """Parse R code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        current_class = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                i += 1
                continue
                
            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name_group = f'{kind}_name'
                    name = match.group(name_group)
                    modifiers = set()
                    if 'modifiers' in match.groupdict() and match.group('modifiers'):
                        modifiers = {m.strip() for m in match.group('modifiers').split()}
                    
                    # Create symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=i,
                        modifiers=modifiers,
                        parent=current_class
                    )
                    
                    # Handle block-level constructs
                    if kind in ('function', 'class', 'method'):
                        # Find the end of the block
                        brace_count = line.count('{')
                        j = i + 1
                        while j < len(lines) and (brace_count > 0 or '{' not in line):
                            line = lines[j].strip()
                            brace_count += line.count('{') - line.count('}')
                            j += 1
                        
                        if j > i + 1:
                            symbol.end_line = j - 1
                            i = j - 1
                        
                        # Update current class context
                        if kind == 'class':
                            current_class = symbol
                    
                    symbols.append(symbol)
                    break
            
            i += 1
        
        # Convert to Declarations for backward compatibility
        return [
            Declaration(
                symbol.kind,
                symbol.name,
                symbol.start_line + 1,
                symbol.end_line + 1
            ) for symbol in symbols
        ]

def parse_r(file_path: str, content: str) -> ParsedFileData:
    """Parse R code and return ParsedFileData."""
    parser = RParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="r",
        content=content,
        declarations=declarations
    )

---
"""Go language parser for CodeConcat."""

from typing import List
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.types import Declaration


class GoParser(BaseParser):
    """Go language parser."""

    def _setup_patterns(self):
        """Set up Go-specific patterns."""
        # Package pattern
        self.package_pattern = self._create_pattern(
            r'package\s+(\w+)'
        )

        # Import pattern
        self.import_pattern = self._create_pattern(
            r'import\s+(?:\(\s*|\s*"?)([^"\s]+)"?'
        )

        # Function pattern (including methods)
        self.func_pattern = self._create_pattern(
            r'func\s+'  # func keyword
            r'(?:\([^)]+\)\s+)?'  # Optional receiver for methods
            r'(\w+)'  # Function name
            r'\s*\([^)]*\)'  # Parameters
            r'(?:\s*\([^)]*\)|\s+[\w.*\[\]{}<>,\s]+)?'  # Optional return type(s)
            r'\s*{'  # Function body start
        )

        # Type pattern (struct/interface)
        self.type_pattern = self._create_pattern(
            r'type\s+'
            r'(\w+)\s+'  # Type name
            r'(?:struct|interface)\s*{'  # Type kind
        )

        # Variable pattern (var/const)
        self.var_pattern = self._create_pattern(
            r'(?:var|const)\s+'
            r'(\w+)'  # Variable name
            r'(?:\s+[\w.*\[\]{}<>,\s]+)?'  # Optional type
            r'(?:\s*=\s*[^;]+)?'  # Optional value
        )

    def parse(self, content: str) -> List[Declaration]:
        """Parse Go code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_package = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle block comments
            if line.startswith('/*'):
                in_comment = True
                if '*/' in line[2:]:
                    in_comment = False
                i += 1
                continue
            if in_comment:
                if '*/' in line:
                    in_comment = False
                i += 1
                continue
            
            # Skip line comments
            if line.startswith('//'):
                i += 1
                continue

            # Track braces for scope
            brace_count += line.count('{') - line.count('}')
            
            # Check for package declaration
            if package_match := self.package_pattern.search(line):
                current_package = package_match.group(1)
                i += 1
                continue

            # Check for function/method declaration
            if func_match := self.func_pattern.search(line):
                func_name = func_match.group(1)
                qualified_name = f"{current_package}.{func_name}" if current_package else func_name
                symbols.append(Declaration(
                    kind="function",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for type declaration
            if type_match := self.type_pattern.search(line):
                type_name = type_match.group(1)
                qualified_name = f"{current_package}.{type_name}" if current_package else type_name
                symbols.append(Declaration(
                    kind="class",  # Using class for both struct and interface
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))
                i += 1
                continue

            # Check for variable/constant declaration
            if var_match := self.var_pattern.search(line):
                var_name = var_match.group(1)
                qualified_name = f"{current_package}.{var_name}" if current_package else var_name
                symbols.append(Declaration(
                    kind="symbol",
                    name=qualified_name,
                    start_line=i,
                    end_line=i
                ))

            i += 1

        return symbols


def parse_go(file_path: str, content: str) -> List[Declaration]:
    """Parse Go code and return declarations."""
    parser = GoParser()
    return parser.parse(content)

---
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

---

---
"""XML writer for CodeConcat output."""

from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
from codeconcat.types import ParsedFileData, ParsedDocData, AnnotatedFileData

def write_xml(
    code_files: List[ParsedFileData],
    doc_files: List[ParsedDocData],
    file_annotations: Dict[str, AnnotatedFileData],
    folder_tree: Optional[str] = None
) -> str:
    """Write the concatenated code and docs to an XML file."""
    
    root = ET.Element("codeconcat")
    
    # Add metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "total_files").text = str(len(code_files) + len(doc_files))
    ET.SubElement(metadata, "code_files").text = str(len(code_files))
    ET.SubElement(metadata, "doc_files").text = str(len(doc_files))
    
    # Add folder tree if present
    if folder_tree:
        tree_elem = ET.SubElement(root, "folder_tree")
        tree_elem.text = folder_tree
    
    # Add code files
    code_section = ET.SubElement(root, "code_files")
    for file in code_files:
        file_elem = ET.SubElement(code_section, "file")
        ET.SubElement(file_elem, "path").text = file.file_path
        ET.SubElement(file_elem, "language").text = file.language
        
        # Add annotations if available
        annotation = file_annotations.get(file.file_path)
        if annotation:
            annotations_elem = ET.SubElement(file_elem, "annotations")
            if annotation.summary:
                ET.SubElement(annotations_elem, "summary").text = annotation.summary
            if annotation.tags:
                tags_elem = ET.SubElement(annotations_elem, "tags")
                for tag in annotation.tags:
                    ET.SubElement(tags_elem, "tag").text = tag
        
        # Add code content with CDATA to preserve formatting
        content_elem = ET.SubElement(file_elem, "content")
        content_elem.text = f"<![CDATA[{file.content}]]>"
    
    # Add doc files
    if doc_files:
        docs_section = ET.SubElement(root, "doc_files")
        for doc in doc_files:
            doc_elem = ET.SubElement(docs_section, "file")
            ET.SubElement(doc_elem, "path").text = doc.file_path
            ET.SubElement(doc_elem, "format").text = doc.format
            content_elem = ET.SubElement(doc_elem, "content")
            content_elem.text = f"<![CDATA[{doc.content}]]>"
    
    # Convert to string with pretty printing
    xml_str = ET.tostring(root, encoding='unicode')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    return pretty_xml

---
"""AI context generation for CodeConcat output."""

from typing import List, Dict
from codeconcat.types import ParsedFileData, ParsedDocData, AnnotatedFileData

def generate_ai_preamble(
    code_files: List[ParsedFileData],
    doc_files: List[ParsedDocData],
    file_annotations: Dict[str, AnnotatedFileData]
) -> str:
    """Generate an AI-friendly preamble that explains the codebase structure and contents."""
    
    # Count files by type
    file_types = {}
    for file in code_files:
        ext = file.file_path.split('.')[-1] if '.' in file.file_path else 'unknown'
        file_types[ext] = file_types.get(ext, 0) + 1

    # Generate summary
    lines = [
        "# CodeConcat AI-Friendly Code Summary",
        "",
        "This document contains a structured representation of a codebase, organized for AI analysis.",
        "",
        "## Repository Structure",
        "```",
        f"Total code files: {len(code_files)}",
        f"Documentation files: {len(doc_files)}",
        "",
        "File types:",
    ]
    
    for ext, count in sorted(file_types.items()):
        lines.append(f"- {ext}: {count} files")
    
    lines.extend([
        "```",
        "",
        "## Code Organization",
        "The code is organized into sections, each prefixed with clear markers:",
        "- Directory markers show file organization",
        "- File headers contain metadata and imports",
        "- Annotations provide context about code purpose",
        "- Documentation sections contain project documentation",
        "",
        "## Navigation",
        "- Each file begins with '---FILE:' followed by its path",
        "- Each section is clearly delimited with markdown headers",
        "- Code blocks are formatted with appropriate language tags",
        "",
        "## Content Summary",
    ])

    # Add file listing
    for file in code_files:
        annotation = file_annotations.get(file.file_path, AnnotatedFileData(file.file_path, "", []))
        if annotation.summary:
            lines.append(f"- `{file.file_path}`: {annotation.summary}")

    lines.extend([
        "",
        "---",
        "Begin code content below:",
        ""
    ])

    return "\n".join(lines)

---
import json
from typing import List
from codeconcat.types import AnnotatedFileData, ParsedDocData, CodeConCatConfig

def write_json(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = ""
) -> str:
    data = {}

    # Add folder tree if present
    if folder_tree_str:
        data["folder_tree"] = folder_tree_str

    # Add code files if any
    if annotated_files:
        data["code"] = []
        for ann in annotated_files:
            data["code"].append({
                "file_path": ann.file_path,
                "language": ann.language,
                "content": ann.content,
                "annotated_content": ann.annotated_content,
                "summary": ann.summary,
                "tags": ann.tags
            })

    # Add docs if any
    if docs:
        data["docs"] = []
        for doc in docs:
            data["docs"].append({
                "file_path": doc.file_path,
                "doc_type": doc.doc_type,
                "content": doc.content
            })

    final_json = json.dumps(data, indent=2)

    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_json)

    print(f"[CodeConCat] JSON output written to: {config.output}")
    return final_json

---
