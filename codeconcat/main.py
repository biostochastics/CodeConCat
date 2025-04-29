"""
Main entry point for the CodeConCat CLI application.

This module handles command-line argument parsing, configuration loading,
file collection, processing, and output generation.
"""

import argparse
import importlib.resources
import logging
import os
import sys
from typing import List, Union
from typing import Literal
from tqdm import tqdm
from codeconcat.base_types import (
    ContentSegmentType,
    AnnotatedFileData,
    CodeConCatConfig,
    WritableItem,
)
from codeconcat.collector.remote_collector import collect_git_repo
from codeconcat.collector.local_collector import collect_local_files
from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.diagnostics import verify_tree_sitter_dependencies, diagnose_parser
from codeconcat.parser.doc_extractor import extract_docs
from codeconcat.parser.file_parser import parse_code_files
from codeconcat.parser.enhanced_pipeline import enhanced_parse_pipeline
from codeconcat.processor.compression_processor import CompressionProcessor
from codeconcat.quotes import get_random_quote
from codeconcat.transformer.annotator import annotate
from codeconcat.version import __version__
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.text_writer import write_text
from codeconcat.writer.xml_writer import write_xml

# Suppress HuggingFace tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

#!/usr/bin/env python3
# SPDX‑License‑Identifier: MIT

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

    Args:
        log_level: The logging level to use. Can be a string (DEBUG, INFO, etc.) or an int.
        debug: If True, sets log level to DEBUG regardless of log_level parameter.
        quiet: If True, only shows ERROR level messages and disables progress bars.
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
        # Add other noisy libraries here if needed


# ──────────────────────────────────────────────────────────────────────────────
# Exception hierarchy
# ──────────────────────────────────────────────────────────────────────────────
class CodeConcatError(Exception):
    """Base exception for CodeConCat."""


class ConfigurationError(CodeConcatError):
    pass


class FileProcessingError(CodeConcatError):
    pass


