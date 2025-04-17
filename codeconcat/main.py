import argparse
import logging
import os
import sys
import importlib.resources # Import importlib.resources
from typing import Any, Dict, List, Optional

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
)
from codeconcat.collector.github_collector import collect_github_files
from codeconcat.collector.local_collector import collect_local_files
from codeconcat.config.config_loader import load_config
from codeconcat.parser.doc_extractor import extract_docs
from codeconcat.parser.file_parser import parse_code_files
from codeconcat.transformer.annotator import annotate
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.xml_writer import write_xml
from .version import __version__  # Import version

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
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Improved help format
    )

    # --- Argument Groups ---
    input_group = parser.add_argument_group('Input Source')
    filter_group = parser.add_argument_group('Filtering Options')
    output_group = parser.add_argument_group('Output Options')
    feature_group = parser.add_argument_group('Feature Toggles')
    processing_group = parser.add_argument_group('Processing Control')
    misc_group = parser.add_argument_group('Miscellaneous')
    # ----------------------

    # --- Version Flag (#35) ---
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    # -------------------------

    # --- Input Source Group ---
    input_group.add_argument(
        "target_path",
        nargs="?",
        default=".",
        help="Local directory path to process."
    )
    input_group.add_argument(
        "--github",
        help="GitHub URL or shorthand (e.g., 'owner/repo') to process instead of local path.",
        default=None
    )
    input_group.add_argument(
        "--github-token",
        help="GitHub personal access token (required for private repos).",
        default=None
    )
    input_group.add_argument(
        "--ref",
        help="Branch, tag, or commit hash for GitHub repo.",
        default=None
    )
    # --------------------------

    # --- Filtering Group ---
    filter_group.add_argument(
        "--include",
        nargs="*",
        default=[],
        help="Glob patterns for files/directories to include explicitly."
    )
    filter_group.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Glob patterns for files/directories to exclude."
    )
    filter_group.add_argument(
        "--include-languages",
        nargs="*",
        default=[],
        help="Only include files matching these languages (e.g., 'python', 'javascript')."
    )
    filter_group.add_argument(
        "--exclude-languages",
        nargs="*",
        default=[],
        help="Exclude files matching these languages."
    )
    # ----------------------

    # --- Output Options Group ---
    output_group.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path. Default: code_concat_output.<format>"
    )
    output_group.add_argument(
        "--format",
        default=None, choices=["markdown", "json", "xml"],
        help="Output format. Default: markdown"
    )
    output_group.add_argument(
        "--sort-files",
        action="store_true",
        help="Sort files alphabetically by path in the output."
    )
    output_group.add_argument(
        "--split-output",
        type=int,
        default=1,
        metavar="X",
        help="Split the output into X approximately equal files (requires X > 1)."
    )
    # ------------------------------

    # --- Feature Toggles Group ---
    feature_group.add_argument(
        "--docs",
        action="store_true",
        help="Enable extraction and inclusion of separate documentation files."
    )
    feature_group.add_argument(
        "--merge-docs",
        action="store_true",
        help="Merge documentation content directly into the main code output file."
    )
    feature_group.add_argument(
        "--no-tree",
        action="store_true",
        help="Disable generation of the folder tree structure in the output."
    )
    feature_group.add_argument(
        "--no-ai-context",
        action="store_true",
        help="Disable the AI-friendly preamble/context generation at the start of the output."
    )
    feature_group.add_argument(
        "--no-annotations",
        action="store_true",
        help="Disable processing and inclusion of code annotations."
    )
    feature_group.add_argument(
        "--no-symbols",
        action="store_true",
        help="Disable extraction and listing of code symbols (functions, classes)."
    )
    feature_group.add_argument(
        "--remove-docstrings",
        action="store_true",
        help="Remove docstrings from the code content in the output."
    )
    # --------------------------

    # --- Processing Control Group ---
    processing_group.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of worker threads for parallel processing."
    )
    # ------------------------------

    # --- Miscellaneous Group ---
    misc_group.add_argument(
        "--init",
        action="store_true",
        help="Initialize a default '.codeconcat.yml' configuration file in the current directory."
    )
    misc_group.add_argument(
        "--show-config", # Added flag (#27)
        action="store_true",
        help="Display the final merged configuration and exit."
    )
    misc_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging."
    )
    # --------------------------

    args = parser.parse_args()

    # Setup logging based on debug flag BEFORE any potential config loading for show-config
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='[%(levelname)s] %(message)s')
    logger.setLevel(log_level)

    # Handle initialization request
    if args.init:
        create_default_config()
        logger.info("Created default configuration file: .codeconcat.yml")
        sys.exit(0)

    # Handle --show-config request (#27)
    if args.show_config:
        try:
            cli_args_dict = {k: v for k, v in vars(args).items() if v is not None} # Filter out None values
            logger.info("Loading configuration to display...")
            # Pass only non-None CLI args to avoid overriding defaults unnecessarily
            final_config = load_config(cli_args_dict)
            print("--- Final Merged Configuration ---")
            # Pydantic models have a good default string representation
            print(final_config)
            print("----------------------------------")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error loading configuration for display: {e}")
            sys.exit(1)

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
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    logger.debug("Debug logging enabled")

    # Load config, with CLI args taking precedence
    cli_args = vars(args)
    logging.debug("CLI args: %s", cli_args)  # Debug print
    config = load_config(cli_args)

    try:
        # Generate the full output string
        full_output_content = run_codeconcat(config)

        # Determine final output base path
        output_base_path = config.output
        if output_base_path is None:
             # Construct default if not provided via CLI or config file
             output_base_path = f"code_concat_output.{config.format}"

        num_splits = config.split_output
        output_format = config.format

        # --- Write output to file(s) --- #
        files_written_paths = []
        can_split = num_splits > 1 and output_format == 'markdown'

        if num_splits > 1 and not can_split:
            logger.warning(f"Output splitting requested but only supported for Markdown. Writing to single file: {output_base_path}")

        if not can_split:
            # Write to a single file
            try:
                with open(output_base_path, "w", encoding="utf-8") as f:
                    f.write(full_output_content)
                logger.info(f"Output successfully written to {output_base_path}")
                files_written_paths.append(output_base_path)
            except IOError as e:
                logger.error(f"Failed to write output to {output_base_path}: {e}")
                sys.exit(1)
        else:
            # Split Markdown content and write to multiple files
            logger.info(f"Splitting Markdown output into {num_splits} files...")
            lines = full_output_content.splitlines(keepends=True)
            total_lines = len(lines)
            lines_per_file = (total_lines + num_splits - 1) // num_splits # Ceiling division

            base, ext = os.path.splitext(output_base_path)

            for i in range(num_splits):
                start_index = i * lines_per_file
                end_index = min((i + 1) * lines_per_file, total_lines)
                if start_index >= total_lines: break # Avoid empty files

                chunk_content = "".join(lines[start_index:end_index])
                split_filename = f"{base}_part_{i+1}{ext}"

                try:
                    with open(split_filename, "w", encoding="utf-8") as f:
                        f.write(chunk_content)
                    files_written_paths.append(split_filename)
                except IOError as e:
                    logger.error(f"Failed to write output chunk to {split_filename}: {e}")
                    sys.exit(1)

            logger.info(f"Output successfully split and written to: {', '.join(files_written_paths)}")

        # --- Handle clipboard copy (after successful write) --- #
        if files_written_paths and not config.disable_copy:
             if not can_split: # Only copy if output is single file
                try:
                    import pyperclip
                    pyperclip.copy(full_output_content)
                    logger.info("Output copied to clipboard.")
                except ImportError:
                    logger.warning("pyperclip not installed, skipping clipboard copy.")
                except Exception as e:
                    logger.warning(f"Failed to copy to clipboard: {e}")
             else:
                logger.info("Clipboard copy skipped as output was split into multiple files.")

    except CodeConcatError as e:
        # Log known operational errors
        logger.error(f"Operation failed: {e}")
        print(f"[CodeConCat] Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Log unexpected errors
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"[CodeConCat] Unexpected Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def create_default_config():
    """Create a default .codeconcat.yml configuration file from the template."""
    target_path = ".codeconcat.yml"
    if os.path.exists(target_path):
        logger.warning(f"Configuration file '{target_path}' already exists. Remove it first to create a new one.")
        return

    try:
        # Read the content from the template file within the package
        template_content = importlib.resources.read_text('codeconcat.config', 'default_config.template.yml')

        with open(target_path, "w") as f:
            f.write(template_content)

        # Use logger instead of print
        logger.info(f"Created default configuration file: {target_path}")

    except FileNotFoundError:
        logger.error("Default configuration template not found within the package.")
    except Exception as e:
        logger.error(f"Failed to create default configuration file: {e}")


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
        included_files = [
            f for f in files if should_include_file(os.path.join(root, f), config)
        ]

        sub_indent = "    " * (level + 1)
        for f in sorted(included_files):
            lines.append(f"{sub_indent}{f}")

        # Filter directories for the next iteration
        dirs[:] = [
            d
            for d in dirs
            if not should_skip_dir(os.path.join(root, d), config.exclude_paths)
        ]
        dirs.sort()  # Sort directories for consistent output

    return "\n".join(lines)


def run_codeconcat(config: CodeConCatConfig) -> str:
    """Main execution function for CodeConCat. Returns the generated output string."""
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

        # Sort files alphabetically if requested (#31)
        if config.sort_files:
            logger.info("Sorting files alphabetically by path...")
            annotated_files.sort(key=lambda f: f.file_path)
            logger.debug("Files sorted.")

        # Write output in requested format
        try:
            if config.format == "markdown":
                output = write_markdown(annotated_files, docs, config, folder_tree_str)
            elif config.format == "json":
                output = write_json(annotated_files, docs, config, folder_tree_str)
            elif config.format == "xml":
                output = write_xml(
                    parsed_files,
                    docs,
                    {f.file_path: f for f in annotated_files},
                    folder_tree_str,
                )
        except Exception as e:
            raise OutputError(f"Error generating {config.format} output: {str(e)}")

        # Return the generated output string
        return output

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
            from codeconcat.writer.ai_context import generate_ai_preamble
            from codeconcat.writer.markdown_writer import write_markdown

            output_chunks = []

            # Only generate AI preamble if not disabled
            if not config.disable_ai_context:
                ai_preamble = generate_ai_preamble(code_files, docs, annotated_files)
                if ai_preamble:
                    output_chunks.append(ai_preamble)

            output = write_markdown(
                annotated_files,
                docs,
                config,
                folder_tree_str,
            )
            if output:
                output_chunks.append(output)

            return "\n".join(output_chunks)
        elif config.format == "json":
            return write_json(annotated_files, docs, config, folder_tree_str)
        elif config.format == "xml":
            return write_xml(
                parsed_files,
                docs,
                {f.file_path: f for f in annotated_files},
                folder_tree_str,
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
