import argparse
import logging
import os
import sys
from typing import List

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData
from codeconcat.collector.github_collector import collect_github_files
from codeconcat.collector.local_collector import (
    collect_local_files,
    should_include_file,
    should_skip_dir,
)
from codeconcat.config.config_loader import load_config
from codeconcat.parser.doc_extractor import extract_docs
from codeconcat.parser.file_parser import parse_code_files
from codeconcat.transformer.annotator import annotate
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.xml_writer import write_xml

# Set up root logger
logger = logging.getLogger("codeconcat")
logger.setLevel(logging.WARNING)


class CodeConcatError(Exception):
    """Base exception class for CodeConCat errors."""
    pass

class ConfigurationError(CodeConcatError):
    """Raised when there's an error in the configuration."""
    pass

class FileProcessingError(CodeConcatError):
    """Raised when there's an error processing files."""
    pass

class OutputError(CodeConcatError):
    """Raised when there's an error generating output."""
    pass


def cli_entry_point():
    parser = argparse.ArgumentParser(
        prog="codeconcat",
        description="CodeConCat - An LLM-friendly code aggregator and doc extractor.",
    )

    parser.add_argument("target_path", nargs="?", default=".")
    parser.add_argument(
        "--github", help="GitHub URL or shorthand (e.g., 'owner/repo')", default=None
    )
    parser.add_argument("--github-token", help="GitHub personal access token", default=None)
    parser.add_argument("--ref", help="Branch, tag, or commit hash for GitHub repo", default=None)

    parser.add_argument("--docs", action="store_true", help="Enable doc extraction")
    parser.add_argument(
        "--merge-docs", action="store_true", help="Merge doc content with code output"
    )

    parser.add_argument("--output", default="code_concat_output.md", help="Output file name")
    parser.add_argument(
        "--format", choices=["markdown", "json", "xml"], default="markdown", help="Output format"
    )

    parser.add_argument("--include", nargs="*", default=[], help="Glob patterns to include")
    parser.add_argument("--exclude", nargs="*", default=[], help="Glob patterns to exclude")
    parser.add_argument(
        "--include-languages", nargs="*", default=[], help="Only include these languages"
    )
    parser.add_argument(
        "--exclude-languages", nargs="*", default=[], help="Exclude these languages"
    )

    parser.add_argument("--max-workers", type=int, default=4, help="Number of worker threads")
    parser.add_argument("--init", action="store_true", help="Initialize default configuration file")

    parser.add_argument(
        "--no-tree", action="store_true", help="Disable folder tree generation (enabled by default)"
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Disable copying output to clipboard (enabled by default)",
    )
    parser.add_argument(
        "--no-ai-context", action="store_true", help="Disable AI context generation"
    )
    parser.add_argument("--no-annotations", action="store_true", help="Disable code annotations")
    parser.add_argument("--no-symbols", action="store_true", help="Disable symbol extraction")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        # Also set debug for all codeconcat loggers
        for name in logging.root.manager.loggerDict:
            if name.startswith("codeconcat"):
                logging.getLogger(name).setLevel(logging.DEBUG)

    # Create console handler if not already present
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG if args.debug else logging.WARNING)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    logger.debug("Debug logging enabled")

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
    from codeconcat.collector.local_collector import should_include_file, should_skip_dir

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
        dirs[:] = [
            d for d in dirs if not should_skip_dir(os.path.join(root, d), config.exclude_paths)
        ]
        dirs.sort()  # Sort directories for consistent output

    return "\n".join(lines)