class OutputError(CodeConcatError):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _write_output_files(output_text: str, config: CodeConCatConfig) -> None:
    """Write the final concatenated output to one or more files.

    Handles splitting the output into multiple parts if requested in the config
    (currently only for Markdown format) and optionally copies the content
    to the clipboard.

    Args:
        output_text: The complete string output generated by CodeConCat.
        config: The CodeConCatConfig object containing output settings like
                output path, format, split_output, and disable_copy.
    """
    output_path = config.output or f"code_concat_output.{config.format}"
    parts = max(1, getattr(config, "split_output", 1))

    if parts > 1 and config.format == "markdown":
        lines = output_text.splitlines(keepends=True)
        chunk_size = (len(lines) + parts - 1) // parts
        base, ext = os.path.splitext(output_path)

        # Wrap loop with tqdm for progress
        write_iterator = tqdm(
            range(parts),
            desc="Writing output chunks",
            unit="chunk",
            total=parts,
            disable=config.disable_progress_bar,
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
        except Exception as e:
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
    config_filename = ".codeconcat.yml"
    if os.path.exists(config_filename):
        logger.warning(f"{config_filename} already exists; aborting.")
        return

    try:
        # First try to use the file directly
        template_path = os.path.join(
            os.path.dirname(__file__), "config", "templates", "default_config.template.yml"
        )
        if os.path.exists(template_path):
            with open(template_path, "r") as src, open(config_filename, "w") as dest:
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
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the command-line argument parser for CodeConCat.

    Defines all available CLI flags, options, and their help messages,
    organizing them into logical groups for better readability.

    CLI options are divided into "Basic" and "Advanced" categories, with advanced
    options hidden by default unless the --advanced flag is specified.

    Returns:
        An configured argparse.ArgumentParser instance.
    """

    # Create a custom argument parser that hides advanced options
    class AdvancedHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
        """Custom formatter that can hide advanced options."""

        def _format_action_invocation(self, action):
            if hasattr(action, "advanced") and action.advanced and not args_namespace.advanced:
                return argparse.SUPPRESS
            return super()._format_action_invocation(action)

    # Create a wrapper for ArgumentParser to track advanced options
    class AdvancedArgumentParser(argparse.ArgumentParser):
        """Parser that supports hiding advanced options."""

        def add_argument(self, *args, **kwargs):
            # Extract and remove advanced flag if present
            advanced = kwargs.pop("advanced", False)
            action = super().add_argument(*args, **kwargs)
            action.advanced = advanced
            return action

        def add_argument_group(self, title=None, description=None, advanced=False):
            group = super().add_argument_group(title, description)
            group.advanced = advanced

            # Override add_argument for the group to track advanced status
            original_add_argument = group.add_argument

            def add_argument_with_advanced(*args, **kwargs):
                # Determine the advanced status, defaulting to the group's status
                is_advanced = kwargs.pop("advanced", group.advanced)  # Use pop to get and remove

                # Call the original add_argument without the 'advanced' kwarg
                action = original_add_argument(*args, **kwargs)

                # Set the custom attribute on the created action for the formatter
                action.advanced = is_advanced
                return action

            group.add_argument = add_argument_with_advanced

            return group

    # Parse just the --advanced flag to determine if we should show advanced options
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--advanced", action="store_true", help="Show advanced options")
    args_namespace, _ = pre_parser.parse_known_args()

    # Now create the real parser with the appropriate formatter
    parser = AdvancedArgumentParser(
        prog="codeconcat",
        description="CodeConCat – LLM‑friendly code aggregator & doc extractor",
        formatter_class=AdvancedHelpFormatter,
    )

    # === Positional Argument ===
    parser.add_argument(
        "target_path",
        nargs="?",
        default=".",
        help="Target directory or file to process. Defaults to the current directory.",
    )

    # === Basic Options ===
    g_gen = parser.add_argument_group("Basic Options")
    g_gen.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    g_gen.add_argument(
        "--config",
        help="Path to a specific configuration file (.yaml/.yml). Overrides default search.",
        metavar="FILE",
    )
    g_gen.add_argument(
        "--init",
        action="store_true",
        help="Interactive setup: create a customized '.codeconcat.yml' and exit.",
    )
    g_gen.add_argument("--show-config", action="store_true", help="Print merged config and exit.")
    g_gen.add_argument(
        "--show-config-detail",
        action="store_true",
        help="Print detailed config showing the source of each setting (default/preset/YAML/CLI).",
    )
    parser.add_argument(
        "--advanced", action="store_true", help="Show advanced options in help output."
    )

    # === Logging & Verbosity ===
    g_log = parser.add_argument_group("Logging & Verbosity")
    g_log.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (-v for INFO, -vv for DEBUG).",
    )
    g_log.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging (equivalent to -vv).",
    )
    g_log.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Quiet mode: suppress progress information but keep token summaries and success message",
    )
    g_log.add_argument(
        "--log-level",
        default=None,  # Default handled based on verbosity/debug flag
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        advanced=True,
        help="Explicitly set logging level (overrides -v/-vv/--debug).",
    )
    g_log.add_argument(
        "--disable-progress-bar",
        action="store_true",
        help="Disable progress bars during file processing.",
    )
    g_log.add_argument(
        "--show-skip",
        action="store_true",
        advanced=True,
        help="Show skipped files list (requires -v or higher).",
    )

    # === Diagnostic Options ===
    g_diag = parser.add_argument_group("Diagnostic Tools", advanced=True)
    g_diag.add_argument(
        "--verify-dependencies",
        action="store_true",
        help="Check if all Tree-sitter grammars are properly installed and exit.",
    )
    g_diag.add_argument(
        "--diagnose-parser",
        metavar="LANGUAGE",
        help="Run diagnostic checks on the parser for a specific language using a test file.",
    )

    # === Input Source ===
    g_in = parser.add_argument_group("Input Source")
    g_in.add_argument("--source-url", help="URL or owner/repo shorthand.")
    g_in.add_argument("--github-token", help="PAT for private repos.")
    g_in.add_argument(
        "--source-ref", dest="source_ref", help="Branch, tag or commit hash for the Git source URL."
    )

    # === Filtering Options ===
    g_filt = parser.add_argument_group("Filtering Options")
    g_filt.add_argument(
        "-ip",
        "--include-paths",
        nargs="*",
        help="Glob patterns for files/directories to explicitly include.",
        metavar="PATTERN",
    )
    g_filt.add_argument(
        "-ep",
        "--exclude-paths",
        nargs="*",
        help="Glob patterns for files/directories to explicitly exclude.",
        metavar="PATTERN",
    )
    g_filt.add_argument(
        "--use-gitignore",
        action=argparse.BooleanOptionalAction,
        default=None,  # Default is handled by CodeConCatConfig
        help="Respect .gitignore files (default: True). Use --no-use-gitignore to disable.",
    )
    g_filt.add_argument(
        "--use-default-excludes",
        action=argparse.BooleanOptionalAction,
        default=None,  # Default is handled by CodeConCatConfig
        help="Use built-in default excludes (default: True). Use --no-use-default-excludes to disable.",
    )
    g_filt.add_argument(
        "-il",
        "--include-languages",
        nargs="+",
        metavar="LANG",
        help="Languages to include (e.g., python, java). Overrides default/config.",
    )
    g_filt.add_argument(
        "-el",
        "--exclude-languages",
        nargs="+",
        metavar="LANG",
        help="Languages to exclude (e.g., python, java). Overrides default/config.",
    )

    # === Output ===
    g_out = parser.add_argument_group("Output")
    g_out.add_argument("-o", "--output", help="Output file path.")
    g_out.add_argument("--format", default="markdown", choices=["markdown", "json", "xml", "text"])
    g_out.add_argument(
        "--preset",
        choices=["lean", "medium", "full"],
        help="Apply a predefined set of output configuration options (overrides individual flags).",
    )
    g_out.add_argument("--split-output", type=int, metavar="N", default=1, help="Split Markdown.")
    g_out.add_argument("--sort-files", action="store_true", help="Sort files alphabetically.")

    # === Feature Toggles ===
    g_feat = parser.add_argument_group("Feature Toggles")
    g_feat.add_argument("--docs", action="store_true", help="Extract standalone docs.")
    g_feat.add_argument("--merge-docs", action="store_true", help="Merge docs into main output.")

    # Replace confusing flag with clearer option
    g_feat.add_argument(
        "--parser-engine",
        choices=["tree_sitter", "regex"],
        default=None,  # Will be determined by the config
        help="Parser engine to use. 'tree_sitter' for advanced parsing, 'regex' for simpler and faster parsing.",
    )
    # Keep old flag for backward compatibility, but mark as deprecated
    g_feat.add_argument(
        "--no-tree",
        action="store_true",
        advanced=True,
        help="DEPRECATED: Use --parser-engine=regex instead. Omit folder tree in output.",
    )

    g_feat.add_argument("--no-ai-context", action="store_true", help="Skip AI preamble.")
    g_feat.add_argument("--no-annotations", action="store_true", help="Skip code annotation.")
    g_feat.add_argument(
        "--mask-output",
        dest="mask_output_content",
        action="store_true",
        advanced=True,
        help="Mask sensitive data directly in the final output content.",
    )
    g_feat.add_argument("--no-symbols", action="store_true", help="Skip symbol index.")
    g_feat.add_argument("--remove-docstrings", action="store_true", help="Strip docstrings.")
    g_feat.add_argument(
        "--cross-link-symbols",
        action="store_true",
        advanced=True,
        help="Cross‑link symbol list ↔ definitions.",
    )
    g_feat.add_argument(
        "--no-progress-bar", action="store_true", advanced=True, help="Disable tqdm progress bars."
    )

    # === Processing ===
    g_proc = parser.add_argument_group("Processing", advanced=True)
    g_proc.add_argument("--max-workers", type=int, default=4, help="Thread‑pool size.")

    return parser


# ──────────────────────────────────────────────────────────────────────────────
def cli_entry_point():
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
        log_level = getattr(args, "log_level", "WARNING")
        debug_mode = getattr(args, "debug", False)
        quiet_mode = getattr(args, "quiet", False)
        configure_logging(log_level, debug_mode, quiet_mode)

        # Initialize config if requested
        if hasattr(args, "init") and args.init:
            logger.info("Running interactive configuration setup")
            create_default_config(interactive=True)
            return 0

        # Convert args namespace to dictionary for easier handling
        cli_args = vars(args)

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

    # We already handled the no_tree flag in the try block above

    # --- Load Configuration using the new ConfigBuilder --- #
    try:
        # Get the preset name (if specified)
        preset_name = args.preset or "medium"  # Default to medium if not specified

        # Create a config builder and apply settings in the proper order
        config_builder = ConfigBuilder()
        config_builder.with_defaults()
        config_builder.with_preset(preset_name)
        config_builder.with_yaml_config(args.config)  # Use config_path_override if provided
        config_builder.with_cli_args(cli_args)  # Apply CLI arguments last

        # Build the final configuration
        config = config_builder.build()

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
    config.verbose = args.verbose > 0

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
        import os

        test_file = None
        test_corpus_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "tests", "parser_test_corpus", language
        )

        if os.path.exists(test_corpus_path):
            for filename in os.listdir(test_corpus_path):
                if filename.startswith("basic.") or filename == "basic":
                    test_file = os.path.join(test_corpus_path, filename)
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
            print(get_random_quote())

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
    """
    from codeconcat.collector.local_collector import (
        should_include_file,
        should_skip_dir,
    )

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
    1. Collects files (local or GitHub).
    2. Parses collected code files.
    3. Extracts documentation files (if enabled).
    4. Performs AI-based annotation (if enabled).
    5. Generates the final output string in the specified format.

    Args:
        config: The fully resolved CodeConCatConfig object containing all settings.

    Returns:
        The concatenated and processed output as a single string.

    Raises:
        CodeConcatError: For general errors during processing.
        ConfigurationError: If the configuration is invalid.
        FileProcessingError: For errors related to reading or parsing files.
        OutputError: For errors during output generation.
    """
    logger.debug("Running CodeConCat with config: %s", config)
    try:
        # Validate configuration
        if not config.target_path:
            raise ConfigurationError("Target path is required")
        if config.format not in ["markdown", "json", "xml", "text"]:
            raise ConfigurationError(f"Invalid format: {config.format}")

        # Collect files
        logger.debug(f"Starting file collection from: {config.target_path or config.source_url}")
        try:
            temp_repo_path = ""  # Initialize for non-remote case
            if config.source_url:
                code_files, temp_repo_path = collect_git_repo(config.source_url, config)
            else:
                code_files = collect_local_files(config.target_path, config)

            if not code_files:
                raise FileProcessingError("No files found to process")
        except Exception as e:
            raise FileProcessingError(f"Error collecting files: {str(e)}")
        logger.debug(f"Collected {len(code_files)} files.")

        # Generate folder tree if enabled
        logger.info("[CodeConCat] Generating folder tree...")
        folder_tree_str = ""
        if not config.disable_tree:
            # Use the temporary repo path for remote runs, otherwise the target path
            tree_root = temp_repo_path if config.source_url else config.target_path
            try:
                folder_tree_str = generate_folder_tree(tree_root, config)  # Pass config
                logger.info("[CodeConCat] Folder tree generated.")
            except Exception as e:
                logger.warning(f"Warning: Failed to generate folder tree: {str(e)}")

        # Parse code files
        logger.debug("Starting file parsing.")
        try:
            logger.info(f"[CodeConCat] Found {len(code_files)} code files. Starting parsing...")
            # Check if we should use the enhanced parsing pipeline
            use_enhanced_pipeline = (
                hasattr(config, "use_enhanced_pipeline") and config.use_enhanced_pipeline
            )

            if use_enhanced_pipeline:
                logger.info("Using enhanced parsing pipeline with progressive fallbacks")
                # Use the enhanced pipeline with progressive fallbacks
                parsed_files, errors = enhanced_parse_pipeline(code_files, config)
            else:
                # Use the standard parsing pipeline
                logger.info("Using standard parsing pipeline")
                parsed_files, errors = parse_code_files(code_files, config)

            if errors:
                # Log errors encountered during parsing
                for error in errors:
                    logger.warning(f"Parsing error for {error.file_path}: {str(error)}")

            if not parsed_files:
                logger.error("[CodeConCat] No files were successfully parsed.")
                # Decide if this should be a fatal error or just a warning
                raise FileProcessingError("No files were successfully parsed")
            else:
                logger.info(f"[CodeConCat] Parsing complete. Parsed {len(parsed_files)} files.")

        except Exception as e:
            raise FileProcessingError(f"Error parsing files: {str(e)}")

        # Extract docs if requested
        docs = []
        if config.extract_docs:
            try:
                doc_paths = [f.file_path for f in code_files]
                docs = extract_docs(doc_paths, config)
            except Exception as e:
                logger.warning(f"Warning: Failed to extract documentation: {str(e)}")

        logger.info("[CodeConCat] Starting annotation of parsed files...")
        # Annotate files if enabled
        annotated_files = []
        try:
            if not config.disable_annotations:
                # Wrap annotation loop with tqdm
                annotation_iterator = tqdm(
                    parsed_files,
                    desc="Annotating files",
                    unit="file",
                    total=len(parsed_files),
                    disable=config.disable_progress_bar,  # Use config flag
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
                                    language=file.language,
                                    content=file.content,
                                    annotated_content=file.content,
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
                basic_annotation_iterator = tqdm(
                    parsed_files,
                    desc="Preparing basic annotations",
                    unit="file",
                    total=len(parsed_files),
                    disable=config.disable_progress_bar,
                )
                for file in basic_annotation_iterator:
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
            raise FileProcessingError(f"Error during annotation phase: {str(e)}")

        # --- Prepare list for polymorphic writers --- #
        items: List[WritableItem] = []
        items.extend(annotated_files)
        items.extend(docs)

        if config.sort_files:
            logger.info("Sorting all items alphabetically by path...")
            items.sort(key=lambda x: x.file_path)
            logger.debug("Items sorted.")

        # Apply compression if enabled
        if config.enable_compression:
            logger.info(f"[CodeConCat] Applying compression (level: {config.compression_level})...")
            compression_processor = CompressionProcessor(config)

            # Apply compression to each annotated file
            for i, item in enumerate(items):
                if isinstance(item, AnnotatedFileData) and item.content:
                    # Process the file through the compression processor
                    compressed_segments = compression_processor.process_file(item)

                    if compressed_segments:
                        # Store the compressed content in the item for rendering
                        item.content = compression_processor.apply_compression(item)

                        # Store segments in config for the renderer to access
                        # This is a workaround since we can't modify the WritableItem interface
                        # without more substantial refactoring
                        config._compressed_segments = compressed_segments

                        # Log compression stats
                        original_lines = len(item.content.split("\n"))
                        compressed_lines = sum(
                            1
                            for s in compressed_segments
                            if s.segment_type == ContentSegmentType.CODE
                        )
                        logger.debug(
                            f"Compressed {item.file_path}: {compressed_lines} retained of {original_lines} lines"
                        )

            logger.info("[CodeConCat] Compression complete.")

        logger.info(f"[CodeConCat] Writing output in {config.format} format...")
        # Write output in requested format
        try:
            output = None
            if config.format == "markdown":
                # Pass the combined & sorted items list
                # Updated call signature
                output = write_markdown(items, config, folder_tree_str)
            elif config.format == "json":
                # Pass the combined & sorted items list
                output = write_json(items, config, folder_tree_str)
            elif config.format == "xml":
                # Pass the combined & sorted items list
                # Corrected call signature
                output = write_xml(items, config, folder_tree_str)
            elif config.format == "text":
                # Pass the combined & sorted items list
                # Corrected call to use the actual writer function
                output = write_text(items, config, folder_tree_str)
        except Exception as e:
            raise OutputError(f"Error generating {config.format} output: {str(e)}")

        # --- Token stats summary (all files) ---
        try:
            from codeconcat.processor.token_counter import get_token_stats

            total_gpt4 = total_davinci = total_claude = 0
            for pf in parsed_files:
                stats = get_token_stats(pf.content)
                total_gpt4 += stats.gpt4_tokens
                total_davinci += stats.davinci_tokens
                total_claude += stats.claude_tokens
            print("\n[Token Summary] Total tokens for all parsed files:")
            print(f"  Claude:   {total_claude}")
            print(f"  GPT-4:    {total_gpt4}")
            print(f"  Davinci:  {total_davinci}")
        except Exception as e:
            logger.warning(f"[Tokens] Failed to calculate token stats: {e}")
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
    runs the main processing pipeline via `run_codeconcat`, and returns the
    generated output string.

    It suppresses the default stdout messages (like the quote and final status)
    to provide a cleaner return value for programmatic callers.

    Args:
        config: A CodeConCatConfig object with all desired settings populated.

    Returns:
        The complete generated output string.

    Raises:
        Inherits exceptions from `run_codeconcat` (CodeConcatError, etc.).
    """
    # Suppress the initial quote and final messages for in-memory usage
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        result = run_codeconcat(config)
    finally:
        # Restore stdout
        sys.stdout.close()
        sys.stdout = original_stdout
    return result


def main():
    """Main function wrapper that calls the CLI entry point."""
    cli_entry_point()


if __name__ == "__main__":
    main()
