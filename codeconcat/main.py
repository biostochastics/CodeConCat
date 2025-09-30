#!/usr/bin/env python3
# SPDX‑License‑Identifier: MIT

"""
Main entry point for the CodeConCat CLI application.

This module handles command-line argument parsing, configuration loading,
file collection, processing, and output generation.
"""

import importlib.resources
import logging
import os  # Ensure os is imported at the global scope
import sys
import warnings
from pathlib import Path
from typing import List, Literal, Union

from rich.progress import track

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    ContentSegmentType,
    ParsedFileData,
    WritableItem,
)
from codeconcat.collector.github_collector import collect_git_repo
from codeconcat.collector.local_collector import collect_local_files
from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.diagnostics import diagnose_parser, verify_tree_sitter_dependencies
from codeconcat.errors import (
    CodeConcatError,
    ConfigurationError,
    FileProcessingError,
    ParserError,
    ValidationError,
)
from codeconcat.parser.doc_extractor import extract_docs
from codeconcat.parser.unified_pipeline import parse_code_files
from codeconcat.processor.compression_processor import CompressionProcessor
from codeconcat.quotes import get_random_quote
from codeconcat.reconstruction import reconstruct_from_file
from codeconcat.transformer.annotator import annotate
from codeconcat.validation.integration import (
    setup_semgrep,
    validate_config_values,
    validate_input_files,
    verify_file_signatures,
)
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.text_writer import write_text
from codeconcat.writer.xml_writer import write_xml

# Suppress HuggingFace warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow warnings
# Suppress transformers warnings about missing PyTorch/TensorFlow
warnings.filterwarnings("ignore", message="None of PyTorch.*have been found")

# ------------------------------------------------------------------------------
# Set up logging for CodeConCat
logger = logging.getLogger(__name__)


