#!/usr/bin/env python3
# SPDX‑License‑Identifier: MIT

"""
Main entry point for the CodeConCat CLI application.

This module handles command-line argument parsing, configuration loading,
file collection, processing, and output generation.
"""

# Ensure os is imported at the global scope
import os
import argparse
import importlib.resources
import logging
import sys
from typing import List, Union
from typing import Literal

from tqdm import tqdm

from codeconcat.base_types import (
    ContentSegmentType,
    AnnotatedFileData,
    CodeConCatConfig,
    WritableItem,
    ParsedFileData,
)


from codeconcat.errors import (
    ValidationError,
    FileProcessingError,
    ConfigurationError,
    CodeConcatError,
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
from codeconcat.validation.integration import (
    validate_input_files,
    validate_config_values,
    verify_file_signatures,
)
from codeconcat.validation.integration import setup_semgrep
from codeconcat.version import __version__
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.text_writer import write_text
from codeconcat.writer.xml_writer import write_xml
from codeconcat.reconstruction import reconstruct_from_file

# Suppress HuggingFace tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
# Exception hierarchy - import OutputError from errors
class OutputError(CodeConcatError):
    """Errors during output generation."""

    pass


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _write_output_files(output_text: str, config: CodeConCatConfig) -> None:
    # Import os in this scope to avoid any potential shadowing
    import os as local_os

    """Write the final concatenated output to one or more files.

    Handles splitting the output into multiple parts if requested in the config
    and optionally copies the content
    to the clipboard.

    Args:
        output_text: The complete string output generated by CodeConCat.
        config: The CodeConCatConfig object containing output settings like
                output path, format, split_output, and disable_copy.
    """
    # Debug print to check what output path is set in config
    # print(f"[DEBUG OUTPUT] Config output path: '{config.output}'")

    # Determine the output path from config
    # If output is None or empty string, use the folder name-based default
    if config.output is None or config.output == "":
        # Get the directory name from target_path
        if config.target_path:
            # Normalize path and get base folder name
            folder_name = local_os.path.basename(local_os.path.normpath(config.target_path))

            # Special case - if target_path is a single file, use its containing folder
            if local_os.path.isfile(config.target_path):
                parent_dir = local_os.path.dirname(config.target_path)
                if parent_dir:
                    folder_name = local_os.path.basename(local_os.path.normpath(parent_dir))

            # Remove any unsafe characters
            folder_name = "".join(c for c in folder_name if c.isalnum() or c in "._- ")

            # If folder_name is empty after cleaning, use a fallback
            if not folder_name.strip():
                folder_name = "codeconcat"

            output_path = f"{folder_name}_ccc.{config.format}"
            print(f"[Info] Using folder-based output name: {output_path}")
        else:
            # Fallback if no target_path is available
            output_path = f"codeconcat_output.{config.format}"
    else:
        output_path = config.output

    # Debug print the final output path
    # print(f"[DEBUG OUTPUT] Final output path: '{output_path}'")

    parts = max(1, getattr(config, "split_output", 1))

    if parts > 1 and config.format == "markdown":
        lines = output_text.splitlines(keepends=True)
        chunk_size = (len(lines) + parts - 1) // parts
        base, ext = local_os.path.splitext(output_path)

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
    # Ensure os is properly imported in this scope
    import os as local_os

    config_filename = ".codeconcat.yml"
    if local_os.path.exists(config_filename):
        logger.warning(f"{config_filename} already exists; aborting.")
        return

    try:
        # First try to use the file directly
        template_path = local_os.path.join(
            local_os.path.dirname(__file__), "config", "templates", "default_config.template.yml"
        )
        if local_os.path.exists(template_path):
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

    # === Output Options ===
    g_output = parser.add_argument_group("Output Options")
    g_output.add_argument(
        "-o", "--output", help="Output file path (auto-detected from --format if omitted)"
    )
    g_output.add_argument(
        "-f",
        "--format",
        choices=["markdown", "md", "json", "xml", "text", "txt"],
        default="markdown",
        help="Output format",
    )
    g_output.add_argument(
        "--output-preset",
        choices=["lean", "medium", "full"],
        default=None,  # Default will be handled by ConfigBuilder or load_config
        help="Configuration preset to use (lean, medium, full). Overrides parts of the config file.",
    )

    # === Reconstruction Options ===
    g_reconstruct = parser.add_argument_group("Reconstruction Options")
    g_reconstruct.add_argument(
        "--reconstruct",
        metavar="FILE",
        help="Reconstruct source files from a CodeConCat output file",
    )
    g_reconstruct.add_argument(
        "--output-dir",
        metavar="DIR",
        default="./reconstructed",
        help="Directory to output reconstructed files",
    )
    g_reconstruct.add_argument(
        "--input-format",
        choices=["markdown", "xml", "json", "auto"],
        default="auto",
        help="Format of input file for reconstruction (auto-detected if not specified)",
    )

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

    # === Compression Options ===
    g_comp = parser.add_argument_group("Compression Options")
    g_comp.add_argument(
        "--enable-compression",
        action="store_true",
        help="Enable intelligent code compression to reduce output size.",
    )
    g_comp.add_argument(
        "--compression-level",
        choices=["low", "medium", "high", "aggressive"],
        default="medium",
        help="Compression intensity level (default: medium).",
    )
    g_comp.add_argument(
        "--compression-placeholder",
        type=str,
        help="Template for placeholder text replacing omitted segments. Use {lines} and {issues} as placeholders.",
    )
    g_comp.add_argument(
        "--compression-keep-threshold",
        type=int,
        default=3,
        advanced=True,
        help="Minimum lines to consider keeping a segment (smaller segments always kept).",
    )
    g_comp.add_argument(
        "--compression-keep-tags",
        nargs="+",
        metavar="TAG",
        advanced=True,
        help="Special comment tags that mark segments to always keep during compression.",
    )

    # === Security Options ===
    g_sec = parser.add_argument_group("Security Options")
    g_sec.add_argument(
        "--enable-security-scanning",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable security scanning (default: True).",
    )
    g_sec.add_argument(
        "--security-threshold",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default="MEDIUM",
        dest="security_scan_severity_threshold",
        help="Minimum severity threshold for security findings (default: MEDIUM).",
    )
    g_sec.add_argument(
        "--enable-semgrep",
        action="store_true",
        help="Enable Semgrep security scanning using the Apiiro malicious code ruleset.",
    )
    g_sec.add_argument(
        "--install-semgrep",
        action="store_true",
        help="Install Semgrep and the Apiiro ruleset if not already installed.",
    )
    g_sec.add_argument(
        "--semgrep-ruleset",
        type=str,
        help="Path to custom Semgrep ruleset (defaults to Apiiro ruleset).",
    )
    g_sec.add_argument(
        "--semgrep-languages",
        nargs="+",
        metavar="LANG",
        help="Languages to scan with Semgrep (defaults to all detected languages).",
    )
    g_sec.add_argument(
        "--strict-security",
        action="store_true",
        help="Fail validation when suspicious content is detected.",
    )

    # === Processing ===
    g_proc = parser.add_argument_group("Processing", advanced=True)
    g_proc.add_argument("--max-workers", type=int, default=4, help="Thread‑pool size.")

    return parser


# ──────────────────────────────────────────────────────────────────────────────
def cli_entry_point():
    # Ensure os is properly imported in this scope
    import os as local_os  # Use a different name to avoid any potential shadowing

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

        # Ensure default output filename uses correct format extension when format is specified via CLI
        if config.output is None or config.output == "code_concat_output.md":
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
    # Validate configuration
    try:
        validate_config_values(config)
        logger.debug("Configuration validation passed")
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ConfigurationError(f"Invalid configuration: {e}")
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

        # Collect input files
        logger.info("Collecting input files...")
        files_to_process: List[ParsedFileData] = []

        if config.source_url:
            logger.info(f"Collecting files from source URL: {config.source_url}")
            # Assuming collect_git_repo can handle generic URLs or is specialized for Git
            files_to_process = collect_git_repo(config)
        elif config.target_path:
            logger.info(f"Collecting files from local path: {config.target_path}")
            files_to_process = collect_local_files(config.target_path, config)
        else:
            raise ConfigurationError(
                "Either source_url or target_path must be provided in the configuration."
            )

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

        # Parse code files
        logger.debug("Starting file parsing.")
        try:
            logger.info(
                f"[CodeConCat] Found {len(files_to_process)} code files. Starting parsing..."
            )
            # Check if we should use the enhanced parsing pipeline
            use_enhanced_pipeline = (
                hasattr(config, "use_enhanced_pipeline") and config.use_enhanced_pipeline
            )

            if use_enhanced_pipeline:
                logger.info("Using enhanced parsing pipeline with progressive fallbacks")
                # Use the enhanced pipeline with progressive fallbacks
                parsed_files, errors = enhanced_parse_pipeline(files_to_process, config)
            else:
                # Use the standard parsing pipeline
                logger.info("Using standard parsing pipeline")
                parsed_files, errors = parse_code_files(files_to_process, config)

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
                doc_paths = [f.file_path for f in files_to_process]
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
            config._compressed_segments = {}

            # Apply compression to each annotated file
            for i, item in enumerate(items):
                if isinstance(item, AnnotatedFileData) and item.content:
                    # Process the file through the compression processor
                    compressed_segments = compression_processor.process_file(item)

                    if compressed_segments:
                        # Store the compressed content in the item for rendering
                        item.content = compression_processor.apply_compression(item)

                        # Store segments in config for the renderer to access, properly indexed by file path
                        # This is a workaround since we can't modify the WritableItem interface
                        # without more substantial refactoring
                        config._compressed_segments[item.file_path] = compressed_segments

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

            for item in items:
                if isinstance(item, AnnotatedFileData) and hasattr(item, "_compression_stats"):
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
                output = write_json(items, config, folder_tree_str)
                print("Using JSON writer")
            elif config.format == "xml":
                # Pass the combined & sorted items list
                output = write_xml(items, config, folder_tree_str)
                print("Using XML writer")
            elif config.format == "text":
                # Pass the combined & sorted items list
                output = write_text(items, config, folder_tree_str)
                print("Using text writer")
            else:
                # Default to markdown if format is unrecognized
                logger.warning(f"Unrecognized format '{config.format}', defaulting to markdown")
                config.format = "markdown"
                output = write_markdown(items, config, folder_tree_str)
        except Exception as e:
            raise OutputError(f"Error generating {config.format} output: {str(e)}")

        # --- Token stats summary (all files) ---
        try:
            from codeconcat.processor.token_counter import get_token_stats

            # Calculate tokens for uncompressed content
            total_gpt4_uncompressed = total_davinci_uncompressed = total_claude_uncompressed = 0
            for pf in parsed_files:
                stats = get_token_stats(pf.content)
                total_gpt4_uncompressed += stats.gpt4_tokens
                total_davinci_uncompressed += stats.davinci_tokens
                total_claude_uncompressed += stats.claude_tokens

            print("\n[Token Summary] Total tokens for all parsed files (UNCOMPRESSED):")
            print(f"  Claude:   {total_claude_uncompressed}")
            print(f"  GPT-4:    {total_gpt4_uncompressed}")
            print(f"  Davinci:  {total_davinci_uncompressed}")

            # If compression was enabled, also show compressed tokens for comparison
            if (
                config.enable_compression
                and hasattr(config, "_compressed_segments")
                and config._compressed_segments
            ):
                total_gpt4_compressed = total_davinci_compressed = total_claude_compressed = 0

                # Calculate compressed tokens by using the compressed segments
                for file_path, file_segments in config._compressed_segments.items():
                    # Concatenate the content of all segments in this file
                    compressed_content = "\n".join(segment.content for segment in file_segments)
                    stats = get_token_stats(compressed_content)
                    total_gpt4_compressed += stats.gpt4_tokens
                    total_davinci_compressed += stats.davinci_tokens
                    total_claude_compressed += stats.claude_tokens

                print("\n[Token Summary] Total tokens for all parsed files (COMPRESSED):")
                print(
                    f"  Claude:   {total_claude_compressed} ({(total_claude_compressed/total_claude_uncompressed*100):.1f}%)"
                )
                print(
                    f"  GPT-4:    {total_gpt4_compressed} ({(total_gpt4_compressed/total_gpt4_uncompressed*100):.1f}%)"
                )
                print(
                    f"  Davinci:  {total_davinci_compressed} ({(total_davinci_compressed/total_davinci_uncompressed*100):.1f}%)"
                )

                # Show token reduction from compression
                print("\n[Compression Effectiveness]")
                print(
                    f"  Claude:   {total_claude_uncompressed - total_claude_compressed} tokens saved ({(1-total_claude_compressed/total_claude_uncompressed)*100:.1f}% reduction)"
                )
                print(
                    f"  GPT-4:    {total_gpt4_uncompressed - total_gpt4_compressed} tokens saved ({(1-total_gpt4_compressed/total_gpt4_uncompressed)*100:.1f}% reduction)"
                )
                print(
                    f"  Davinci:  {total_davinci_uncompressed - total_davinci_compressed} tokens saved ({(1-total_davinci_compressed/total_davinci_uncompressed)*100:.1f}% reduction)"
                )
        except Exception as e:
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