def run_codeconcat(config: CodeConCatConfig):
    """Main execution function for CodeConCat."""
    try:
        # Validate configuration
        if not config.target_path:
            raise ConfigurationError("Target path is required")
        if config.format not in ["markdown", "json", "xml"]:
            raise ConfigurationError(f"Invalid format: {config.format}")

        # Collect files
        try:
            if config.github_url:
                code_files = collect_github_files(config)
            else:
                code_files = collect_local_files(config.target_path, config)
                
            if not code_files:
                raise FileProcessingError("No files found to process")
        except Exception as e:
            raise FileProcessingError(f"Error collecting files: {str(e)}")

        # Generate folder tree if enabled
        folder_tree_str = ""
        if not config.disable_tree:
            try:
                folder_tree_str = generate_folder_tree(config.target_path, config)
            except Exception as e:
                print(f"Warning: Failed to generate folder tree: {str(e)}")

        # Parse code files
        try:
            parsed_files = parse_code_files([f.file_path for f in code_files], config)
            if not parsed_files:
                raise FileProcessingError("No files were successfully parsed")
        except Exception as e:
            raise FileProcessingError(f"Error parsing files: {str(e)}")

        # Extract docs if requested
        docs = []
        if config.extract_docs:
            try:
                docs = extract_docs([f.file_path for f in code_files], config)
            except Exception as e:
                print(f"Warning: Failed to extract documentation: {str(e)}")

        # Annotate files if enabled
        try:
            annotated_files = []
            if not config.disable_annotations:
                for file in parsed_files:
                    try:
                        annotated = annotate(file, config)
                        annotated_files.append(annotated)
                    except Exception as e:
                        print(f"Warning: Failed to annotate {file.file_path}: {str(e)}")
                        # Fall back to basic annotation
                        annotated_files.append(
                            AnnotatedFileData(
                                file_path=file.file_path,
                                language=file.language,
                                content=file.content,
                                annotated_content=file.content,
                                summary="",
                                tags=[],
                            )
                        )
            else:
                # Create basic annotations without AI analysis
                for file in parsed_files:
                    annotated_files.append(
                        AnnotatedFileData(
                            file_path=file.file_path,
                            language=file.language,
                            content=file.content,
                            annotated_content=file.content,
                            summary="",
                            tags=[],
                        )
                    )
        except Exception as e:
            raise FileProcessingError(f"Error during annotation: {str(e)}")

        # Write output in requested format
        try:
            if config.format == "markdown":
                output = write_markdown(annotated_files, docs, config, folder_tree_str)
            elif config.format == "json":
                output = write_json(annotated_files, docs, config, folder_tree_str)
            elif config.format == "xml":
                output = write_xml(
                    parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str
                )
        except Exception as e:
            raise OutputError(f"Error generating {config.format} output: {str(e)}")

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

    except CodeConcatError as e:
        print(f"[CodeConCat] Error: {str(e)}")
        raise
    except Exception as e:
        print(f"[CodeConCat] Unexpected error: {str(e)}")
        raise


def run_codeconcat_in_memory(config: CodeConCatConfig) -> str:
    """Run CodeConCat and return the output as a string."""
    try:
        if config.disable_copy is None:
            config.disable_copy = True  # Always disable clipboard in memory mode
            
        # Process code
        if config.github_url:
            code_files = collect_github_files(config)
        else:
            code_files = collect_local_files(config.target_path, config)

        if not code_files:
            raise FileProcessingError("No files found to process")

        # Generate folder tree
        folder_tree_str = ""
        if not config.disable_tree:
            folder_tree_str = generate_folder_tree(config.target_path, config)

        # Parse and process files
        parsed_files = parse_code_files([f.file_path for f in code_files], config)
        if not parsed_files:
            raise FileProcessingError("No files were successfully parsed")

        # Extract docs if requested
        docs = []
        if config.extract_docs:
            docs = extract_docs([f.file_path for f in code_files], config)

        # Annotate files
        annotated_files = []
        if not config.disable_annotations:
            for file in parsed_files:
                try:
                    annotated = annotate(file, config)
                    annotated_files.append(annotated)
                except Exception as e:
                    print(f"Warning: Failed to annotate {file.file_path}: {str(e)}")
                    # Fall back to basic annotation
                    annotated_files.append(
                        AnnotatedFileData(
                            file_path=file.file_path,
                            language=file.language,
                            content=file.content,
                            annotated_content=file.content,
                            summary="",
                            tags=[],
                        )
                    )
        else:
            for file in parsed_files:
                annotated_files.append(
                    AnnotatedFileData(
                        file_path=file.file_path,
                        language=file.language,
                        content=file.content,
                        annotated_content=file.content,
                        summary="",
                        tags=[],
                    )
                )

        # Generate output in requested format
        if config.format == "markdown":
            return write_markdown(annotated_files, docs, config, folder_tree_str)
        elif config.format == "json":
            return write_json(annotated_files, docs, config, folder_tree_str)
        elif config.format == "xml":
            return write_xml(
                parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str
            )
        else:
            raise ConfigurationError(f"Invalid format: {config.format}")

    except Exception as e:
        error_msg = f"Error processing code: {str(e)}"
        print(f"[CodeConCat] {error_msg}")
        raise CodeConcatError(error_msg) from e


def main():
    cli_entry_point()


if __name__ == "__main__":
    main()