def configure_logging(
    log_level: Union[
        str, int, Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ] = "WARNING",
    debug: bool = False,
    quiet: bool = False,
) -> None:
    """Configure the logging system for CodeConCat.

    Sets up the logging infrastructure for the entire application with appropriate
    levels and formats. Handles special modes like debug and quiet operation.

    Args:
        log_level: The logging level to use. Can be a string (DEBUG, INFO, etc.) or an int.
        debug: If True, sets log level to DEBUG regardless of log_level parameter.
        quiet: If True, only shows ERROR level messages and disables progress bars.

    Complexity:
        O(1) - Fixed number of logger configurations

    Flow:
        Called by: cli_entry_point(), main()
        Calls: logging.basicConfig(), logging.getLogger()

    Security Notes:
        - Validates log level strings to prevent injection
        - Falls back to WARNING on invalid input
        - No sensitive data logged at INFO or below
    """
    # Determine the actual log level to use
    if debug:
        actual_level = logging.DEBUG
    elif quiet:
        actual_level = logging.ERROR
    elif isinstance(log_level, str):
        # Convert string log level to int
        try:
            actual_level = getattr(logging, log_level.upper())
        except AttributeError:
            # Invalid log level string, fall back to WARNING
            actual_level = logging.WARNING
            logger.error(f"Invalid log level: {log_level}. Using WARNING instead.")
    else:
        # Assume it's already a valid int level
        actual_level = log_level

    # Configure root logger
    logging.basicConfig(
        level=actual_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # When in quiet mode, make sure progress bars are disabled and adjust logging further
    if quiet:
        # Suppress internal logging for non-error messages
        # But leave handlers in place for actual errors
        for logger_name in [
            "codeconcat",
            "codeconcat.collector",
            "codeconcat.parser",
            "codeconcat.writer",
            "codeconcat.processor",
            "codeconcat.transformer",
        ]:
            logging.getLogger(logger_name).setLevel(logging.ERROR)

    # Only log this if not in quiet mode
    if not quiet:
        logger.info(f"Logging level set to: {logging.getLevelName(actual_level)}")

    # Suppress overly verbose logs from libraries if not in debug mode
    if actual_level != logging.DEBUG:
        logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("filelock").setLevel(logging.WARNING)
        logging.getLogger("tree_sitter").setLevel(logging.WARNING)
        logging.getLogger("tree_sitter_languages").setLevel(logging.WARNING)
        # Suppress INFO level messages from codeconcat modules by default
        # to reduce verbosity unless explicitly requested
        if actual_level == logging.WARNING:
            for logger_name in [
                "codeconcat.collector",
                "codeconcat.parser",
                "codeconcat.transformer",
                "codeconcat.writer",
            ]:
                logging.getLogger(logger_name).setLevel(logging.WARNING)


# ──────────────────────────────────────────────────────────────────────────────
# Exception hierarchy - import OutputError from errors
class OutputError(CodeConcatError):
    """Errors during output generation.

    Custom exception class for handling errors that occur during the output
    generation phase of CodeConCat processing. Inherits from CodeConcatError
    for consistent error handling across the application.

    Used When:
        - File write operations fail
        - Output formatting errors occur
        - Clipboard operations fail

    Flow:
        Raised by: _write_output_files(), run_codeconcat()
        Caught by: main(), cli_entry_point()
    """

    pass


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _write_output_files(output_text: str, config: CodeConCatConfig) -> None:
    # Import os in this scope to avoid any potential shadowing
    """Write the final concatenated output to one or more files.
    Handles splitting the output into multiple parts if requested in the config and optionally copies the content to the clipboard. Includes error handling for file operations and clipboard access.
    Parameters:
        - output_text (str): The complete string output generated by CodeConCat.
        - config (CodeConCatConfig): The CodeConCatConfig object containing output settings like output path, format, split_output, and disable_copy.
    Raises:
        - OutputError: If file writing fails
    Complexity:
        O(n) where n is the length of output_text when splitting
    Flow:
        Called by: run_codeconcat()
        Calls: open(), pyperclip.copy()
    Security Notes:
        - Uses specific exception types (ImportError, OSError) instead of broad catches
        - Validates output path from config
        - Safe file operations with proper encoding"""
    import os as local_os

    """Write the final concatenated output to one or more files.

    Handles splitting the output into multiple parts if requested in the config
    and optionally copies the content to the clipboard. Includes error handling
    for file operations and clipboard access.

    Args:
        output_text: The complete string output generated by CodeConCat.
        config: The CodeConCatConfig object containing output settings like
                output path, format, split_output, and disable_copy.

    Raises:
        OutputError: If file writing fails

    Complexity:
        O(n) where n is the length of output_text when splitting

    Flow:
        Called by: run_codeconcat()
        Calls: open(), pyperclip.copy()

    Security Notes:
        - Uses specific exception types (ImportError, OSError) instead of broad catches
        - Validates output path from config
        - Safe file operations with proper encoding
    """
    # Debug print to check what output path is set in config
    # print(f"[DEBUG OUTPUT] Config output path: '{config.output}'")

    # Use the output path from config directly
    output_path = config.output

    # This should not happen anymore since we set defaults in cli_entry_point,
    # but just in case...
    if not output_path:
        output_path = f"codeconcat_output.{config.format}"
        logger.warning(f"Output path was not set, using default: {output_path}")

    # Debug print the final output path
    # print(f"[DEBUG OUTPUT] Final output path: '{output_path}'")

    parts = max(1, getattr(config, "split_output", 1))

    if parts > 1 and config.format == "markdown":
        lines = output_text.splitlines(keepends=True)
        chunk_size = (len(lines) + parts - 1) // parts
        base, ext = local_os.path.splitext(output_path)

        # Wrap loop with track for progress
        write_iterator = track(
            range(parts),
            description="Writing output chunks",
            disable=config.disable_progress_bar,
            total=parts,
        )
        for idx in write_iterator:
            chunk = "".join(lines[idx * chunk_size : (idx + 1) * chunk_size])
            chunk_file = f"{base}.part{idx + 1}{ext}"
            with open(chunk_file, "w", encoding="utf-8") as fh:
                fh.write(chunk)
            logger.info("Output chunk %d/%d → %s", idx + 1, parts, chunk_file)
        print("✔ Output split into", parts, "chunks.")
    else:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(output_text)
        logger.info("Output written → %s", output_path)
        print("✔ Output written to:", output_path)

    # Handle clipboard copy if enabled
    if not getattr(config, "disable_copy", True) and parts <= 1:
        try:
            import pyperclip

            pyperclip.copy(output_text)
            logger.info("Output copied to clipboard.")
        except ImportError:
            logger.warning("pyperclip not installed, skipping clipboard copy.")
        except (OSError, Exception) as e:
            logger.warning(f"Failed to copy to clipboard: {e}")


def create_default_config(interactive: bool = True) -> None:
    """Creates a default '.codeconcat.yml' configuration file in the current directory.

    This function is typically triggered by the '--init' CLI flag.
    It can either create a default configuration file directly from a template,
    or run an interactive setup that guides the user through configuration options.

    Args:
        interactive: If True, runs the interactive configuration setup.
                    If False, creates a default configuration from the template.
    """
    if interactive:
        # Use the interactive configuration builder
        try:
            from codeconcat.config.interactive_config import run_interactive_setup

            success = run_interactive_setup()
            if not success:
                logger.warning("Interactive configuration setup did not complete successfully.")
        except ImportError:
            logger.error(
                "Failed to import interactive_config module. Falling back to basic config creation."
            )
            _create_basic_config()
        except Exception as e:
            logger.error(f"Error during interactive configuration setup: {e}")
            logger.info("Falling back to basic config creation.")
            _create_basic_config()
    else:
        # Create a basic configuration from the template
        _create_basic_config()


def _create_basic_config() -> None:
    """Creates a basic default '.codeconcat.yml' configuration file from the template."""
    # Ensure os is properly imported in this scope
    import os as local_os

    from codeconcat.processor.security_processor import SecurityProcessor

    config_filename = ".codeconcat.yml"
    if local_os.path.exists(config_filename):
        logger.warning(f"{config_filename} already exists; aborting.")
        return

    try:
        # First try to use the file directly with security validation
        base_dir = local_os.path.dirname(__file__)
        # Validate path to prevent traversal attacks
        try:
            validated_base = SecurityProcessor.validate_path(local_os.getcwd(), base_dir)
        except Exception:
            # If validation fails, use current directory as safe fallback
            validated_base = Path(local_os.getcwd())

        template_path = local_os.path.join(
            str(validated_base), "config", "templates", "default_config.template.yml"
        )

        # Ensure template path is within expected boundaries
        template_path = local_os.path.normpath(template_path)
        if not template_path.startswith(str(validated_base)):
            raise ValidationError("Template path outside of expected directory")

        if local_os.path.exists(template_path):
            with open(template_path) as src, open(config_filename, "w") as dest:
                dest.write(src.read())
        else:
            # Fall back to importlib.resources if file not found directly
            template_content = importlib.resources.read_text(
                "codeconcat.config.templates", "default_config.template.yml"
            )
            with open(config_filename, "w") as f:
                f.write(template_content)

        logger.info(f"Created default configuration file: {config_filename}")
        print(f"\n✅ Created default configuration file: {config_filename}")
        print("To use this configuration, run CodeConCat without the --init flag:")
        print("  codeconcat --target-path <your_code_directory>")
    except FileNotFoundError:
        logger.error("Default configuration template not found within the package.")
        print("\n❌ Default configuration template not found. Please reinstall CodeConCat.")
    except Exception as e:
        logger.error(f"Failed to create default configuration file: {e}")
        print(f"\n❌ Failed to create default configuration file: {e}")


# ──────────────────────────────────────────────────────────────────────────────
def cli_entry_point():
    """The main command-line interface entry point for CodeConCat."""
    # Import CLI components locally to avoid circular imports
    import os as local_os

    from codeconcat.api.cli import build_parser

    """The main command-line interface entry point for CodeConCat.

    Parses command-line arguments, sets up logging, handles special flags
    like --init and --show-config, loads the configuration, runs the main
    CodeConCat logic via run_codeconcat, and writes the output.
    Handles potential errors and logs them appropriately.
    """
    try:
        # Parse arguments (returns namespace with defaults)
        parser = build_parser()
        args = parser.parse_args()

        # Configure logging based on args
        debug_mode = getattr(args, "debug", False) or args.verbose > 1
        quiet_mode = getattr(args, "quiet", False)
        log_level = getattr(args, "log_level", "WARNING")
        if debug_mode or args.verbose > 1:
            log_level = "DEBUG"
        configure_logging(log_level, debug_mode, quiet_mode)

        # Handle reconstruction command if specified
        if hasattr(args, "reconstruct") and args.reconstruct:
            logger.info(f"Reconstructing files from {args.reconstruct}")
            input_format = None if args.input_format == "auto" else args.input_format
            try:
                stats = reconstruct_from_file(
                    args.reconstruct,
                    args.output_dir,
                    input_format,
                    verbose=(args.verbose > 0 or debug_mode),
                )
                print("\n✅ Reconstruction complete!")
                print(f"Files processed: {stats['files_processed']}")
                print(f"Files created: {stats['files_created']}")
                print(f"Errors: {stats['errors']}")
                print(f"Output directory: {args.output_dir}")
                return 0
            except Exception as e:
                logger.error(f"Error during reconstruction: {e}")
                print(f"\n❌ Error reconstructing files: {e}")
                return 1

        # Initialize config if requested
        if hasattr(args, "init") and args.init:
            logger.info("Running interactive configuration setup")
            create_default_config(interactive=True)
            return 0

        # Convert args namespace to dictionary for easier handling
        cli_args = vars(args)

        # Print important CLI args for debugging
        # if 'output' in cli_args:
        #    print(f"\n[DEBUG CLI] Output path from CLI: {cli_args['output']}")
        # if 'enable_compression' in cli_args:
        #    print(f"[DEBUG CLI] Compression enabled from CLI: {cli_args['enable_compression']}")
        # if 'compression_level' in cli_args:
        #    print(f"[DEBUG CLI] Compression level from CLI: {cli_args['compression_level']}")

        # Handle backward compatibility for parser engine selection
        if hasattr(args, "no_tree") and args.no_tree and "parser_engine" not in cli_args:
            logger.warning(
                "The --no-tree flag is deprecated. Please use --parser-engine=regex instead."
            )
            cli_args["parser_engine"] = "regex"
    except Exception as e:
        logger.error(f"Error during argument parsing: {e}")
        print(f"\n❌ Error initializing CodeConCat: {e}")
        return 1

    # --- Load Configuration using the ConfigBuilder --- #
    try:
        # Get the preset name (if specified)
        preset_name = (
            cli_args.get("output_preset") or "medium"
        )  # Default to medium if not specified

        # Debug: Show what CLI arguments were received
        if args.verbose > 1:
            print("\n[DEBUG] CLI arguments received:")
            for key, value in cli_args.items():
                if value is not None and key not in ["verbose", "debug", "quiet"]:
                    print(f"  {key}: {value}")

        # Create a config builder and apply settings in the proper order of precedence:
        # 1. Defaults, 2. Preset, 3. YAML file, 4. CLI arguments
        config_builder = ConfigBuilder()
        config_builder.with_defaults()
        config_builder.with_preset(preset_name)
        config_builder.with_yaml_config(args.config)  # Use config_path_override if provided

        # Apply CLI arguments which have the highest precedence
        config_builder.with_cli_args(cli_args)

        # Build the final configuration with all settings applied in proper order
        config = config_builder.build()

        # Show what CLI arguments were applied to config
        if hasattr(config_builder, "_cli_values") and config_builder._cli_values:
            print("\n[CLI Settings Applied]")
            for config_key, value in config_builder._cli_values.items():
                print(f"  {config_key}: {value}")

        # Direct application of critical CLI arguments to ensure they take effect
        # This is necessary in case the with_cli_args method isn't applying them correctly
        if "format" in cli_args and cli_args["format"] is not None:
            print(f"[Direct Override] Setting format from CLI: {cli_args['format']}")
            config.format = cli_args["format"].lower()

        # Fix: Ensure compression flags are directly applied from CLI to config
        if "enable_compression" in cli_args and cli_args["enable_compression"]:
            print("[Direct Override] Enabling compression from CLI")
            config.enable_compression = True

        if "compression_level" in cli_args and cli_args["compression_level"]:
            print(
                f"[Direct Override] Setting compression level from CLI: {cli_args['compression_level']}"
            )
            config.compression_level = cli_args["compression_level"]

        # Verify that key settings are correctly applied
        if args.verbose > 0:
            print("\n[CONFIG VALUES]")
            for key in ["format", "output", "enable_compression", "compression_level"]:
                print(f"  {key}: {getattr(config, key, None)}")

        # Force lowercase format to ensure consistent comparison later
        if config.format:
            config.format = config.format.lower()

        # Only set default output filename if no output was specified
        if config.output is None or config.output == "":
            # Target_path could be a directory or file
            if hasattr(config, "target_path") and config.target_path:
                # Normalize path and get base folder name
                folder_name = local_os.path.basename(local_os.path.normpath(config.target_path))

                # Special case - if target_path is a single file, use its containing folder
                if local_os.path.isfile(config.target_path):
                    parent_dir = local_os.path.dirname(config.target_path)
                    if parent_dir:
                        folder_name = local_os.path.basename(local_os.path.normpath(parent_dir))
                    else:
                        folder_name = "codeconcat"

                # Remove any unsafe characters
                folder_name = "".join(c for c in folder_name if c.isalnum() or c in "._- ")

                # If folder_name is empty after cleaning, use a fallback
                if not folder_name.strip():
                    folder_name = "codeconcat"

                # Set the output path with the correct format extension
                config.output = f"{folder_name}_ccc.{config.format}"
                print(f"[Info] Using folder-based output name: {config.output}")
            else:
                # Fallback if no target_path is available
                config.output = f"codeconcat_output.{config.format}"

        # Print detailed configuration if requested
        if args.show_config_detail:
            config_builder.print_config_details()
            return  # Exit after showing config details
    except ConfigurationError as e:
        logger.critical(f"Configuration error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.critical(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        if log_level == logging.DEBUG:
            logger.exception("Detailed error information:")
        sys.exit(1)

    # Propagate verbosity to config for other modules
    config.verbose = args.verbose > 0 if isinstance(args.verbose, int) else bool(args.verbose)

    if args.show_config:
        print("Current Configuration:")
        print(config.model_dump_json(indent=2))
        print("-----------------------------")
        return  # Exit after showing config

    # We already handled show_config_detail in the configuration loading step

    # Handle --verify-dependencies early exit case
    if args.verify_dependencies:
        print("\nVerifying Tree-sitter grammar dependencies...")
        success, successful_langs, failed_langs = verify_tree_sitter_dependencies()

        # Print summary
        if success:
            print(f"\n✅ All {len(successful_langs)} Tree-sitter grammars are properly installed.")
            print(f"Supported languages: {', '.join(sorted(successful_langs))}")
            return 0
        else:
            print("\n❌ Tree-sitter dependency check failed.")
            print(f"✅ Successful: {len(successful_langs)} languages")
            print(f"❌ Failed: {len(failed_langs)} languages")

            # Print detailed errors
            if failed_langs:
                print("\nError details:")
                for i, error in enumerate(failed_langs, 1):
                    print(f"  {i}. {error}")

            print("\nSuggestions for fixing:")
            print("  1. Run 'pip install tree-sitter-languages' to install all grammar packages")
            print(
                "  2. Or install individual language grammars with 'pip install tree-sitter-<language>'"
            )
            print(
                "  3. Check that your Python environment has the necessary compilers for native extensions"
            )
            return 1

    # Handle --diagnose-parser early exit case
    if args.diagnose_parser:
        language = args.diagnose_parser.lower()
        print(f"\nRunning parser diagnostics for language: {language}")

        # Find a test file for this language in the test corpus if available

        test_file = None
        test_corpus_path = local_os.path.join(
            local_os.path.dirname(local_os.path.dirname(__file__)),
            "tests",
            "parser_test_corpus",
            language,
        )

        if local_os.path.exists(test_corpus_path):
            for filename in local_os.listdir(test_corpus_path):
                if filename.startswith("basic.") or filename == "basic":
                    test_file = local_os.path.join(test_corpus_path, filename)
                    break

        if test_file:
            print(f"Using test file: {test_file}")
        else:
            print(f"No test file found for {language}. Only checking parser availability.")

        success, results = diagnose_parser(language, test_file)

        # Print results
        print("\nParser Availability:")
        for parser_type, parser_name in results.get("parsers_found", {}).items():
            if isinstance(parser_name, str):
                print(f"  {parser_type.capitalize() + ':':12} {parser_name or 'Not available'}")

        if test_file and "parsers_tested" in results:
            print("\nParser Test Results:")
            for parser_type, result in results.get("parsers_tested", {}).items():
                status = "✅ Success" if result.get("success") else "❌ Failed"
                print(f"  {parser_type.capitalize() + ':':12} {status}")

                if "declarations_count" in result:
                    print(f"    - Declarations: {result['declarations_count']}")
                if "imports_count" in result:
                    print(f"    - Imports: {result['imports_count']}")
                if result.get("error"):
                    print(f"    - Error: {result['error']}")

        if results.get("errors"):
            print("\nDiagnostic Errors:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
            return 1

        return 0 if success else 1

    # --- Run Main Logic --- #
    try:
        # Quote only shown if not verbose
        if not config.verbose:
            quote = get_random_quote()
            # Colorize cat quotes for better visual appeal
            if "cat" in quote.lower() or "meow" in quote.lower() or "purr" in quote.lower():
                # Use cyan color for cat-themed quotes
                print(f"\033[96m{quote}\033[0m")
            else:
                print(quote)

        # Pass the loaded and updated config
        output_content = run_codeconcat(config)

        # --- Write Output --- #
        if output_content is not None:
            _write_output_files(output_content, config)
            print("✓ CodeConCat finished successfully.")
            return 0
        else:
            logger.warning("CodeConCat finished, but no output was generated.")

    except (ConfigurationError, FileProcessingError, OutputError) as e:
        logger.error(f"CodeConCat failed: {e}")
        if config.verbose:
            logger.exception("Detailed traceback:")  # Log traceback only in verbose
        sys.exit(1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


def generate_folder_tree(root_path: str, config: CodeConCatConfig) -> str:
    """
    Walk the directory tree starting at root_path and return a string representing the folder structure.

    Respects exclusion patterns defined in the config (default and user-defined).
    Uses characters like '│', '├', '└', and '─' to create a visual tree.

    Args:
        root_path: The root directory to start generating the tree from.
        config: The CodeConCatConfig object containing exclusion patterns.

    Returns:
        A string representing the folder structure, ready for inclusion in output.

    Complexity:
        O(n) where n is the total number of files and directories

    Flow:
        Called by: run_codeconcat() when folder_tree option is enabled
        Calls: should_include_file(), should_skip_dir()

    Security Notes:
        - Respects path traversal protection from should_skip_dir
        - Honors exclusion patterns to avoid sensitive directories
    """
    from codeconcat.collector.local_collector import should_include_file, should_skip_dir

    lines = []
    for root, dirs, files in os.walk(root_path):
        # Check if we should skip this directory
        if should_skip_dir(root, config):
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
        dirs[:] = [d for d in dirs if not should_skip_dir(os.path.join(root, d), config)]
        dirs.sort()  # Sort directories for consistent output

    return "\n".join(lines)


def run_codeconcat(config: CodeConCatConfig) -> str:
    """Runs the main CodeConCat processing pipeline and returns the output string.

    This function orchestrates the core steps:
    1. Validates configuration for security and correctness
    2. Collects files (local or remote GitHub repositories)
    3. Parses collected code files with language-specific parsers
    4. Extracts documentation files (if enabled)
    5. Performs AI-based annotation (if enabled)
    6. Applies compression (if enabled)
    7. Generates the final output string in the specified format

    Args:
        config: The fully resolved CodeConCatConfig object containing all settings.

    Returns:
        The concatenated and processed output as a single string.

    Raises:
        CodeConcatError: For general errors during processing.
        ConfigurationError: If the configuration is invalid.
        FileProcessingError: For errors related to reading or parsing files.
        OutputError: For errors during output generation.

    Complexity:
        O(n*m) where n is number of files and m is average file size

    Flow:
        Called by: cli_entry_point(), run_codeconcat_in_memory()
        Calls: collect_files(), parse_code_files(), generate_output()

    Security Notes:
        - Validates all configuration values before processing
        - Uses specific exception types for better error diagnosis
        - Path validation performed during file collection
        - File size limits enforced (20 MB collection, 5 MB binary check)
    """
    # Validate configuration
    try:
        validate_config_values(config)
        logger.debug("Configuration validation passed")
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ConfigurationError(f"Invalid configuration: {e}") from e
    logger.debug("Running CodeConCat with config: %s", config)
    try:
        # Validate configuration
        if not config.target_path:
            raise ConfigurationError("Target path is required")
        if config.format not in ["markdown", "json", "xml", "text"]:
            raise ConfigurationError(f"Invalid format: {config.format}")

        # Collect input files
        logger.info("Collecting input files...")
        files_to_process: List[ParsedFileData] = []

        # Check if we're in diff mode
        diff_mode = (
            hasattr(config, "diff_from")
            and config.diff_from
            and hasattr(config, "diff_to")
            and config.diff_to
        )

        logger.info(
            f"Diff mode check: has diff_from={hasattr(config, 'diff_from')}, diff_from={getattr(config, 'diff_from', None)}, has diff_to={hasattr(config, 'diff_to')}, diff_to={getattr(config, 'diff_to', None)}, diff_mode={diff_mode}"
        )

        if diff_mode:
            logger.info("DIFF MODE ACTIVATED - will collect diffs instead of all files")

        if diff_mode:
            # Validate that both diff refs are provided
            if not config.diff_from or not config.diff_to:
                raise ConfigurationError(
                    "Both --diff-from and --diff-to are required for diff mode"
                )

            logger.info(f"Collecting diffs between {config.diff_from} and {config.diff_to}")

            # Use DiffCollector for differential outputs
            from codeconcat.collector.diff_collector import DiffCollector

            # Determine the repository path
            repo_path = config.target_path if config.target_path else "."

            try:
                diff_collector = DiffCollector(repo_path, config.diff_from, config.diff_to, config)
                diff_items = diff_collector.collect_diffs()

                # Convert AnnotatedFileData to ParsedFileData for compatibility
                # Note: In diff mode, the files are already annotated with diff information
                files_to_process = []
                for item in diff_items:
                    # Create ParsedFileData from AnnotatedFileData
                    parsed_file = ParsedFileData(
                        file_path=item.file_path,
                        language=item.language,
                        content=item.content,
                        declarations=item.declarations,
                        imports=item.imports,
                        # Store the diff-specific data
                        diff_content=item.diff_content,
                        diff_metadata=item.diff_metadata,
                    )
                    files_to_process.append(parsed_file)

                logger.info(f"Collected {len(files_to_process)} file diffs")
            except ValueError as e:
                raise ConfigurationError(f"Diff collection error: {e}") from e

        elif config.source_url:
            logger.info(f"Collecting files from source URL: {config.source_url}")
            # Use the secure async implementation with synchronous wrapper
            files_to_process, temp_dir = collect_git_repo(config.source_url, config)
        elif config.target_path:
            logger.info(f"Collecting files from local path: {config.target_path}")
            files_to_process = collect_local_files(config.target_path, config)
        else:
            raise ConfigurationError(
                "Either source_url or target_path must be provided in the configuration."
            )

        # Track initial collected file count for stats (before validation)
        initial_collected_count = len(files_to_process)

        # Setup Semgrep if enabled
        if hasattr(config, "enable_semgrep") and config.enable_semgrep:
            logger.info("Setting up Semgrep for security scanning...")
            is_available = setup_semgrep(config)
            if not is_available:
                logger.warning("Semgrep is not available. Security scanning will be limited.")
                # Disable Semgrep if not available
                config.enable_semgrep = False

        # Validate input files
        logger.info("Validating input files...")
        try:
            validated_files = validate_input_files(files_to_process, config)
            logger.debug(f"Validated {len(validated_files)} of {len(files_to_process)} files")
            files_to_process = validated_files
        except ValidationError as e:
            logger.error(f"File validation error: {e}")
            # In strict security mode, fail immediately on validation errors
            if hasattr(config, "strict_security") and config.strict_security:
                raise
            # Otherwise, continue with validated files, log warning
            logger.warning("Continuing with validated files only")

        # Verify file types match expected formats
        try:
            file_types = verify_file_signatures(files_to_process)
            logger.debug(f"Verified file signatures for {len(file_types)} files")
        except ValidationError as e:
            logger.error(f"File signature validation error: {e}")
            # This is a more serious error, but we'll continue with a warning
            logger.warning("Some files may have incorrect content types")

        # Parse code files (skip if in diff mode as files are already parsed)
        logger.debug("Starting file parsing.")
        try:
            logger.info(
                f"[CodeConCat] Found {len(files_to_process)} code files. Starting parsing..."
            )

            # Skip parsing if we're in diff mode (files already processed)
            if diff_mode:
                logger.info("Diff mode: skipping additional parsing (files already processed)")
                parsed_files = files_to_process
                parser_errors: List[ParserError] = []
            else:
                # Use the unified parsing pipeline
                logger.info("Using unified parsing pipeline with progressive fallbacks")
                parsed_files, parser_errors = parse_code_files(files_to_process, config)

            if parser_errors:
                # Log errors encountered during parsing
                for error in parser_errors:
                    logger.warning(
                        f"Parsing error for {getattr(error, 'file_path', 'unknown')}: {str(error)}"
                    )

            if not parsed_files:
                logger.error("[CodeConCat] No files were successfully parsed.")
                # Decide if this should be a fatal error or just a warning
                raise FileProcessingError("No files were successfully parsed")
            else:
                logger.info(f"[CodeConCat] Parsing complete. Parsed {len(parsed_files)} files.")

        except (OSError, UnicodeDecodeError, AttributeError) as e:
            raise FileProcessingError(f"Error parsing files: {str(e)}") from e

        # Apply AI summarization if enabled
        logger.debug(f"[CodeConCat] AI summary enabled: {config.enable_ai_summary}")
        if config.enable_ai_summary:
            try:
                logger.info("[CodeConCat] Generating AI summaries...")
                import asyncio

                from codeconcat.processor.summarization_processor import (
                    create_summarization_processor,
                )

                summarizer = create_summarization_processor(config)
                if summarizer:
                    logger.info(
                        f"[CodeConCat] Summarizer created, processing {len(parsed_files)} files..."
                    )
                    logger.info(f"[DEBUG MAIN] Config ai_meta_overview: {config.ai_meta_overview}")
                    # Run async summarization
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        parsed_files = loop.run_until_complete(
                            summarizer.process_batch(parsed_files)
                        )
                    finally:
                        loop.run_until_complete(summarizer.cleanup())
                        # Allow aiohttp session cleanup to complete before closing loop
                        loop.run_until_complete(asyncio.sleep(0.25))
                        loop.close()

                    # Check if any summaries were actually added
                    summaries_added = sum(
                        1 for f in parsed_files if hasattr(f, "ai_summary") and f.ai_summary
                    )
                    logger.info(
                        f"[CodeConCat] Processing complete. {summaries_added} of {len(parsed_files)} files have AI summaries."
                    )
                else:
                    logger.warning("[CodeConCat] Summarizer was not created - check configuration")
            except Exception as e:
                logger.error(f"Error during AI summarization: {str(e)}")
                import traceback

                logger.debug(traceback.format_exc())
                # Continue without summaries - this is not a fatal error

        # Extract docs if requested
        docs = []
        if config.extract_docs:
            try:
                doc_paths = [f.file_path for f in files_to_process]
                docs = extract_docs(doc_paths, config)
            except Exception as e:
                logger.warning(f"Warning: Failed to extract documentation: {str(e)}")

        logger.info("[CodeConCat] Starting annotation of parsed files...")
        # Annotate files if enabled (skip in diff mode as files are already annotated)
        annotated_files = []
        try:
            if diff_mode:
                logger.info("Diff mode: files already annotated, skipping annotation step")
                # Convert ParsedFileData with diff info to AnnotatedFileData
                for parsed in parsed_files:
                    annotated = AnnotatedFileData(
                        file_path=parsed.file_path,
                        language=parsed.language or "unknown",
                        content=parsed.content or "",
                        annotated_content=parsed.content or "",
                        summary=f"Diff for {parsed.file_path}",
                        ai_summary=getattr(parsed, "ai_summary", None),  # Preserve AI summary
                        ai_metadata=getattr(parsed, "ai_metadata", None),  # Preserve AI metadata
                        declarations=parsed.declarations,
                        imports=parsed.imports,
                        diff_content=getattr(parsed, "diff_content", None),
                        diff_metadata=getattr(parsed, "diff_metadata", None),
                    )
                    annotated_files.append(annotated)
            elif not config.disable_annotations:
                # Wrap annotation loop with track
                annotation_iterator = track(
                    parsed_files,
                    description="Annotating files",
                    disable=config.disable_progress_bar,  # Use config flag
                    total=len(parsed_files),
                )
                for file in annotation_iterator:
                    try:
                        annotated = annotate(file, config)
                        annotated_files.append(annotated)
                    except Exception as e:
                        # DEBUG: Log type and value of 'file' before using file.file_path
                        logger.error(
                            f"DEBUG: Annotation exception for file object. Type: {type(file)}, Value: {repr(file)}"
                        )
                        try:
                            file_path_debug = file.file_path
                        except Exception as path_exc:
                            file_path_debug = f"<unavailable: {path_exc}>"
                        logger.warning(f"Warning: Failed to annotate {file_path_debug}: {str(e)}")
                        # Fall back to basic annotation
                        try:
                            annotated_files.append(
                                AnnotatedFileData(
                                    file_path=file.file_path,
                                    language=file.language or "",
                                    content=file.content or "",
                                    annotated_content=file.content or "",
                                    summary="",
                                    tags=[],
                                )
                            )
                        except Exception as fallback_exc:
                            logger.error(
                                f"DEBUG: Fallback AnnotatedFileData creation failed: {fallback_exc}"
                            )
                            # Optionally, skip appending if fallback also fails

            else:
                # Create basic annotations without AI analysis
                # Wrap this loop too, for consistency, although it should be fast
                basic_annotation_iterator = track(
                    parsed_files,
                    description="Preparing basic annotations",
                    disable=config.disable_progress_bar,
                    total=len(parsed_files),
                )
                for file in basic_annotation_iterator:
                    annotated_files.append(
                        AnnotatedFileData(
                            file_path=file.file_path,
                            language=file.language or "",
                            content=file.content or "",
                            annotated_content=file.content or "",
                            summary="",
                            tags=[],
                        )
                    )
        except (OSError, AttributeError, TypeError) as e:
            raise FileProcessingError(f"Error during annotation phase: {str(e)}") from e

        # --- Prepare list for polymorphic writers --- #
        items: List[WritableItem] = []
        items.extend(annotated_files)
        items.extend(docs)

        if config.sort_files:
            logger.info("Sorting all items alphabetically by path...")
            items.sort(key=lambda x: getattr(x, "file_path", ""))
            logger.debug("Items sorted.")

        # Apply compression if enabled
        if config.enable_compression:
            logger.info(f"[CodeConCat] Applying compression (level: {config.compression_level})...")
            # Print detailed compression configuration information as standard output
            print("\n[Compression Config]")
            print(f"  Level: {config.compression_level}")
            print(
                f"  Threshold: {config.compression_keep_threshold} lines (segments smaller than this are always kept)"
            )
            print(f"  Preserved tags: {', '.join(config.compression_keep_tags)}")
            print(f"  Placeholder: {config.compression_placeholder}")

            compression_processor = CompressionProcessor(config)

            # Initialize dictionary to store compressed segments by file path
            config._compressed_segments = {}  # type: ignore[attr-defined]

            # Apply compression to each annotated file
            for _i, writable_item in enumerate(items):
                if isinstance(writable_item, AnnotatedFileData) and writable_item.content:
                    item = writable_item  # Type narrowed to AnnotatedFileData
                    # Process the file through the compression processor
                    compressed_segments = compression_processor.process_file(item)  # type: ignore[arg-type]

                    if compressed_segments:
                        # Store the compressed content in the item for rendering
                        item.content = compression_processor.apply_compression(item)  # type: ignore[arg-type]

                        # Store segments in config for the renderer to access, properly indexed by file path
                        # This is a workaround since we can't modify the WritableItem interface
                        # without more substantial refactoring
                        config._compressed_segments[item.file_path] = compressed_segments  # type: ignore[attr-defined]

                        # Log compression stats
                        original_lines = len(item.content.split("\n"))
                        compressed_lines = sum(
                            1
                            for s in compressed_segments
                            if s.segment_type == ContentSegmentType.CODE
                        )

                        # Only print detailed file compression stats for large or high-compression-ratio files
                        if original_lines > 15 or original_lines - compressed_lines > 5:
                            # Format the file path to make it more readable
                            rel_path = (
                                item.file_path.split("codeconcat/")[-1]
                                if "codeconcat/" in item.file_path
                                else os.path.basename(item.file_path)
                            )
                            compression_percent = (1 - compressed_lines / original_lines) * 100

                            # Use color indicators for compression ratio
                            ratio_indicator = (
                                "🟢"
                                if compression_percent > 70
                                else "🟡"
                                if compression_percent > 40
                                else "🔴"
                            )

                            print(
                                f"  {ratio_indicator} {rel_path}: {compressed_lines}/{original_lines} lines kept ({compression_percent:.1f}% reduction)"
                            )

                        # Calculate segment counts for statistics (commented out for now)
                        # Uncomment if you need to track these metrics
                        # code_segments = sum(
                        #     1
                        #     for s in compressed_segments
                        #     if s.segment_type == ContentSegmentType.CODE
                        # )
                        # omitted_segments = sum(
                        #     1
                        #     for s in compressed_segments
                        #     if s.segment_type == ContentSegmentType.OMITTED
                        # )

                        logger.debug(
                            f"Compressed {item.file_path}: {compressed_lines} retained of {original_lines} lines"
                        )

            # Calculate and display overall compression statistics
            total_original_lines = 0
            total_compressed_lines = 0
            total_files_compressed = 0
            high_compression_files = 0  # >70% reduction
            medium_compression_files = 0  # 40-70% reduction
            low_compression_files = 0  # <40% reduction

            for writable_item in items:
                if isinstance(writable_item, AnnotatedFileData) and hasattr(
                    writable_item, "_compression_stats"
                ):
                    item = writable_item  # Type narrowed to AnnotatedFileData
                    total_files_compressed += 1
                    stats = item._compression_stats
                    total_original_lines += stats["original_lines"]
                    total_compressed_lines += stats["compressed_lines"]

                    compression_percent = (
                        1 - stats["compressed_lines"] / stats["original_lines"]
                    ) * 100
                    if compression_percent > 70:
                        high_compression_files += 1
                    elif compression_percent > 40:
                        medium_compression_files += 1
                    else:
                        low_compression_files += 1

            if total_files_compressed > 0 and total_original_lines > 0:
                overall_reduction = (1 - total_compressed_lines / total_original_lines) * 100

                print("\n[Compression Summary]")
                print(f"  Files compressed: {total_files_compressed}")
                print(
                    f"  Total lines: {total_original_lines:,} → {total_compressed_lines:,} ({overall_reduction:.1f}% reduction)"
                )
                print("  Compression breakdown:")
                print(f"    🟢 High (>70%): {high_compression_files} files")
                print(f"    🟡 Medium (40-70%): {medium_compression_files} files")
                print(f"    🔴 Low (<40%): {low_compression_files} files")

            logger.info("[CodeConCat] Compression complete.")

        # --- Compute run statistics BEFORE any writing ---
        try:
            initial_collected_count = len(parsed_files) + len(docs)
            languages_set = {pf.language for pf in parsed_files if hasattr(pf, "language")}
            total_lines = sum(len(pf.content.splitlines()) for pf in parsed_files if pf.content)
            total_bytes = sum(len(pf.content.encode("utf-8")) for pf in parsed_files if pf.content)

            run_stats = {
                "files_scanned": initial_collected_count,
                "files_parsed": len(parsed_files),
                "docs_extracted": len(docs),
                "languages": languages_set,
                "languages_count": len(languages_set),
                "total_lines": total_lines,
                "total_bytes": total_bytes,
            }

            # Store stats in a way that doesn't violate Pydantic model validation
            # Use object.__setattr__ to bypass Pydantic validation for this dynamic attribute
            object.__setattr__(config, "_run_stats", run_stats)

        except Exception as e:
            # Log the exception at DEBUG level for debugging purposes
            logger.debug(f"Failed to compute run statistics: {e}")
            # Initialize empty stats to prevent downstream errors
            object.__setattr__(config, "_run_stats", {})

        folder_tree_str = ""
        if hasattr(config, "include_directory_structure") and config.include_directory_structure:
            # Placeholder for actual tree generation logic
            # folder_tree_str = generate_folder_tree(items, config) # Assuming 'items' contains file paths
            folder_tree_str = "[INFO] Directory tree would be displayed here.\n"
            logger.info("Including directory structure in output.")
        else:
            logger.info("Skipping directory structure in output.")

        # Make sure format is lowercase for consistent comparison
        if hasattr(config, "format") and config.format:
            config.format = config.format.lower()

        print(f"\n[OutputFormat] Using: {config.format}")
        logger.info(f"[CodeConCat] Writing output in {config.format} format...")

        # Write output in requested format
        try:
            output = None
            if config.format == "markdown":
                # Pass the combined & sorted items list
                output = write_markdown(items, config, folder_tree_str)
                print("Using markdown writer")
            elif config.format == "json":
                # Pass the combined & sorted items list
                output = write_json(items, config, folder_tree_str)  # type: ignore[arg-type]
                print("Using JSON writer")
            elif config.format == "xml":
                # Pass the combined & sorted items list
                output = write_xml(items, config, folder_tree_str)
                print("Using XML writer")
            elif config.format == "text":
                # Pass the combined & sorted items list
                output = write_text(items, config, folder_tree_str)  # type: ignore[arg-type]
                print("Using text writer")
            else:
                # Default to markdown if format is unrecognized
                logger.warning(f"Unrecognized format '{config.format}', defaulting to markdown")
                config.format = "markdown"
                output = write_markdown(items, config, folder_tree_str)
        except (OSError, AttributeError, KeyError, ValueError) as e:
            raise OutputError(f"Error generating {config.format} output: {str(e)}") from e

        # --- Token stats summary (all files) ---
        try:
            from codeconcat.processor.token_counter import get_token_stats

            # Calculate tokens for uncompressed content
            total_gpt4_uncompressed = total_claude_uncompressed = 0
            for pf in parsed_files:
                stats = get_token_stats(pf.content or "")
                total_gpt4_uncompressed += stats.gpt4_tokens
                total_claude_uncompressed += stats.claude_tokens

            print("\n[Token Summary] Total tokens for all parsed files (UNCOMPRESSED):")
            print(f"  Claude:   {total_claude_uncompressed}")
            print(f"  GPT-4:    {total_gpt4_uncompressed}")

            # If compression was enabled, also show compressed tokens for comparison
            if (
                config.enable_compression
                and hasattr(config, "_compressed_segments")
                and config._compressed_segments
            ):
                total_gpt4_compressed = total_claude_compressed = 0

                # Calculate compressed tokens by using the compressed segments
                for _file_path, file_segments in config._compressed_segments.items():
                    # Concatenate the content of all segments in this file
                    compressed_content = "\n".join(segment.content for segment in file_segments)
                    stats = get_token_stats(compressed_content)
                    total_gpt4_compressed += stats.gpt4_tokens
                    total_claude_compressed += stats.claude_tokens

                print("\n[Token Summary] Total tokens for all parsed files (COMPRESSED):")
                print(
                    f"  Claude:   {total_claude_compressed} ({(total_claude_compressed / total_claude_uncompressed * 100):.1f}%)"
                )
                print(
                    f"  GPT-4:    {total_gpt4_compressed} ({(total_gpt4_compressed / total_gpt4_uncompressed * 100):.1f}%)"
                )

                # Show token reduction from compression
                print("\n[Compression Effectiveness]")
                print(
                    f"  Claude:   {total_claude_uncompressed - total_claude_compressed} tokens saved ({(1 - total_claude_compressed / total_claude_uncompressed) * 100:.1f}% reduction)"
                )
                print(
                    f"  GPT-4:    {total_gpt4_uncompressed - total_gpt4_compressed} tokens saved ({(1 - total_gpt4_compressed / total_gpt4_uncompressed) * 100:.1f}% reduction)"
                )
        except (ImportError, AttributeError, ValueError, TypeError) as e:
            logger.warning(f"[Tokens] Failed to calculate token stats: {e}")
            import traceback

            logger.debug(f"Token calculation error details: {traceback.format_exc()}")
        # Return the generated output string
        return output

    except CodeConcatError as e:
        logger.error(f"[CodeConCat] Error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"[CodeConCat] Unexpected error: {str(e)}")
        raise


def run_codeconcat_in_memory(config: CodeConCatConfig) -> str:
    """Run CodeConCat and return the output as a string, suitable for programmatic use.

    This function acts as a high-level API for integrating CodeConCat into other
    Python applications. It takes a pre-configured CodeConCatConfig object,
    runs the main processing pipeline via run_codeconcat, and returns the
    generated output string.

    Thread-safe implementation that does not redirect sys.stdout, making it safe
    for use in async/multi-threaded environments like FastAPI.

    Args:
        config: A CodeConCatConfig object with all desired settings populated.

    Returns:
        The complete generated output string.

    Raises:
        Inherits exceptions from run_codeconcat (CodeConcatError, etc.).

    Complexity:
        O(n) where n is the total size of files being processed

    Flow:
        Called by: API endpoints in api/app.py
        Calls: run_codeconcat()

    Security Notes:
        - Thread-safe: Creates a deep copy of config to avoid mutations
        - Safe for concurrent execution in multi-threaded servers
        - No shared state modifications
    """
    import copy

    # Create a deep copy of the config to ensure thread safety
    # This prevents mutations from affecting other concurrent requests
    config_copy = copy.deepcopy(config)

    # Set minimal verbosity to suppress console output during processing
    config_copy.verbose = 0  # Set to minimal verbosity for API usage
    config_copy.quiet = True  # Suppress all non-error output
    config_copy.disable_progress_bar = True  # Disable progress bars for API

    # Run with the copied config to ensure thread safety
    result = run_codeconcat(config_copy)
    return result


if __name__ == "__main__":
    from codeconcat.cli import app

    app()
